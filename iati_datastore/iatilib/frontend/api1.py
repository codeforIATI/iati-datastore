from collections import OrderedDict
from datetime import datetime
import sqlalchemy as sa
from flask import (current_app, request, Response, Blueprint,
                   jsonify, abort, render_template, make_response,
                   url_for, stream_with_context, send_file)
from flask.views import MethodView
from werkzeug.datastructures import MultiDict

from iatilib import db, rq
from iatilib.model import (Resource, Dataset,
                           Log, DeletedActivity, Stats)

from . import dsfilter, validators, serialize


api = Blueprint('api1', __name__)


@api.route('/')
def list_routes():
    urls = []
    rules = [
        r for r in current_app.url_map.iter_rules()
        if r.endpoint.startswith('api1.')]
    for rule in rules:
        options = {
            arg: arg.upper()
            for arg in rule.arguments
            if arg not in rule.defaults
        }
        url = url_for(rule.endpoint, _external=True, **options)
        urls.append(url)
    urls = sorted(urls)
    return jsonify(urls)


@api.route('/meta/filters/')
def meta_filters():
    return jsonify({
        'filters': list(validators.activity_api_args.schema.keys())
        })


@api.route('/about/')
def about():
    # General status info
    count_activities = db.session.query(
        Stats.count
    ).filter_by(label='activities').scalar()

    count_transactions = db.session.query(
        Stats.count
    ).filter_by(label='transactions').scalar()

    count_budgets = db.session.query(
        Stats.count
    ).filter_by(label='budgets').scalar()

    count_datasets = Dataset.query.count()

    # Check last updated times

    updated = db.session.query(
        sa.func.max(Resource.last_fetch).label('last_fetch'),
        sa.func.max(Resource.last_succ).label('last_succ'),
        sa.func.max(Resource.last_parsed).label('last_parsed')
    ).first()
    now = datetime.now()
    # If the file was last fetched less than 2 days
    # ago and parsed less than 1 day
    # ago, then the API is healthy.
    if ((updated.last_fetch is not None) and
            (updated.last_succ is not None) and
            (updated.last_parsed is not None)):
        healthy = (
            ((now-updated.last_fetch).days < 2) and
            ((now-updated.last_succ).days < 2) and
            ((now-updated.last_parsed).days < 1)
        )
    else:
        healthy = False

    # Number of items on the queue
    items_on_queue = rq.get_queue().count

    return jsonify(
        ok=healthy,
        status={True: 'healthy', False: 'unhealthy'}[healthy],
        status_data={
            'last_fetch': updated.last_fetch,
            'last_successful_fetch': updated.last_succ,
            'last_parsed': updated.last_parsed
        },
        indexed_activities=count_activities,
        indexed_transactions=count_transactions,
        indexed_budgets=count_budgets,
        num_datasets=count_datasets,
        items_on_queue=items_on_queue
    )


@api.route('/about/dataset/')
def datasets():
    query = db.session.query(Dataset)\
        .options(db.selectinload(Dataset.resources))
    try:
        valid_args = validators.about_dataset_args(MultiDict(request.args))
    except (validators.MultipleInvalid, validators.Invalid) as e:
        return make_response(
            render_template('error/invalid_filter.html', errors=e), 400)
    if not valid_args.get('detail', False):
        return jsonify(datasets=[i.name for i in query.all()])

    offset = valid_args.get("offset", 0)
    limit = valid_args.get("limit", 50)
    datasets = query.limit(limit).offset(offset)
    items = [{
        'url': d.resources[0].url if d.resources else None,
        'last_fetch': d.resources[0].last_fetch.isoformat()
        if d.resources and d.resources[0].last_fetch else None,
        'last_status_code': d.resources[0].last_status_code
        if d.resources else None,
        'last_successful_fetch': d.resources[0].last_succ.isoformat()
        if d.resources and d.resources[0].last_succ else None,
        'last_parsed': d.resources[0].last_parsed.isoformat()
        if d.resources and d.resources[0].last_parsed else None,
    } for d in datasets]

    return jsonify(OrderedDict((
            ("ok", True),
            ("total-count", query.count()),
            ("start", offset),
            ("limit", limit),
            ("datasets", items),
        )
    ))


@api.route('/about/dataset/<dataset>/')
def about_dataset(dataset):
    dataset = db.session.query(Dataset).get(dataset)
    if dataset is None:
        abort(404)
    resources = [{
        'url': r.url,
        'last_fetch': r.last_fetch.isoformat() if r.last_fetch else None,
        'last_status_code': r.last_status_code,
        'last_successful_fetch': r.last_succ.isoformat() if r.last_succ else None,
        'last_parsed': r.last_parsed.isoformat() if r.last_parsed else None,
        'num_of_activities': r.activities.count(),
    } for r in dataset.resources]

    return jsonify(
            dataset=dataset.name,
            last_modified=None if dataset.last_modified is None else dataset.last_modified.isoformat(),
            num_resources=len(dataset.resources),
            resources=resources,
    )


@api.route('/about/deleted/')
def deleted_activities():
    try:
        valid_args = validators.pagination_args(MultiDict(request.args))
    except (validators.MultipleInvalid, validators.Invalid) as e:
        return make_response(
            render_template('error/invalid_filter.html', errors=e), 400)
    offset = valid_args.get("offset", 0)
    limit = valid_args.get("limit", 50)
    query = db.session.query(DeletedActivity)

    items = [
        {
            'iati_identifier': da.iati_identifier,
            'deletion_date': da.deletion_date.isoformat(),
        }
        for da in query
        .order_by(DeletedActivity.deletion_date.desc())
        .limit(limit).offset(offset)
    ]

    return jsonify(OrderedDict((
            ("ok", True),
            ("total-count", query.count()),
            ("start", offset),
            ("limit", limit),
            ("deleted_activities", items),
        )
    ))


@api.route('/error/dataset/')
def error():
    # logs = db.session.query(Log.dataset).distinct()
    logs = db.session.query(Log.dataset, Log.logger).\
            group_by(Log.dataset, Log.logger).\
            order_by(Log.dataset)
    return jsonify(
            errored_datasets=[{'dataset': i[0], 'logger': i[1]} for i in logs.all()]
    )


@api.route('/error/dataset/<dataset_id>/')
def dataset_error(dataset_id):
    error_logs = db.session.query(Log).\
            filter(Log.dataset == dataset_id).\
            order_by(sa.desc(Log.created_at))
    errors = [{
                'resource_url': log.resource,
                'dataset': log.dataset,
                'logger': log.logger,
                'msg': log.msg,
                'traceback': log.trace,
                'datestamp': log.created_at.isoformat(),
            } for log in error_logs.all()]

    return jsonify(errors=errors)


@api.route('/error/dataset.log')
def dataset_log():
    logs = db.session.query(Log.dataset).distinct()
    response = make_response(
        render_template('datasets.log', logs=logs))
    response.mimetype = 'text/plain'
    return response


@api.route('/error/dataset.log/<dataset_id>/')
def dataset_log_error(dataset_id):
    error_logs = db.session.query(Log).\
        filter(Log.dataset == dataset_id).\
        order_by(Log.created_at.desc())
    errors = [{
        'resource_url': log.resource,
        'logger': log.logger,
        'msg': log.msg,
        'traceback': log.trace.split('\n') if log.trace else [],
        'datestamp': log.created_at.isoformat(),
    } for log in error_logs]

    response = make_response(
        render_template('dataset.log', errors=errors))
    response.mimetype = 'text/plain'
    return response


class Scrollination:
    def __init__(self, items, query=None, offset=None, limit=None):
        self.items = items
        self.query = query
        self.offset = offset
        self.limit = limit

    @property
    def total(self):
        return self.query.count()


class Stream(Scrollination):
    """
    Wrapper to make a query object quack like a pagination object
    """
    @property
    def total(self):
        return self.items.count()


class DataStoreView(MethodView):
    filter = None
    serializer = None

    @property
    def streaming(self):
        return self.validate_args().get("stream", False)

    @property
    def wrapped(self):
        return not self.validate_args().get("unwrap", False)

    def paginate(self, query, offset, limit):
        items = query.order_by('iati_identifier').limit(limit).offset(offset)
        return Scrollination(items, query, offset, limit)

    def validate_args(self):
        if not hasattr(self, "_valid_args"):
            args = MultiDict(request.args)
            args.pop("ref", None)
            args.pop("locale", None)
            self._valid_args = validators.activity_api_args(args)
        return self._valid_args

    def get_response(self, mimetype, serializer=None):
        if serializer is None:
            serializer = self.serializer

        try:
            valid_args = self.validate_args()
        except (validators.MultipleInvalid, validators.Invalid) as e:
            return make_response(
                render_template('error/invalid_filter.html', errors=e), 400)
        query = self.filter(valid_args)

        query = query.yield_per(100)
        if self.streaming:
            pagination = Stream(query)
        else:
            pagination = self.paginate(
                query,
                valid_args.get("offset", 0),
                valid_args.get("limit", 50),
            )
        if hasattr(serializer, 'file_mode') and serializer.file_mode:
            filedata = serializer(pagination, self.wrapped)
            return send_file(
                filedata['file'],
                mimetype=mimetype,
                attachment_filename=filedata['client_filename'],
                as_attachment=True
            )
        else:
            return Response(
                stream_with_context(serializer(pagination, self.wrapped)),
                mimetype=mimetype)


class ActivityView(DataStoreView):
    filter = staticmethod(dsfilter.activities)

    def get(self, format):
        forms = {
            "xml": ("application/xml", serialize.xml),
            "db.json": ("application/json", serialize.datastore_json),
        }
        if format not in forms:
            abort(404)
        return self.get_response(*forms[format])


class ActivityJSONView(DataStoreView):
    filter = staticmethod(dsfilter.activities_for_json)

    def get(self, format="json"):
        return self.get_response("application/json", serialize.json)  # rfc4627


class DataStoreCSVView(DataStoreView):
    def get(self, format="csv"):
        return self.get_response("text/csv")

    def paginate(self, query, offset, limit):
        items = query\
            .order_by('iati_identifier')\
            .limit(limit)\
            .offset(offset)
        return Scrollination(items)


class DataStoreXLSXView(DataStoreView):
    def get(self, format="xlsx"):
        return self.get_response("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def paginate(self, query, offset, limit):
        items = query\
            .order_by('iati_identifier')\
            .limit(limit)\
            .offset(offset)
        return Scrollination(items)


class ActivityCSVView(DataStoreCSVView):
    filter = staticmethod(dsfilter.activities_for_csv)
    serializer = staticmethod(serialize.csv)


class ActivityXLSXView(DataStoreXLSXView):
    filter = staticmethod(dsfilter.activities_for_csv)
    serializer = staticmethod(serialize.xlsx)


class ActivityByCountryView(DataStoreCSVView):
    filter = staticmethod(dsfilter.activities_by_country)
    serializer = staticmethod(serialize.csv_activity_by_country)


class ActivityByCountryXLSXView(DataStoreXLSXView):
    filter = staticmethod(dsfilter.activities_by_country)
    serializer = staticmethod(serialize.xlsx_activity_by_country)


class ActivityBySectorView(DataStoreCSVView):
    filter = staticmethod(dsfilter.activities_by_sector)
    serializer = staticmethod(serialize.csv_activity_by_sector)


class ActivityBySectorXLSXView(DataStoreXLSXView):
    filter = staticmethod(dsfilter.activities_by_sector)
    serializer = staticmethod(serialize.xlsx_activity_by_sector)


class TransactionsView(DataStoreCSVView):
    filter = staticmethod(dsfilter.transactions)
    serializer = staticmethod(serialize.transaction_csv)


class TransactionsXLSXView(DataStoreXLSXView):
    filter = staticmethod(dsfilter.transactions)
    serializer = staticmethod(serialize.transaction_xlsx)


class TransactionsByCountryView(DataStoreCSVView):
    filter = staticmethod(dsfilter.transactions_by_country)
    serializer = staticmethod(serialize.csv_transaction_by_country)


class TransactionsByCountryXLSXView(DataStoreXLSXView):
    filter = staticmethod(dsfilter.transactions_by_country)
    serializer = staticmethod(serialize.xlsx_transaction_by_country)


class TransactionsBySectorView(DataStoreCSVView):
    filter = staticmethod(dsfilter.transactions_by_sector)
    serializer = staticmethod(serialize.csv_transaction_by_sector)


class TransactionsBySectorXLSXView(DataStoreXLSXView):
    filter = staticmethod(dsfilter.transactions_by_sector)
    serializer = staticmethod(serialize.xlsx_transaction_by_sector)


class BudgetsView(DataStoreCSVView):
    filter = staticmethod(dsfilter.budgets)
    serializer = staticmethod(serialize.budget_csv)


class BudgetsXLSXView(DataStoreXLSXView):
    filter = staticmethod(dsfilter.budgets)
    serializer = staticmethod(serialize.budget_xlsx)


class BudgetsByCountryView(DataStoreCSVView):
    filter = staticmethod(dsfilter.budgets_by_country)
    serializer = staticmethod(serialize.csv_budget_by_country)


class BudgetsByCountryXLSXView(DataStoreXLSXView):
    filter = staticmethod(dsfilter.budgets_by_country)
    serializer = staticmethod(serialize.xlsx_budget_by_country)


class BudgetsBySectorView(DataStoreCSVView):
    filter = staticmethod(dsfilter.budgets_by_sector)
    serializer = staticmethod(serialize.csv_budget_by_sector)


class BudgetsBySectorXLSXView(DataStoreXLSXView):
    filter = staticmethod(dsfilter.budgets_by_sector)
    serializer = staticmethod(serialize.xlsx_budget_by_sector)


api.add_url_rule(
    '/access/activity/',
    defaults={"format": "json"},
    view_func=ActivityJSONView.as_view('activity-view'),
)

api.add_url_rule(
    '/access/activity.csv',
    view_func=ActivityCSVView.as_view('activity-csv-view'),
)

api.add_url_rule(
    '/access/activity.xlsx',
    view_func=ActivityXLSXView.as_view('activity-xlsx-view'),
)

api.add_url_rule(
    '/access/activity.json',
    view_func=ActivityJSONView.as_view('activity-json-view'),
)

api.add_url_rule(
    '/access/activity.<format>',
    view_func=ActivityView.as_view('activity')
)

api.add_url_rule(
    '/access/activity/by_country.csv',
    view_func=ActivityByCountryView.as_view('activity_by_country'))

api.add_url_rule(
    '/access/activity/by_country.xlsx',
    view_func=ActivityByCountryXLSXView.as_view('activity_by_country_xlsx'))

api.add_url_rule(
    '/access/activity/by_sector.csv',
    view_func=ActivityBySectorView.as_view('activity_by_sector'))

api.add_url_rule(
    '/access/activity/by_sector.xlsx',
    view_func=ActivityBySectorXLSXView.as_view('activity_by_sector_xlsx'))

api.add_url_rule(
    '/access/transaction.csv',
    view_func=TransactionsView.as_view('transaction_list'))

api.add_url_rule(
    '/access/transaction.xlsx',
    view_func=TransactionsXLSXView.as_view('transaction_list_xlsx'))

api.add_url_rule(
    '/access/transaction/by_country.csv',
    view_func=TransactionsByCountryView.as_view('transaction_by_country'))

api.add_url_rule(
    '/access/transaction/by_country.xlsx',
    view_func=TransactionsByCountryXLSXView.as_view('transaction_by_country_xlsx'))

api.add_url_rule(
    '/access/transaction/by_sector.csv',
    view_func=TransactionsBySectorView.as_view('transaction_by_sector'))

api.add_url_rule(
    '/access/transaction/by_sector.xlsx',
    view_func=TransactionsBySectorXLSXView.as_view('transaction_by_sector_xlsx'))

api.add_url_rule(
    '/access/budget.csv',
    view_func=BudgetsView.as_view('budget_list'))

api.add_url_rule(
    '/access/budget.xlsx',
    view_func=BudgetsXLSXView.as_view('budget_list_xlsx'))

api.add_url_rule(
    '/access/budget/by_country.csv',
    view_func=BudgetsByCountryView.as_view('budget_by_country'))


api.add_url_rule(
    '/access/budget/by_country.xlsx',
    view_func=BudgetsByCountryXLSXView.as_view('budget_by_country_xlsx'))

api.add_url_rule(
    '/access/budget/by_sector.csv',
    view_func=BudgetsBySectorView.as_view('budget_by_sector'))

api.add_url_rule(
    '/access/budget/by_sector.xlsx',
    view_func=BudgetsBySectorXLSXView.as_view('budget_by_sector_xlsx'))
