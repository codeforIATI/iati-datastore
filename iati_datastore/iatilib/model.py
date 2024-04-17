import datetime
import functools as ft
from collections import namedtuple

import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import JSONB

from . import codelists, db

act_relationship = ft.partial(
        sa.orm.relationship,
        cascade="all,delete",
        passive_deletes=True,
)
lazy_act_relationship = ft.partial(
        sa.orm.relationship,
        cascade="all,delete",
        lazy='dynamic',
        passive_deletes=True,
)

act_ForeignKey = ft.partial(
        sa.ForeignKey,
        ondelete="CASCADE"
)


# The "Unique Object" pattern
# http://www.sqlalchemy.org/trac/wiki/UsageRecipes/UniqueObject
def _unique(session, cls, hashfunc, queryfunc, constructor, arg, kw):
    cache = getattr(session, '_unique_cache', None)
    if cache is None:
        session._unique_cache = cache = {}

    key = (cls, hashfunc(*arg, **kw))
    if key in cache:
        if getattr(session, '_update_all_unique', False):
            obj = cache[key]
            for name, value in kw.items():
                setattr(obj, name, value)
            return obj
        else:
            return cache[key]
    else:
        with session.no_autoflush:
            q = session.query(cls)
            q = queryfunc(q, *arg, **kw)
            obj = q.first()
            if not obj:
                obj = constructor(*arg, **kw)
                session.add(obj)
            elif getattr(session, '_update_all_unique', False):
                for name, value in kw.items():
                    setattr(obj, name, value)
        cache[key] = obj
        return obj


class UniqueMixin(object):
    @classmethod
    def unique_hash(cls, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def unique_filter(cls, query, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def as_unique(cls, session, *arg, **kw):
        return _unique(
                session,
                cls,
                cls.unique_hash,
                cls.unique_filter,
                cls,
                arg, kw
        )


class TransactionType(object):
    def __init__(self, type_codes):
        self.type_codes = [x.value for x in type_codes]

    def __get__(self, obj, type=None):
        return [t for t in obj.transactions if t.type and t.type.value in self.type_codes]


class Participation(db.Model):
    __tablename__ = "participation"
    activity_identifier = sa.Column(
            act_ForeignKey("activity.iati_identifier"),
            primary_key=True)
    organisation_id = sa.Column(
            sa.ForeignKey("organisation.id"),
            primary_key=True)
    role = sa.Column(
            codelists.OrganisationRole.db_type(),
            primary_key=True)
    organisation = sa.orm.relationship("Organisation")


class Activity(db.Model):
    __tablename__ = "activity"
    iati_identifier = sa.Column(sa.Unicode, primary_key=True, nullable=False)
    hierarchy = sa.Column(sa.Integer)
    default_language = sa.Column(codelists.Language.db_type())
    # parsed from xml iati-activity@last-updated-datetime
    last_updated_datetime = sa.Column(sa.DateTime, nullable=True)
    # last time datastore has seen change in the activity
    last_change_datetime = sa.Column(sa.DateTime, nullable=False,
                                     default=sa.func.now())
    resource_url = sa.Column(
            sa.ForeignKey("resource.url", ondelete='CASCADE'),
            index=True,
            nullable=True)
    reporting_org_id = sa.Column(
            sa.ForeignKey("organisation.id"),
            nullable=True,
            index=True)
    start_planned = sa.Column(sa.Date, nullable=True)
    start_actual = sa.Column(sa.Date, nullable=True)
    end_planned = sa.Column(sa.Date, nullable=True)
    end_actual = sa.Column(sa.Date, nullable=True)
    title = sa.Column(sa.Unicode, default=u"", nullable=False)
    # Collect multiple title values. Key is lang attribute.
    title_all_values = sa.Column(JSONB, nullable=True)
    description = sa.Column(sa.Unicode, default=u"", nullable=False)
    # Collect multiple title values. First key is lang attribute. Second key is description type.
    description_all_values = sa.Column(JSONB, nullable=True)
    default_currency = sa.Column(codelists.Currency.db_type())
    raw_xml = sa.Column(
            sa.UnicodeText,
            nullable=False)
    # This should be nullable=False, but we have historical data from before this column was added to think about
    # Don't load by default - we only want it in one place, so we will explicitly undefer it there.
    raw_json = sa.orm.deferred(sa.Column(
            JSONB,
            nullable=True))
    version = sa.Column(
            sa.Unicode,
            nullable=True)
    major_version = sa.Column(
            sa.Unicode,
            nullable=False,
            default=u'1')

    commitments = TransactionType([
        codelists.by_major_version['1'].TransactionType.commitment,
        codelists.by_major_version['2'].TransactionType.outgoing_commitment,
        ])
    disbursements = TransactionType([codelists.by_major_version[mv].TransactionType.disbursement for mv in ['1', '2']])
    expenditures = TransactionType([codelists.by_major_version[mv].TransactionType.expenditure for mv in ['1', '2']])
    incoming_funds = TransactionType(
            [codelists.by_major_version[mv].TransactionType.incoming_funds for mv in ['1', '2']])
    interest_repayment = TransactionType([
        codelists.by_major_version['1'].TransactionType.interest_repayment,
        codelists.by_major_version['2'].TransactionType.interest_payment,
        ])
    loan_repayments = TransactionType(
            [codelists.by_major_version[mv].TransactionType.loan_repayment for mv in ['1', '2']])
    reembursements = TransactionType(
            [codelists.by_major_version[mv].TransactionType.reimbursement for mv in ['1', '2']])

    reporting_org = sa.orm.relationship("Organisation", uselist=False)
    activity_websites = act_relationship(
            "ActivityWebsite",
            cascade="all,delete")
    websites = association_proxy(
            "activity_websites",
            "url",
            creator=lambda url: ActivityWebsite(url=url))
    created = sa.Column(
            sa.DateTime,
            nullable=False,
            default=datetime.datetime.utcnow)
    participating_orgs = act_relationship("Participation")
    recipient_country_percentages = act_relationship("CountryPercentage")
    recipient_region_percentages = act_relationship("RegionPercentage")
    transactions = act_relationship("Transaction")
    sector_percentages = act_relationship("SectorPercentage")
    budgets = act_relationship("Budget")
    policy_markers = act_relationship("PolicyMarker")
    related_activities = act_relationship("RelatedActivity")
    resource = sa.orm.relationship("Resource")
    activity_status = sa.Column(codelists.ActivityStatus.db_type())
    collaboration_type = sa.Column(codelists.CollaborationType.db_type())
    default_finance_type = sa.Column(codelists.FinanceType.db_type())
    default_flow_type = sa.Column(codelists.FlowType.db_type())
    default_aid_type = sa.Column(codelists.AidType.db_type())
    default_tied_status = sa.Column(codelists.TiedStatus.db_type())


class DeletedActivity(db.Model):
    __tablename__ = "deleted_activity"
    iati_identifier = sa.Column(sa.Unicode, primary_key=True, nullable=False)
    deletion_date = sa.Column(sa.Date)


class Organisation(db.Model, UniqueMixin):
    __tablename__ = "organisation"
    id = sa.Column(sa.Integer, primary_key=True, nullable=False)
    ref = sa.Column(sa.Unicode, nullable=False)
    name = sa.Column(sa.Unicode, default=u"", nullable=True)
    name_all_values = sa.Column(JSONB, nullable=True)
    type = sa.Column(codelists.OrganisationType.db_type())
    __table_args__ = (sa.UniqueConstraint('ref', 'name', 'type'),)

    @classmethod
    def unique_hash(cls, ref, name, type, **kw):
        return ref, name, type

    @classmethod
    def unique_filter(cls, query, ref, name, type, **kw):
        return query.filter(
                (cls.ref == ref) & (cls.name == name) & (cls.type == type)
        )

    def __repr__(self):
        return "Organisation(ref=%r)" % self.ref


class ActivityWebsite(db.Model):
    __tablename__ = "website"
    id = sa.Column(
            sa.Integer,
            primary_key=True)
    activity_id = sa.Column(
            act_ForeignKey("activity.iati_identifier"),
            nullable=False,
            index=True)
    url = sa.Column(sa.Unicode)
    activity = sa.orm.relationship("Activity")


class PercentageMixin(object):
    @declared_attr
    def activity_id(cls):
        return sa.Column(
                act_ForeignKey("activity.iati_identifier"),
                nullable=True,
                index=True,
        )

    @declared_attr
    def transaction_id(cls):
        return sa.Column(
                act_ForeignKey("transaction.id"),
                nullable=True,
                index=True,
        )

    id = sa.Column(sa.Integer, primary_key=True)
    percentage = sa.Column(sa.Numeric, nullable=True)
    name = sa.Column(sa.Unicode, nullable=True)


class CountryPercentage(db.Model, PercentageMixin):
    __tablename__ = "country_percentage"
    country = sa.Column(codelists.Country.db_type(), index=True)


class RegionPercentage(db.Model, PercentageMixin):
    __tablename__ = "region_percentage"
    region = sa.Column(
            codelists.Region.db_type(),
            nullable=False,
            index=True)


class PolicyMarker(db.Model):
    __tablename__ = "policy_marker"
    id = sa.Column(sa.Integer, primary_key=True)
    activity_id = sa.Column(
            act_ForeignKey("activity.iati_identifier"),
            nullable=False,
            index=True)
    code = sa.Column(codelists.PolicyMarker.db_type(), nullable=True, index=True)
    significance = sa.Column(codelists.PolicySignificance.db_type(), nullable=True, index=True)
    text = sa.Column(sa.Unicode(), nullable=True)
    activity = sa.orm.relationship("Activity")


class RelatedActivity(db.Model):
    __tablename__ = "related_activity"
    id = sa.Column(sa.Integer, primary_key=True)
    activity_id = sa.Column(
            act_ForeignKey("activity.iati_identifier"),
            nullable=False,
            index=True)
    ref = sa.Column(sa.Unicode(), nullable=False)
    text = sa.Column(sa.Unicode())
    # i'd like to make this column a foreign key to activity, infact a self referential
    # relation would be nice but the standard allows a related-activity to have a type
    # which describes the type of relationship (parent, child, sibling etc) that makes
    # it nontrivial to model. It's probably best just to have it as free text, it will
    # will only be filtered on rather than joined.
    activity = sa.orm.relationship("Activity")


class TransactionValue(namedtuple("TransactionValue", "date amount currency")):
    def __composite_values__(self):
        return self.date, self.amount, self.currency


class Transaction(db.Model):
    __tablename__ = "transaction"
    id = sa.Column(sa.Integer, primary_key=True)
    ref = sa.Column(sa.Unicode, nullable=True)
    activity_id = sa.Column(
            act_ForeignKey("activity.iati_identifier"),
            nullable=False,
            index=True
    )
    activity = sa.orm.relationship("Activity")
    description = sa.Column(sa.Unicode, nullable=True)
    flow_type = sa.Column(codelists.FlowType.db_type(), nullable=True)
    finance_type = sa.Column(codelists.FinanceType.db_type())
    aid_type = sa.Column(codelists.AidType.db_type())
    tied_status = sa.Column(codelists.TiedStatus.db_type())
    disbursement_channel = sa.Column(codelists.DisbursementChannel.db_type())
    # The spec examples allows <provider-org ref="GB-1">DFID</provider-org>
    # the Organisation.name with ref is actually "Department for International
    # Development". So the text DFID is being stored in provider_org_text
    provider_org_id = sa.Column(sa.Integer, sa.ForeignKey("organisation.id"))
    provider_org = sa.orm.relationship(
            "Organisation",
            primaryjoin=provider_org_id == Organisation.id,
            foreign_keys=[provider_org_id],
    )
    provider_org_text = sa.Column(sa.Unicode, nullable=True)
    provider_org_activity_id = sa.Column(sa.Unicode, nullable=True)

    receiver_org_id = sa.Column(sa.Integer, sa.ForeignKey("organisation.id"))
    receiver_org = sa.orm.relationship(
            "Organisation",
            primaryjoin=receiver_org_id == Organisation.id,
            foreign_keys=[receiver_org_id],
    )
    receiver_org_text = sa.Column(sa.Unicode, nullable=True)
    receiver_org_activity_id = sa.Column(sa.Unicode, nullable=True)
    type = sa.Column(codelists.TransactionType.db_type(), nullable=True)
    date = sa.Column(sa.Date, nullable=True)
    value_date = sa.Column(sa.Date, nullable=True)
    value_amount = sa.Column(sa.Numeric(), nullable=True)
    value_usd = sa.Column(sa.Numeric(), nullable=True)
    value_eur = sa.Column(sa.Numeric(), nullable=True)
    value_currency = sa.Column(codelists.Currency.db_type())
    value = sa.orm.composite(TransactionValue, value_date, value_amount,
                             value_currency)

    recipient_country_percentages = act_relationship("CountryPercentage")
    recipient_region_percentages = act_relationship("RegionPercentage")
    sector_percentages = act_relationship("SectorPercentage")

    def __repr__(self):
        return u"Transaction(id=%r)" % self.id


class SectorPercentage(db.Model):
    __tablename__ = "sector_percentage"
    id = sa.Column(sa.Integer, primary_key=True)
    text = sa.Column(sa.Unicode)
    activity_id = sa.Column(
            act_ForeignKey("activity.iati_identifier"),
            nullable=True,
            index=True)
    transaction_id = sa.Column(
            act_ForeignKey("transaction.id"),
            nullable=True,
            index=True)
    sector = sa.Column(
        codelists.Sector.db_type(),
        nullable=True,
        index=True)
    vocabulary = sa.Column(
            codelists.Vocabulary.db_type(),
            default=codelists.Vocabulary.oecd_development_assistance_committee,
            nullable=False)
    percentage = sa.Column(sa.Numeric, nullable=True)
    activity = sa.orm.relationship("Activity")


class Budget(db.Model):
    __tablename__ = "budget"
    id = sa.Column(sa.Integer, primary_key=True)
    activity_id = sa.Column(
            act_ForeignKey("activity.iati_identifier"),
            nullable=False,
            index=True)
    type = sa.Column(codelists.BudgetType.db_type())
    period_end = sa.Column(sa.Date, nullable=True)
    period_start = sa.Column(sa.Date, nullable=True)
    value_currency = sa.Column(codelists.Currency.db_type())
    value_amount = sa.Column(sa.Numeric(), nullable=True)
    value_usd = sa.Column(sa.Numeric(), nullable=True)
    value_eur = sa.Column(sa.Numeric(), nullable=True)
    activity = sa.orm.relationship("Activity")


class Dataset(db.Model):
    __tablename__ = "dataset"
    name = sa.Column(sa.Unicode, primary_key=True)
    publisher = sa.Column(sa.Unicode)
    first_seen = sa.Column(
            sa.DateTime,
            nullable=False,
            default=sa.func.now())
    last_seen = sa.Column(
            sa.DateTime,
            nullable=False,
            default=sa.func.now())
    last_modified = sa.Column(sa.DateTime, nullable=True)
    resources = sa.orm.relationship("Resource",
                                    cascade="all, delete, delete-orphan",
                                    passive_deletes=True,
                                    backref="dataset")
    resource_urls = association_proxy(
            "resources",
            "url",
            creator=lambda url: Resource(url=url))
    license = sa.Column(sa.Unicode)
    is_open = sa.Column(sa.Boolean)


class Resource(db.Model):
    __tablename__ = "resource"
    url = sa.Column(sa.Unicode, primary_key=True)
    dataset_id = sa.Column(sa.ForeignKey("dataset.name", ondelete='CASCADE'), index=True)
    last_fetch = sa.Column(sa.DateTime)  # most recent request of this url
    last_status_code = sa.Column(sa.Integer)  # status code from last fetch
    last_succ = sa.Column(sa.DateTime)  # last time status code was 200
    last_parsed = sa.Column(sa.DateTime)  # when parsing last completed
    last_parse_error = sa.Column(sa.Unicode)  # last error from xml parser
    document = sa.orm.deferred(sa.Column(sa.LargeBinary))
    etag = sa.Column(sa.Unicode)
    activities = lazy_act_relationship("Activity", cascade="all,delete", passive_deletes=True)
    version = sa.Column(sa.Unicode)

class CurrencyConversion(db.Model):
    __tablename__ = "currency_conversion"
    id = sa.Column(sa.Integer, primary_key=True)
    date = sa.Column(sa.Date)
    rate = sa.Column(sa.Float)
    currency = sa.Column(sa.String)
    frequency = sa.Column(sa.String)
    source = sa.Column(sa.String)
    country_code = sa.Column(sa.String)
    country = sa.Column(sa.String)

class Log(db.Model):
    # A table to use like a logfile. Personally I don't like doing this but
    # it's the easiest way of dumping some log data to an accessable place
    # on Heroku.
    #
    # This comes from the Pyramid docs, there's also a log handler there.
    # http://docs.pylonsproject.org/projects/pyramid_cookbook/en/latest/logging/sqlalchemy_logger.html

    __tablename__ = 'log'
    id = sa.Column(sa.Integer, primary_key=True)
    dataset = sa.Column(sa.String)
    resource = sa.Column(sa.String, index=True)
    logger = sa.Column(sa.String, index=True)  # the name of the logger. (e.g. myapp.views)
    level = sa.Column(sa.String)  # info, debug, or error?
    trace = sa.Column(sa.String)  # the full traceback printout
    msg = sa.Column(sa.String)  # any custom log you may have included
    created_at = sa.Column(
            sa.DateTime,
            default=sa.func.now())  # the current timestamp

    def __repr__(self):
        return "<Log: %s - %s>" % (
            self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            self.msg[:50]
        )


class Stats(db.Model):
    # A cache of table counts.
    # The values in this table are updated automatically
    # in postgres - see:
    #   migrations/versions/120ee2333afe_.py
    __tablename__ = 'stats'
    label = sa.Column(
        sa.Unicode, primary_key=True,
        nullable=False)
    count = sa.Column(
        sa.Integer,
        nullable=False)


# We use sqlite for testing and postgres for prod. Sadly sqlite will only
# pay attention to forign keys if you tell it to.
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlite3 import Connection as SQLite3Connection


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
