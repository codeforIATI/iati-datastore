import datetime
import hashlib
import logging
import traceback

import iatikit
import sqlalchemy as sa
from dateutil.parser import parse as date_parser
from flask import Blueprint
import click

from iatilib import db, parse, rq
from iatilib.model import Dataset, Resource, Activity, Log, DeletedActivity
from iatilib.loghandlers import DatasetMessage as _

from iatilib.currency_conversion import download_imf_exchange_rates, update_exchange_rates

log = logging.getLogger("crawler")


manager = Blueprint('crawler', __name__)
manager.cli.short_help = "Crawl IATI registry"


def fetch_dataset_list():
    '''
    Fetches datasets from iatikit and stores them in the DB. Used in update() to update the Flask job queue. Uses CKAN metadata to determine
    if an activity is active or deleted.
    :return:
    '''
    existing_datasets = Dataset.query.all()
    existing_ds_names = set(ds.name for ds in existing_datasets)

    package_list = [d.name for d in iatikit.data().datasets]
    incoming_ds_names = set(package_list)

    new_datasets = [Dataset(name=n) for n
                    in incoming_ds_names - existing_ds_names]
    all_datasets = existing_datasets + new_datasets
    last_seen = iatikit.data().last_updated
    for dataset in all_datasets:
        dataset.last_seen = last_seen

    db.session.add_all(all_datasets)
    db.session.commit()

    deleted_ds_names = existing_ds_names - incoming_ds_names
    if deleted_ds_names:
        delete_datasets(deleted_ds_names)

    all_datasets = Dataset.query
    return all_datasets


def delete_datasets(datasets):
    deleted = sum([
        delete_dataset(dataset)
        for dataset in datasets])
    log.info("Deleted {0} datasets".format(deleted))
    return deleted


def delete_dataset(dataset):
    deleted_dataset = db.session.query(Dataset). \
        filter(Dataset.name == dataset)

    activities_to_delete = db.session.query(Activity). \
        filter(Activity.resource_url == Resource.url). \
        filter(Resource.dataset_id == dataset)

    now = datetime.datetime.now()
    for a in activities_to_delete:
        db.session.merge(DeletedActivity(
            iati_identifier=a.iati_identifier,
            deletion_date=now
        ))
    db.session.commit()
    return deleted_dataset.delete(synchronize_session='fetch')


def fetch_dataset_metadata(dataset):
    d = iatikit.data().datasets.get(dataset.name)
    dataset.publisher = d.metadata['organization']['name']

    dataset.last_modified = date_parser(
        d.metadata.get(
            'metadata_modified',
            datetime.datetime.now().date().isoformat()))
    new_urls = [resource['url'] for resource
                in d.metadata.get('resources', [])
                if resource['url'] not in dataset.resource_urls]
    dataset.resource_urls.extend(new_urls)

    urls = [resource['url'] for resource
            in d.metadata.get('resources', [])]
    for deleted in set(dataset.resource_urls) - set(urls):
        dataset.resource_urls.remove(deleted)

    dataset.license = d.metadata.get('license_id')
    dataset.is_open = d.metadata.get('isopen', False)
    db.session.add(dataset)
    return dataset


def fetch_resource(dataset, ignore_hashes):
    '''
    Gets the resource and sets the times of last successful update based on the status code.
    If `ignore_hashes` is set to True, `last_parsed` will be set to None and an
    update will be triggered.
    :param resource:
    :return:
    '''
    d = iatikit.data().datasets.get(dataset.name)
    last_updated = iatikit.data().last_updated
    resource = dataset.resources[0]
    resource.last_fetch = last_updated

    try:
        content = d.raw_xml
        resource.last_status_code = 200
        resource.last_succ = last_updated
        if (not resource.document) or \
                (hash(resource.document) != hash(content)) or \
                ignore_hashes:
            resource.document = content
            resource.last_parsed = None
            resource.last_parse_error = None
    except IOError:
        # TODO: this isn't true
        resource.last_status_code = 404

    db.session.add(resource)
    return resource


def check_for_duplicates(activities):
    if activities:
        dup_activity = Activity.query.filter(
                Activity.iati_identifier.in_(
                        a.iati_identifier for a in activities
                )
        )
        with db.session.no_autoflush:
            for db_activity in dup_activity:
                res_activity = next(
                        a for a in activities
                        if a.iati_identifier == db_activity.iati_identifier
                )
                activities.remove(res_activity)
                db.session.expunge(res_activity)
    return activities


def hash(string):
    m = hashlib.md5()
    m.update(string)
    return m.digest()


def parse_activity(new_identifiers, old_xml, resource):
    for activity in parse.document_from_bytes(resource.document, resource):
        activity.resource = resource

        if activity.iati_identifier not in new_identifiers:
            new_identifiers.add(activity.iati_identifier)
            try:
                if hash(activity.raw_xml.encode('utf-8')) == old_xml[activity.iati_identifier][1]:
                    activity.last_change_datetime = old_xml[activity.iati_identifier][0]
                else:
                    activity.last_change_datetime = datetime.datetime.now()
            except KeyError:
                activity.last_change_datetime = datetime.datetime.now()
            db.session.add(activity)
            check_for_duplicates([activity])
        else:
            parse.log.warn(
                    _("Duplicate identifier {0} in same resource document".format(
                            activity.iati_identifier),
                      logger='activity_importer', dataset=resource.dataset_id, resource=resource.url),
                    exc_info=''
            )

        db.session.flush()
    db.session.commit()


def parse_resource(resource):
    db.session.add(resource)
    current = Activity.query.filter_by(resource_url=resource.url)
    current_identifiers = set([i.iati_identifier for i in current.all()])

    # obtains the iati-identifier, last-updated datetime, and a hash of the existing xml associated with
    # every activity associated with the current url.
    old_xml = dict([(i[0], (i[1], hash(i[2].encode('utf-8')))) for i in db.session.query(
            Activity.iati_identifier, Activity.last_change_datetime,
            Activity.raw_xml).filter_by(resource_url=resource.url)])

    db.session.query(Activity).filter_by(resource_url=resource.url).delete()
    new_identifiers = set()
    parse_activity(new_identifiers, old_xml, resource)

    resource.version = parse.document_metadata(resource.document)

    # add any identifiers that are no longer present to deleted_activity table
    diff = current_identifiers - new_identifiers
    now = datetime.datetime.utcnow()
    deleted = [
        DeletedActivity(iati_identifier=deleted_activity, deletion_date=now)
        for deleted_activity in diff]
    if deleted:
        db.session.add_all(deleted)

    # remove any new identifiers from the deleted_activity table
    if new_identifiers:
        db.session.query(DeletedActivity) \
            .filter(DeletedActivity.iati_identifier.in_(new_identifiers)) \
            .delete(synchronize_session="fetch")

    log.info(
            "Parsed %d activities from %s",
            resource.activities.count(),
            resource.url)
    resource.last_parsed = now
    return resource  # , new_identifiers


def update_activities(dataset_name, ignore_hashes=False):
    '''
    Parses and stores the raw XML associated with a resource [see parse_resource()], or logs the invalid resource
    :param resource_url:
    :return:
    '''
    # clear up previous job queue log errors
    db.session.query(Log).filter(sa.and_(
            Log.logger == 'job iatilib.crawler.update_activities',
            Log.resource == dataset_name,
    )).delete(synchronize_session=False)
    db.session.commit()

    dataset = Dataset.query.get(dataset_name)
    resource = dataset.resources[0]

    if ignore_hashes: db.session._update_all_unique = True

    try:
        db.session.query(Log).filter(sa.and_(
                Log.logger.in_(
                        ['activity_importer', 'failed_activity', 'xml_parser']),
                Log.resource == dataset_name,
        )).delete(synchronize_session=False)
        parse_resource(resource)
        db.session.commit()
    except parse.ParserError as exc:
        db.session.rollback()
        resource.last_parse_error = str(exc)
        db.session.add(resource)
        db.session.add(Log(
                dataset=resource.dataset_id,
                resource=resource.url,
                logger="xml_parser",
                msg="Failed to parse XML file {0} error was".format(dataset_name, exc),
                level="error",
                trace=traceback.format_exc(),
                created_at=datetime.datetime.now()
        ))
        db.session.commit()

    if ignore_hashes: db.session._update_all_unique = False

def update_dataset(dataset_name, ignore_hashes):
    '''
    Takes the dataset name and determines whether or not an update is needed based on whether or not the last
    successful update detail exits, and whether or not it last updated since the contained data was updated.
    If ignore_hashes is set to true, an update will be triggered, regardless of whether there appears
    to be any change in the dataset hash compared with that stored in the database.
    :param dataset_name:
    :param ignore_hashes:
    :return:
    '''
    # clear up previous job queue log errors
    db.session.query(Log).filter(sa.and_(
            Log.logger == 'job iatilib.crawler.update_dataset',
            Log.dataset == dataset_name,
    )).delete(synchronize_session=False)
    db.session.commit()

    queue = rq.get_queue()
    dataset = Dataset.query.get(dataset_name)

    fetch_dataset_metadata(dataset)
    try:
        db.session.commit()
    except sa.exc.IntegrityError as exc:
        db.session.rollback()
        # the resource can't be added, so we should
        # give up.
        db.session.add(Log(
            dataset=dataset_name,
            resource=None,
            logger="update_dataset",
            msg="Failed to update dataset {0}, error was".format(dataset_name, exc),
            level="error",
            trace=traceback.format_exc(),
            created_at=datetime.datetime.now()
        ))
        db.session.commit()
        return

    resource = fetch_resource(dataset, ignore_hashes)
    db.session.commit()

    if resource.last_status_code == 200 and not resource.last_parsed:
        queue.enqueue(
            update_activities, args=(dataset_name, ignore_hashes),
            result_ttl=0, job_timeout=100000)


def status_line(msg, filt, tot):
    total_count = tot.count()
    filtered_count = filt.count()
    try:
        ratio = 1.0 * filtered_count / total_count
    except ZeroDivisionError:
        ratio = 0.0
    return "{filt_c:4d}/{tot_c:4d} ({pct:6.2%}) {msg}".format(
            filt_c=filtered_count,
            tot_c=total_count,
            pct=ratio,
            msg=msg
    )


@manager.cli.command('status')
def status_cmd():
    """Show status of current jobs"""
    print("%d jobs on queue" % rq.get_queue().count)

    print(status_line(
            "datasets have no metadata",
            Dataset.query.filter_by(last_modified=None),
            Dataset.query,
    ))

    print(status_line(
            "datasets not seen in the last day",
            Dataset.query.filter(Dataset.last_seen <
                                 (datetime.datetime.utcnow() - datetime.timedelta(days=1))),
            Dataset.query,
    ))

    print(status_line(
            "resources have had no attempt to fetch",
            Resource.query.outerjoin(Dataset).filter(
                    Resource.last_fetch == None),
            Resource.query,
    ))

    print(status_line(
            "resources not successfully fetched",
            Resource.query.outerjoin(Dataset).filter(
                    Resource.last_succ == None),
            Resource.query,
    ))

    print(status_line(
            "resources not fetched since modification",
            Resource.query.outerjoin(Dataset).filter(
                    sa.or_(
                            Resource.last_succ == None,
                            Resource.last_succ < Dataset.last_modified)),
            Resource.query,
    ))

    print(status_line(
            "resources not parsed since mod",
            Resource.query.outerjoin(Dataset).filter(
                    sa.or_(
                            Resource.last_succ == None,
                            Resource.last_parsed < Dataset.last_modified)),
            Resource.query,
    ))

    print(status_line(
          "resources have no activites",
          db.session.query(Resource.url).outerjoin(Activity)
          .group_by(Resource.url)
          .having(sa.func.count(Activity.iati_identifier) == 0),
          Resource.query))

    print("")

    total_activities = Activity.query.count()
    # out of date activitiy was created < resource last_parsed
    total_activities_fetched = Activity.query.join(Resource).filter(
        Activity.created < Resource.last_parsed).count()
    try:
        ratio = 1.0 * total_activities_fetched / total_activities
    except ZeroDivisionError:
        ratio = 0.0
    print("{nofetched_c}/{res_c} ({pct:6.2%}) activities out of date".format(
            nofetched_c=total_activities_fetched,
            res_c=total_activities,
            pct=ratio
    ))


@manager.cli.command('download')
def download_cmd():
    """
    Download all IATI data from IATI Data Dump.
    """
    iatikit.download.data()


def download_and_update(ignore_hashes):
    iatikit.download.data()
    update_registry(ignore_hashes)


@manager.cli.command('fetch-dataset-list')
def fetch_dataset_list_cmd():
    """
    Fetches dataset metadata from existing IATI Data Dump cache.
    """
    fetch_dataset_list()


@click.option('--ignore-hashes', is_flag=True,
              help="Ignore hashes in the database, which determine whether \
              activities should be updated or not, and update all data. \
              This will lead to a full refresh of data.")
@manager.cli.command('download-and-update')
def download_and_update_cmd(ignore_hashes):
    """
    Enqueue a download of all IATI data from
    IATI Data Dump, and then start an update.
    """
    queue = rq.get_queue()
    print("Enqueuing a download from IATI Data Dump")
    queue.enqueue(
        download_and_update,
        args=(ignore_hashes,),
        result_ttl=0,
        job_timeout=100000)


def update_registry(ignore_hashes):
    """
    Get all dataset metadata and update dataset data.
    """
    queue = rq.get_queue()
    datasets = fetch_dataset_list()
    print("Enqueuing %d datasets for update" % datasets.count())
    for dataset in datasets:
        queue.enqueue(update_dataset, args=(dataset.name, ignore_hashes), result_ttl=0)


@click.option('--dataset', 'dataset', type=str,
              help="update a single dataset")
@click.option('--ignore-hashes', is_flag=True,
              help="Ignore hashes in the database, which determine whether \
              activities should be updated or not, and update all data. \
              This will lead to a full refresh of data.")
@manager.cli.command('update')
def update_cmd(ignore_hashes, dataset=None):
    """
    Step through downloaded datasets, adding them to the dataset table, and then adding an update command to
    the Flask job queue. See update_registry, then update_dataset for next actions.
    """
    queue = rq.get_queue()

    if dataset is not None:
        print("Enqueuing {0} for update".format(dataset))
        queue.enqueue(update_dataset, args=(dataset, ignore_hashes), result_ttl=0)
    else:
        print("Enqueuing a full registry update")
        queue.enqueue(update_registry, args=(ignore_hashes,), result_ttl=0)

def download_currencies():
    """
    Download of all IMF currency conversion
    data, then update database.
    """
    rate_data = download_imf_exchange_rates()
    update_exchange_rates(rate_data)

@manager.cli.command('download-imf-currencies')
def download_currencies_cmd():
    """
    Enqueue a currency conversion data download.
    """
    queue = rq.get_queue()
    print("Enqueuing a download from IMF currency Data")
    queue.enqueue(
        download_currencies,
        args=(),
        result_ttl=0,
        job_timeout=100000)
