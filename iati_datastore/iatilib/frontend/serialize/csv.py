from collections import OrderedDict
from functools import partial
import csv as unicodecsv
import six
from io import StringIO, BytesIO
from operator import attrgetter
from iatilib import codelists
from pyexcelerate import Workbook
from openpyxl_copy.utils import get_column_letter
from flask_babel import gettext
from flask import request


USD = codelists.by_major_version['2'].Currency.from_string("USD")
EUR = codelists.by_major_version['2'].Currency.from_string("EUR")


def total(column, currency=None):
    def accessor(activity):
        if currency == USD:
            return sum(t.value_usd for t in getattr(activity, column) if t.value_usd)
        elif currency == EUR:
            return sum(t.value_eur for t in getattr(activity, column) if t.value_eur)
        else:
            if len(set(t.value.currency for t in getattr(activity, column))) > 1:
                return "!Mixed currency"
            return sum(t.value.amount for t in getattr(activity, column) if t.value.amount)
    return accessor


def currency(activity):
    if len(set(t.value.currency for t in activity.transactions)) > 1:
        return "!Mixed currency"
    curr = next(iter(set(t.value_currency for t in activity.transactions)), None)
    if curr:
        return curr.value
    return ""


def sector_code(activity):
    return u";".join(
        u"%s" % sec.sector.value if sec.sector else ""
        for sec in activity.sector_percentages)


def codelist_code(column_name, activity):
    column = getattr(activity, column_name)
    if column:
        return column.value
    else:
        return ""


def activity_status(activity):
    return activity.activity_status.description if activity.activity_status and activity.activity_status.description else ""


def collaboration_type(activity):
    return activity.collaboration_type.description if activity.collaboration_type and activity.collaboration_type.description else ""


def sector_percentage(activity):
    return u";".join(
        u"%d" % sec.percentage if sec.percentage else ""
        for sec in activity.sector_percentages)


def sector(activity):
    return u";".join(
        u"%s" % sec.sector.description if sec.sector and sec.sector.description else u""
        for sec in activity.sector_percentages)


def sector_vocabulary(activity):
    return u";".join(
        u"%s" % sec.vocabulary.description if sec.vocabulary and sec.vocabulary.description else u""
        for sec in activity.sector_percentages)


def sector_vocabulary_code(activity):
    return u";".join(
        u"%s" % sec.vocabulary.value if sec.vocabulary else u""
        for sec in activity.sector_percentages)


def default_currency(transaction):
    return activity_default_currency(transaction.activity)


def transaction_type(transaction):
    return transaction.type.value if transaction.type else ""


def transaction_date(transaction):
    return transaction.date.strftime("%Y-%m-%d") if transaction.date else ""


def transaction_value(transaction):
    return transaction.value.amount


def transaction_value_usd(transaction):
    return transaction.value_usd


def transaction_value_eur(transaction):
    return transaction.value_eur


def transaction_flow_type(transaction):
    return transaction.flow_type.value if transaction.flow_type else ""


def transaction_aid_type(transaction):
    return transaction.aid_type.value if transaction.aid_type else ""


def transaction_finance_type(transaction):
    return transaction.finance_type.value if transaction.finance_type else ""


def transaction_tied_status(transaction):
    return transaction.tied_status.value if transaction.tied_status else ""


def transaction_disbursement_channel(transaction):
    if transaction.disbursement_channel:
        return transaction.disbursement_channel.value
    return ""


def transaction_org(field, transaction):
    organisation = getattr(transaction, field)
    if organisation:
        return organisation.ref
    else:
        return ""


provider_org = partial(transaction_org, 'provider_org')
receiver_org = partial(transaction_org, 'receiver_org')


def title(activity):
    """Select most appropriate title for request locale"""
    locale = request.args.get("locale", "en")
    if activity.title_all_values and locale in activity.title_all_values:
        return activity.title_all_values[locale]
    elif activity.title_all_values and 'default' in activity.title_all_values:
        return activity.title_all_values['default']
    else:
        return activity.title

def description_most_general(all_values):
    """Select most general description type, lowest type code (as integer) wins"""
    out = None
    for desc_type in all_values:
        if not out:
            out = desc_type
        elif int(desc_type) < int(out):
            out = desc_type
    return all_values[out]

def select_description_type(all_values, desc_type_name):
    """Select description based on given description type"""
    codes = {'default': 0, 'general': '1', 'objectives': '2', 'target_groups': '3', 'other': '4'}
    if len(all_values) == 1 and desc_type_name == 'default':
        return next(iter(all_values))
    elif len(all_values) > 1 and desc_type_name == 'default':
        return description_most_general(all_values)
    elif desc_type_name != 'default':
        if codes[desc_type_name] in all_values:
            return all_values[codes[desc_type_name]]
        else:
            return ''

def description(desc_type_name, activity):
    """Select most appropriate description for requested locale and type"""
    locale = request.args.get("locale", "en")
    if activity.description_all_values and locale in activity.description_all_values:
        return select_description_type(activity.description_all_values[locale], desc_type_name)
    elif activity.description_all_values and 'default' in activity.description_all_values:
        return select_description_type(activity.description_all_values['default'], desc_type_name)
    else:
        return activity.description


iati_identifier = attrgetter("iati_identifier")
hierarchy = attrgetter("hierarchy")


def recipient_country_code(activity):
    return u";".join(
        rcp.country.value if rcp.country else "none"
        for rcp in activity.recipient_country_percentages)


def recipient_country(activity):
    return u";".join(
        rcp.country.description.title() if rcp.country and rcp.country.description else ""
        for rcp in activity.recipient_country_percentages)


def recipient_country_percentage(activity):
    return u";".join(
        u"%d" % rcp.percentage if rcp.percentage else ""
        for rcp in activity.recipient_country_percentages)


def recipient_region_code(activity):
    return u";".join(
        rrp.region.value
        for rrp in activity.recipient_region_percentages)


def recipient_region(activity):
    return u";".join(
        rrp.region.description if rrp.region and rrp.region.description else ""
        for rrp in activity.recipient_region_percentages)


def recipient_region_percentage(activity):
    return u";".join(
        u"%d" % rrp.percentage if rrp.percentage else ""
        for rrp in activity.recipient_region_percentages)


def reporting_org_ref(activity):
    try:
        return activity.reporting_org.ref
    except AttributeError:
        return ""


def reporting_org_name(activity):
    try:
        locale = request.args.get("locale", "en")
        if activity.reporting_org.name_all_values and locale in activity.reporting_org.name_all_values:
            return activity.reporting_org.name_all_values[locale]
        elif activity.reporting_org.name_all_values and 'default' in activity.reporting_org.name_all_values:
            return activity.reporting_org.name_all_values['default']
        else:
            return activity.reporting_org.name
    except AttributeError:
        return ""


def reporting_org_type(activity):
    try:
        return activity.reporting_org.type.description
    except AttributeError:
        return ""


def reporting_org_type_code(activity):
    try:
        return activity.reporting_org.type.value
    except AttributeError:
        return ""


def participating_org(attr, role, activity):
    activity_by_role = dict(
            [(a.role.value, a) for a in activity.participating_orgs])

    participant = activity_by_role.get(role.value, "")
    if participant:
        return getattr(participant.organisation, attr)
    else:
        return ''


participating_org_name = partial(participating_org, "name")
participating_org_ref = partial(participating_org, "ref")


def participating_org_type(role, activity):
    code = participating_org("type", role, activity)
    if code:
        return code.description
    else:
        return ""


def participating_org_type_code(role, activity):
    code = participating_org("type", role, activity)
    if code:
        return code.value
    else:
        return ""


def period_start_date(budget):
    if budget.period_start:
        return budget.period_start.strftime("%Y-%m-%d")
    return u""


def period_end_date(budget):
    if budget.period_end:
        return budget.period_end.strftime("%Y-%m-%d")
    return u""


def budget_value(budget):
    return budget.value_amount


def budget_value_usd(budget):
    return budget.value_usd


def budget_value_eur(budget):
    return budget.value_eur


def budget_type(budget):
    try:
        return budget.type.name
    except AttributeError:
        return ""


def value_currency(transaction):
    if transaction.value_currency:
        return transaction.value_currency.value
    else:
        return u""


def activity_default_currency(activity):
    if activity.default_currency:
        return activity.default_currency.value
    else:
        return u""


def fielddict_from_major_version(major_version):
    cl = codelists.by_major_version[major_version]

    class FieldDict(OrderedDict):
        common_field = {
            u"iati-identifier": iati_identifier,
            u"hierarchy": hierarchy,
            u"last-updated-datetime": attrgetter(u'last_updated_datetime'),
            u"default-language": partial(codelist_code, 'default_language'),
            u"reporting-org": reporting_org_name,
            u"reporting-org-ref": reporting_org_ref,
            u"reporting-org-type": reporting_org_type,
            u"reporting-org-type-code": reporting_org_type_code,
            u"title": title,
            u"description": partial(description, "default"),
            u"description_general": partial(description, "general"),
            u"description_objectives": partial(description, "objectives"),
            u"description_target_groups": partial(description, "target_groups"),
            u"description_other": partial(description, "other"),
            u"activity-status-code": partial(codelist_code, "activity_status"),
            u"start-planned": attrgetter(u"start_planned"),
            u"end-planned": attrgetter(u"end_planned"),
            u"start-actual": attrgetter(u"start_actual"),
            u"end-actual": attrgetter(u"end_actual"),
            u"participating-org (Accountable)": partial(
                participating_org_name,
                cl.OrganisationRole.accountable),
            u"participating-org-ref (Accountable)": partial(
                participating_org_ref,
                cl.OrganisationRole.accountable),
            u"participating-org-type (Accountable)": partial(
                participating_org_type,
                cl.OrganisationRole.accountable),
            u"participating-org-type-code (Accountable)": partial(
                participating_org_type_code,
                cl.OrganisationRole.accountable),
            u"participating-org (Funding)": partial(
                participating_org_name,
                cl.OrganisationRole.funding),
            u"participating-org-ref (Funding)": partial(
                participating_org_ref,
                cl.OrganisationRole.funding),
            u"participating-org-type (Funding)": partial(
                participating_org_type,
                cl.OrganisationRole.funding),
            u"participating-org-type-code (Funding)": partial(
                participating_org_type_code,
                cl.OrganisationRole.funding),
            u"participating-org (Extending)": partial(
                participating_org_name,
                cl.OrganisationRole.extending),
            u"participating-org-ref (Extending)": partial(
                participating_org_ref,
                cl.OrganisationRole.extending),
            u"participating-org-type (Extending)": partial(
                participating_org_type,
                cl.OrganisationRole.extending),
            u"participating-org-type-code (Extending)": partial(
                participating_org_type_code,
                cl.OrganisationRole.extending),
            u"participating-org (Implementing)": partial(
                participating_org_name,
                cl.OrganisationRole.implementing),
            u"participating-org-ref (Implementing)": partial(
                participating_org_ref,
                cl.OrganisationRole.implementing),
            u"participating-org-type (Implementing)": partial(
                participating_org_type,
                cl.OrganisationRole.implementing),
            u"participating-org-type-code (Implementing)": partial(
                participating_org_type_code,
                cl.OrganisationRole.implementing),
            u"recipient-country-code": recipient_country_code,
            u"recipient-country": recipient_country,
            u"recipient-country-percentage": recipient_country_percentage,
            u"sector-code": sector_code,
            u"sector": sector,
            u"sector-percentage": sector_percentage,
            u"sector-vocabulary": sector_vocabulary,
            u"sector-vocabulary-code": sector_vocabulary_code,
            u"collaboration-type-code": partial(codelist_code, "collaboration_type"),
            u"default-finance-type-code": partial(codelist_code, "default_finance_type"),
            u"default-flow-type-code": partial(codelist_code, "default_flow_type"),
            u"default-aid-type-code": partial(codelist_code, "default_aid_type"),
            u"default-tied-status-code": partial(codelist_code, "default_tied_status"),
            u"recipient-country-code": recipient_country_code,
            u"recipient-country": recipient_country,
            u"recipient-country-percentage": recipient_country_percentage,
            u"recipient-region-code": recipient_region_code,
            u"recipient-region": recipient_region,
            u"recipient-region-percentage": recipient_region_percentage,
            u"default-currency": activity_default_currency,
            u"currency": currency,
            u'total-Commitment': total("commitments"),
            u"total-Disbursement": total("disbursements"),
            u"total-Expenditure": total("expenditures"),
            u"total-Incoming Funds": total("incoming_funds"),
            u"total-Interest Repayment": total("interest_repayment"),
            u"total-Loan Repayment": total("loan_repayments"),
            u"total-Reimbursement": total("reembursements"),
            u'total-Commitment-USD': total("commitments", currency=USD),
            u"total-Disbursement-USD": total("disbursements", currency=USD),
            u"total-Expenditure-USD": total("expenditures", currency=USD),
            u"total-Incoming Funds-USD": total("incoming_funds", currency=USD),
            u"total-Interest Repayment-USD": total("interest_repayment", currency=USD),
            u"total-Loan Repayment-USD": total("loan_repayments", currency=USD),
            u"total-Reimbursement-USD": total("reembursements", currency=USD),
            u'total-Commitment-EUR': total("commitments", currency=EUR),
            u"total-Disbursement-EUR": total("disbursements", currency=EUR),
            u"total-Expenditure-EUR": total("expenditures", currency=EUR),
            u"total-Incoming Funds-EUR": total("incoming_funds", currency=EUR),
            u"total-Interest Repayment-EUR": total("interest_repayment", currency=EUR),
            u"total-Loan Repayment-EUR": total("loan_repayments", currency=EUR),
            u"total-Reimbursement-EUR": total("reembursements", currency=EUR),
        }

        def __init__(self, itr, *args, **kw):
            adapt = kw.pop("adapter", lambda i: i)

            def field_for(i):
                if isinstance(i, six.string_types):
                    cf = (i, self.common_field[i])
                    return cf[0], adapt(cf[1])
                elif isinstance(i, tuple):
                    return i
                else:
                    raise ValueError("%s is not allowed in FieldDict" % type(i))
            super().__init__(
                (field_for(i) for i in itr),
                *args,
                **kw
            )

    return FieldDict


fielddict_by_major_version = {
    major_version: fielddict_from_major_version(major_version)
    for major_version in ['1', '2']}


def identity(x):
    return x


class CSVSerializer(object):
    """
    A serializer that outputs the fields in the `fields` param.

    `fields` is a tuple which contains either strings which are
    names  of common fields or 2-tuples of (fieldname, accessor) where
    accessor is a function that will take an item from the query and
    return the field value

    `adaptor` is a function that will be composed with the accessors of
    the common fields to adapt them such that the objects for your query
    are compatible.
    """
    def __init__(self, fields, adapter=identity):
        self.get_major_version = adapter(lambda x: x.major_version)
        self.fields_by_major_version = {
            major_version: FieldDict(fields, adapter=adapter)
            for major_version, FieldDict in fielddict_by_major_version.items()}

    def __call__(self, data, wrapped=True):
        """
        Return a generator of lines of csv
        """
        def line(row):
            out = StringIO()
            writer = unicodecsv.writer(out)
            writer.writerow(row)
            return out.getvalue()
        yield line([gettext(label) for label in self.fields_by_major_version['1'].keys()])
        get_major_version = self.get_major_version
        for obj in data.items:
            row = [accessor(obj) for accessor in self.fields_by_major_version[get_major_version(obj)].values()]
            yield line(row)


class XLSXSerializer(object):
    def __init__(self, fields, adapter=identity, client_filename='iati_datastore_classic.xlsx'):
        self.file_mode = True
        self.client_filename = client_filename
        self.get_major_version = adapter(lambda x: x.major_version)
        self.fields_by_major_version = {
            major_version: FieldDict(fields, adapter=adapter)
            for major_version, FieldDict in fielddict_by_major_version.items()}

    def __call__(self, data, wrapped=True):
        outfile = BytesIO()
        # Create workbook
        wb = Workbook()
        ws = wb.new_sheet("data")
        # Headers
        headers = [gettext(label) for label in self.fields_by_major_version['1'].keys()]
        final_column = get_column_letter(len(headers))
        ws.range("A1", final_column+"1").value = [headers]
        # Data
        row_count = 2
        get_major_version = self.get_major_version
        for obj in data.items:
            row = [accessor(obj) for accessor in self.fields_by_major_version[get_major_version(obj)].values()]
            ws.range("A"+str(row_count), final_column+str(row_count)).value = [row]
            row_count += 1
        # Save
        wb.save(outfile)
        # Return
        outfile.seek(0)
        return {
            'file': outfile,
            'client_filename': self.client_filename
        }


_activity_fields = (
    "iati-identifier",
    "hierarchy",
    "last-updated-datetime",
    "default-language",
    "reporting-org",
    "reporting-org-ref",
    "reporting-org-type",
    "reporting-org-type-code",
    "title",
    "description",
    "description_general",
    "description_objectives",
    "description_target_groups",
    "description_other",
    "activity-status-code",
    "start-planned",
    "end-planned",
    "start-actual",
    "end-actual",
    "participating-org (Accountable)",
    "participating-org-ref (Accountable)",
    "participating-org-type (Accountable)",
    "participating-org-type-code (Accountable)",
    "participating-org (Funding)",
    "participating-org-ref (Funding)",
    "participating-org-type (Funding)",
    "participating-org-type-code (Funding)",
    "participating-org (Extending)",
    "participating-org-ref (Extending)",
    "participating-org-type (Extending)",
    "participating-org-type-code (Extending)",
    "participating-org (Implementing)",
    "participating-org-ref (Implementing)",
    "participating-org-type (Implementing)",
    "participating-org-type-code (Implementing)",
    "recipient-country-code",
    "recipient-country",
    "recipient-country-percentage",
    u"recipient-region-code",
    u"recipient-region",
    u"recipient-region-percentage",
    u"sector-code",
    u"sector",
    u"sector-percentage",
    u"sector-vocabulary",
    u"sector-vocabulary-code",
    u"collaboration-type-code",
    u"default-finance-type-code",
    u"default-flow-type-code",
    u"default-aid-type-code",
    u"default-tied-status-code",
    u"default-currency",
    u"currency",
    u'total-Commitment',
    u"total-Disbursement",
    u"total-Expenditure",
    u"total-Incoming Funds",
    u"total-Interest Repayment",
    u"total-Loan Repayment",
    u"total-Reimbursement",
    u'total-Commitment-USD',
    u"total-Disbursement-USD",
    u"total-Expenditure-USD",
    u"total-Incoming Funds-USD",
    u"total-Interest Repayment-USD",
    u"total-Loan Repayment-USD",
    u"total-Reimbursement-USD",
    u'total-Commitment-EUR',
    u"total-Disbursement-EUR",
    u"total-Expenditure-EUR",
    u"total-Incoming Funds-EUR",
    u"total-Interest Repayment-EUR",
    u"total-Loan Repayment-EUR",
    u"total-Reimbursement-EUR",
)

csv = CSVSerializer(_activity_fields)

xlsx = XLSXSerializer(_activity_fields, client_filename='activities.xlsx')


def adapt_activity(func):
    "Adapt an accessor to work against object's activtiy attrib"
    def wrapper(obj):
        return func(obj.activity)
    return wrapper


def adapt_activity_other(func):
    """
    Adapt an accessor for an activity to accept (Activity, other)

    other is Country or Sector, but that param is ignored anyway.
    """
    # can't use functools.wraps on attrgetter
    def wrapper(args):
        a, c = args
        return func(a)
    return wrapper


_activity_by_country_fields = (
    ("recipient-country-code", lambda r: r.CountryPercentage.country.value if r.CountryPercentage.country is not None else ""),
    ("recipient-country", lambda r: r.CountryPercentage.country.description.title() if r.CountryPercentage.country and r.CountryPercentage.country.description is not None else ""),
    ("recipient-country-percentage", lambda r: r.CountryPercentage.percentage if r.CountryPercentage.percentage is not None else ""),
    "iati-identifier",
    "hierarchy",
    "last-updated-datetime",
    "default-language",
    "reporting-org",
    "reporting-org-ref",
    "reporting-org-type",
    "reporting-org-type-code",
    "title",
    "description",
    "description_general",
    "description_objectives",
    "description_target_groups",
    "description_other",
    "activity-status-code",
    "start-planned",
    "end-planned",
    "start-actual",
    "end-actual",
    "participating-org (Accountable)",
    "participating-org-ref (Accountable)",
    "participating-org-type (Accountable)",
    "participating-org-type-code (Accountable)",
    "participating-org (Funding)",
    "participating-org-ref (Funding)",
    "participating-org-type (Funding)",
    "participating-org-type-code (Funding)",
    "participating-org (Extending)",
    "participating-org-ref (Extending)",
    "participating-org-type (Extending)",
    "participating-org-type-code (Extending)",
    "participating-org (Implementing)",
    "participating-org-ref (Implementing)",
    "participating-org-type (Implementing)",
    "participating-org-type-code (Implementing)",
    u"recipient-region-code",
    u"recipient-region",
    u"recipient-region-percentage",
    u"sector-code",
    u"sector",
    u"sector-percentage",
    u"sector-vocabulary",
    u"sector-vocabulary-code",
    u"collaboration-type-code",
    u"default-finance-type-code",
    u"default-flow-type-code",
    u"default-aid-type-code",
    u"default-tied-status-code",
    u"currency",
    u'total-Commitment',
    u"total-Disbursement",
    u"total-Expenditure",
    u"total-Incoming Funds",
    u"total-Interest Repayment",
    u"total-Loan Repayment",
    u"total-Reimbursement",
    u'total-Commitment-USD',
    u"total-Disbursement-USD",
    u"total-Expenditure-USD",
    u"total-Incoming Funds-USD",
    u"total-Interest Repayment-USD",
    u"total-Loan Repayment-USD",
    u"total-Reimbursement-USD",
    u'total-Commitment-EUR',
    u"total-Disbursement-EUR",
    u"total-Expenditure-EUR",
    u"total-Incoming Funds-EUR",
    u"total-Interest Repayment-EUR",
    u"total-Loan Repayment-EUR",
    u"total-Reimbursement-EUR",
)

csv_activity_by_country = CSVSerializer(_activity_by_country_fields, adapter=adapt_activity_other)

xlsx_activity_by_country = XLSXSerializer(_activity_by_country_fields, adapter=adapt_activity_other, client_filename='activities_by_country.xlsx')


_activity_by_sector_fields = (
    (u"sector-code", lambda r: r.SectorPercentage.sector.value if r.SectorPercentage.sector is not None else ""),
    (u"sector", lambda r: r.SectorPercentage.sector.description.title() if r.SectorPercentage.sector and r.SectorPercentage.sector.description is not None else ""),
    (u"sector-percentage", lambda r: r.SectorPercentage.percentage if r.SectorPercentage.percentage else ""),
    (u"sector-vocabulary", lambda r: r.SectorPercentage.vocabulary.description if r.SectorPercentage.vocabulary and r.SectorPercentage.vocabulary.description is not None else ""),
    (u"sector-vocabulary-code", lambda r: r.SectorPercentage.vocabulary.value if r.SectorPercentage.vocabulary and r.SectorPercentage.vocabulary.description is not None else ""),
    "iati-identifier",
    "hierarchy",
    "last-updated-datetime",
    "default-language",
    "reporting-org",
    "reporting-org-ref",
    "reporting-org-type",
    "reporting-org-type-code",
    "title",
    "description",
    "activity-status-code",
    "start-planned",
    "end-planned",
    "start-actual",
    "end-actual",
    "participating-org (Accountable)",
    "participating-org-ref (Accountable)",
    "participating-org-type (Accountable)",
    "participating-org-type-code (Accountable)",
    "participating-org (Funding)",
    "participating-org-ref (Funding)",
    "participating-org-type (Funding)",
    "participating-org-type-code (Funding)",
    "participating-org (Extending)",
    "participating-org-ref (Extending)",
    "participating-org-type (Extending)",
    "participating-org-type-code (Extending)",
    "participating-org (Implementing)",
    "participating-org-ref (Implementing)",
    "participating-org-type (Implementing)",
    "participating-org-type-code (Implementing)",
    "recipient-country-code",
    "recipient-country",
    "recipient-country-percentage",
    u"recipient-region-code",
    u"recipient-region",
    u"recipient-region-percentage",
    u"collaboration-type-code",
    u"default-finance-type-code",
    u"default-flow-type-code",
    u"default-aid-type-code",
    u"default-tied-status-code",
    u"currency",
    u'total-Commitment',
    u"total-Disbursement",
    u"total-Expenditure",
    u"total-Incoming Funds",
    u"total-Interest Repayment",
    u"total-Loan Repayment",
    u"total-Reimbursement",
    u'total-Commitment-USD',
    u"total-Disbursement-USD",
    u"total-Expenditure-USD",
    u"total-Incoming Funds-USD",
    u"total-Interest Repayment-USD",
    u"total-Loan Repayment-USD",
    u"total-Reimbursement-USD",
    u'total-Commitment-EUR',
    u"total-Disbursement-EUR",
    u"total-Expenditure-EUR",
    u"total-Incoming Funds-EUR",
    u"total-Interest Repayment-EUR",
    u"total-Loan Repayment-EUR",
    u"total-Reimbursement-EUR",
)

csv_activity_by_sector = CSVSerializer(_activity_by_sector_fields, adapter=adapt_activity_other)

xlsx_activity_by_sector = XLSXSerializer(_activity_by_sector_fields, adapter=adapt_activity_other, client_filename='activities_by_sector.xlsx')

common_transaction_csv = (
    (u'transaction_ref', lambda t: t.ref),
    (u'transaction_value_currency', value_currency),
    (u'transaction_value_value-date', lambda t: t.value_date),
    (u'transaction_provider-org', lambda t: t.provider_org_text),
    (u'transaction_provider-org_ref', provider_org),
    (u'transaction_provider-org_provider-activity-id',
     lambda t: t.provider_org_activity_id),
    (u'transaction_receiver-org', lambda t: t.receiver_org_text),
    (u'transaction_receiver-org_ref', receiver_org),
    (u'transaction_receiver-org_receiver-activity-id',
     lambda t: t.receiver_org_activity_id),
    (u'transaction_description', lambda t: t.description),
    (u'transaction_flow-type_code', transaction_flow_type),
    (u'transaction_finance-type_code', transaction_finance_type),
    (u'transaction_aid-type_code', transaction_aid_type),
    (u'transaction_tied-status_code', transaction_tied_status),
    (u'transaction_disbursement-channel_code',
     transaction_disbursement_channel),
    (u"transaction_recipient-country-code", recipient_country_code),
    (u"transaction_recipient-country", recipient_country),
    (u"transaction_recipient-region-code", recipient_region_code),
    (u"transaction_recipient-region", recipient_region),
    (u"transaction_sector-code", sector_code),
    (u"transaction_sector", sector),
    (u"transaction_sector-vocabulary", sector_vocabulary),
    (u"transaction_sector-vocabulary-code", sector_vocabulary_code),
    # (u'reporting-org', lambda t: t.activity.reporting_org_ref),
)

_transaction_fields = (
    (u'transaction-type', transaction_type),
    (u'transaction-date', transaction_date),
    (u"default-currency", default_currency),
    (u"transaction-value", transaction_value),
    (u"transaction-value-USD", transaction_value_usd),
    (u"transaction-value-EUR", transaction_value_eur),
    ) + common_transaction_csv + (
    "iati-identifier",
     "hierarchy",
     "last-updated-datetime",
     "default-language",
     "reporting-org",
     "reporting-org-ref",
     "reporting-org-type",
     "reporting-org-type-code",
     "title",
     "description",
     "activity-status-code",
     "start-planned",
     "end-planned",
     "start-actual",
     "end-actual",
     "participating-org (Accountable)",
     "participating-org-ref (Accountable)",
     "participating-org-type (Accountable)",
     "participating-org-type-code (Accountable)",
     "participating-org (Funding)",
     "participating-org-ref (Funding)",
     "participating-org-type (Funding)",
     "participating-org-type-code (Funding)",
     "participating-org (Extending)",
     "participating-org-ref (Extending)",
     "participating-org-type (Extending)",
     "participating-org-type-code (Extending)",
     "participating-org (Implementing)",
     "participating-org-ref (Implementing)",
     "participating-org-type (Implementing)",
     "participating-org-type-code (Implementing)",
     "recipient-country-code",
     "recipient-country",
     "recipient-country-percentage",
     u"recipient-region-code",
     u"recipient-region",
     u"recipient-region-percentage",
     u"sector-code",
     u"sector",
     u"sector-percentage",
     u"sector-vocabulary",
     u"sector-vocabulary-code",
     u"collaboration-type-code",
     u"default-finance-type-code",
     u"default-flow-type-code",
     u"default-aid-type-code",
     u"default-tied-status-code",
    )


transaction_csv = CSVSerializer(_transaction_fields, adapter=adapt_activity)

transaction_xlsx = XLSXSerializer(_transaction_fields, adapter=adapt_activity, client_filename='transactions.xlsx')


def trans(func):
    def wrapper(args):
        t, c = args
        return func(t)
    return wrapper


def trans_activity(func):
    def wrapper(args):
        t, c = args
        return func(t.activity)
    return wrapper


_transaction_by_country_fields = (
    (u"recipient-country-code", lambda r: r.CountryPercentage.country.value if r.CountryPercentage.country is not None else ""),
    (u"recipient-country", lambda r: r.CountryPercentage.country.description.title() if (r.CountryPercentage.country is not None and r.CountryPercentage.country.description is not None) else ""),
    (u"recipient-country-percentage", lambda r: r.CountryPercentage.percentage),
    (u'transaction-type', trans(transaction_type)),
    (u'transaction-date', trans(transaction_date)),
    (u"default-currency", trans(default_currency)),
    (u'transaction-value', trans(transaction_value)),
    (u"transaction-value-USD", trans(transaction_value_usd)),
    (u"transaction-value-EUR", trans(transaction_value_eur)),
    ) + tuple([(i[0], trans(i[1])) for i in common_transaction_csv]) + (
    "iati-identifier",
     "hierarchy",
     "last-updated-datetime",
     "default-language",
     "reporting-org",
     "reporting-org-ref",
     "reporting-org-type",
     "reporting-org-type-code",
     "title",
     "description",
     "activity-status-code",
     "start-planned",
     "end-planned",
     "start-actual",
     "end-actual",
     "participating-org (Accountable)",
     "participating-org-ref (Accountable)",
     "participating-org-type (Accountable)",
     "participating-org-type-code (Accountable)",
     "participating-org (Funding)",
     "participating-org-ref (Funding)",
     "participating-org-type (Funding)",
     "participating-org-type-code (Funding)",
     "participating-org (Extending)",
     "participating-org-ref (Extending)",
     "participating-org-type (Extending)",
     "participating-org-type-code (Extending)",
     "participating-org (Implementing)",
     "participating-org-ref (Implementing)",
     "participating-org-type (Implementing)",
     "participating-org-type-code (Implementing)",
     u"recipient-region-code",
     u"recipient-region",
     u"recipient-region-percentage",
     u"sector-code",
     u"sector",
     u"sector-percentage",
     u"sector-vocabulary",
     u"sector-vocabulary-code",
     u"collaboration-type-code",
     u"default-finance-type-code",
     u"default-flow-type-code",
     u"default-aid-type-code",
     u"default-tied-status-code",
     )

csv_transaction_by_country = CSVSerializer(_transaction_by_country_fields, adapter=trans_activity)

xlsx_transaction_by_country = XLSXSerializer(_transaction_by_country_fields, adapter=trans_activity, client_filename='transactions_by_country.xlsx')


_transaction_by_sector_fields = (
    (u"sector-code", lambda r: r.SectorPercentage.sector.value if r.SectorPercentage.sector is not None else ""),
    (u"sector", lambda r: r.SectorPercentage.sector.description.title() if (r.SectorPercentage.sector is not None and r.SectorPercentage.sector.description is not None) else ""),
    (u"sector-percentage", lambda r: r.SectorPercentage.percentage),
    (u"sector-vocabulary", lambda r: r.SectorPercentage.vocabulary.description if r.SectorPercentage.vocabulary is not None else ""),
    (u"sector-vocabulary-code", lambda r: r.SectorPercentage.vocabulary.value if r.SectorPercentage.vocabulary is not None else ""),
    (u'transaction-type', trans(transaction_type)),
    (u'transaction-date', trans(transaction_date)),
    (u"default-currency", trans(default_currency)),
    (u'transaction-value', trans(transaction_value)),
    (u"transaction-value-USD", trans(transaction_value_usd)),
    (u"transaction-value-EUR", trans(transaction_value_eur)),
    ) + tuple([(i[0], trans(i[1])) for i in common_transaction_csv]) + (
    "iati-identifier",
     "hierarchy",
     "last-updated-datetime",
     "default-language",
     "reporting-org",
     "reporting-org-ref",
     "reporting-org-type",
     "reporting-org-type-code",
     "title",
     "description",
     "activity-status-code",
     "start-planned",
     "end-planned",
     "start-actual",
     "end-actual",
     "participating-org (Accountable)",
     "participating-org-ref (Accountable)",
     "participating-org-type (Accountable)",
     "participating-org-type-code (Accountable)",
     "participating-org (Funding)",
     "participating-org-ref (Funding)",
     "participating-org-type (Funding)",
     "participating-org-type-code (Funding)",
     "participating-org (Extending)",
     "participating-org-ref (Extending)",
     "participating-org-type (Extending)",
     "participating-org-type-code (Extending)",
     "participating-org (Implementing)",
     "participating-org-ref (Implementing)",
     "participating-org-type (Implementing)",
     "participating-org-type-code (Implementing)",
     "recipient-country-code",
     "recipient-country",
     "recipient-country-percentage",
     u"recipient-region-code",
     u"recipient-region",
     u"recipient-region-percentage",
     u"collaboration-type-code",
     u"default-finance-type-code",
     u"default-flow-type-code",
     u"default-aid-type-code",
     u"default-tied-status-code",
     )


csv_transaction_by_sector = CSVSerializer(_transaction_by_sector_fields, adapter=trans_activity)

xlsx_transaction_by_sector = XLSXSerializer(_transaction_by_sector_fields, adapter=trans_activity, client_filename='transactions_by_sector.xlsx')

_budget_fields = (
    (u'budget-period-start-date', period_start_date),
    (u'budget-period-end-date', period_end_date),
    (u"budget-value", budget_value),
    (u"budget-value-USD", budget_value_usd),
    (u"budget-value-EUR", budget_value_eur),
    (u"budget-type", budget_type),
    u"iati-identifier",
    u"title",
    u"description",
    u"recipient-country-code",
    u"recipient-country",
    u"recipient-country-percentage",
    u"sector-code",
    u"sector",
    u"sector-percentage",
)

budget_csv = CSVSerializer(_budget_fields, adapter=adapt_activity)

budget_xlsx = XLSXSerializer(_budget_fields, adapter=adapt_activity, client_filename='budgets.xlsx')

_budget_by_country_fields = (
    (u"recipient-country-code", lambda r: r.CountryPercentage.country.value if r.CountryPercentage.country is not None else ""),
    (u"recipient-country", lambda r: r.CountryPercentage.country.description.title() if (r.CountryPercentage.country is not None and r.CountryPercentage.country.description is not None) else ""),
    (u"recipient-country-percentage", lambda r: r.CountryPercentage.percentage),
    (u'budget-period-start-date', trans(period_start_date)),
    (u'budget-period-end-date', trans(period_end_date)),
    (u"budget-value", trans(budget_value)),
    (u"budget-value-USD", trans(budget_value_usd)),
    (u"budget-value-EUR", trans(budget_value_eur)),
    (u"budget-type", trans(budget_type)),
    u"iati-identifier",
    u"title",
    u"description",
    u"sector-code",
    u"sector",
    u"sector-percentage",
)

csv_budget_by_country = CSVSerializer(_budget_by_country_fields, adapter=trans_activity)

xlsx_budget_by_country = XLSXSerializer(_budget_by_country_fields, adapter=trans_activity, client_filename='budgets_by_country.xlsx')


_budget_by_sector_fields = (
    (u"sector-code", lambda r: r.SectorPercentage.sector.value if r.SectorPercentage.sector is not None else ""),
    (u"sector", lambda r: r.SectorPercentage.sector.description.title() if (r.SectorPercentage.sector is not None and r.SectorPercentage.sector.description is not None) else ""),
    (u"sector-percentage", lambda r: r.SectorPercentage.percentage),
    (u'budget-period-start-date', trans(period_start_date)),
    (u'budget-period-end-date', trans(period_end_date)),
    (u"budget-value", trans(budget_value)),
    (u"budget-value-USD", trans(budget_value_usd)),
    (u"budget-value-EUR", trans(budget_value_eur)),
    (u"budget-type", trans(budget_type)),
    u"iati-identifier",
    u"title",
    u"description",
)

csv_budget_by_sector = CSVSerializer(_budget_by_sector_fields, adapter=trans_activity)

xlsx_budget_by_sector = XLSXSerializer(_budget_by_sector_fields, adapter=trans_activity, client_filename='budgets_by_sector.xlsx')

