import datetime
from functools import partial

import voluptuous as v
from voluptuous import Invalid, MultipleInvalid

from iatilib import codelists


def apidate(value):
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise Invalid(u"Date must be in the form yyyy-mm-dd")


def codelist_validator(Codelist, value):
    codes = []
    for i in value.split('|'):
        codes.append(Codelist.from_string(i))
    return codes


organisation_role = partial(codelist_validator, codelists.OrganisationRole)
recipient_country = partial(codelist_validator, codelists.Country)
recipient_region = partial(codelist_validator, codelists.Region)
reporting_org_type = partial(codelist_validator, codelists.OrganisationType)
sector = partial(codelist_validator, codelists.Sector)
policy_marker = partial(codelist_validator, codelists.PolicyMarker)
policy_significance = partial(codelist_validator, codelists.PolicySignificance)

pagination_schema = {
    "limit": v.All(v.Coerce(int), v.Range(max=1000)),
    "offset": v.All(v.Coerce(int), v.Range(min=0)),
}
pagination_args = v.Schema(pagination_schema)

activity_api_schema = {
    "date": apidate,
    "stream": v.All(v.Coerce(bool)),
    "unwrap": v.All(v.Coerce(bool)),
    'iati-identifier': v.All(v.Coerce(str)),
    'activity-status': v.All(v.Coerce(str)),
    'title': v.All(v.Coerce(str)),
    'description': v.All(v.Coerce(str)),
    'recipient-country': v.All(v.Coerce(str), recipient_country),
    'recipient-country.code': v.All(v.Coerce(str), recipient_country),
    'recipient-country.text': v.All(v.Coerce(str)),
    'recipient-region': v.All(v.Coerce(str), recipient_region),
    'recipient-region.code': v.All(v.Coerce(str), recipient_region),
    'recipient-region.text': v.All(v.Coerce(str)),
    'reporting-org': v.All(v.Coerce(str)),
    'reporting-org.ref': v.All(v.Coerce(str)),
    'reporting-org.type': v.All(v.Coerce(str), reporting_org_type),
    'reporting-org.text': v.All(v.Coerce(str)),
    'sector': v.All(v.Coerce(str), sector),
    'sector.code': v.All(v.Coerce(str), sector),
    'sector.text': v.All(v.Coerce(str)),
    'policy-marker': v.All(v.Coerce(str)),
    'policy-marker.code': v.All(v.Coerce(str), policy_marker),
    'policy-marker.significance': v.All(v.Coerce(str), policy_significance),
    'participating-org': v.All(v.Coerce(str)),
    'participating-org.ref': v.All(v.Coerce(str)),
    'participating-org.text': v.All(v.Coerce(str)),
    'participating-org.role': organisation_role,
    'related-activity': v.All(v.Coerce(str)),
    'related-activity.ref': v.All(v.Coerce(str)),
    'transaction.ref': v.All(v.Coerce(str)),
    'transaction': v.All(v.Coerce(str)),
    'transaction_provider-org': v.All(v.Coerce(str)),
    'transaction_provider-org.ref': v.All(v.Coerce(str)),
    'transaction_provider-org.text': v.All(v.Coerce(str)),
    'transaction_provider-org.type': v.All(v.Coerce(str)),
    'transaction_provider-org.provider-activity-id': v.All(v.Coerce(str)),
    'transaction_receiver-org': v.All(v.Coerce(str)),
    'transaction_receiver-org.ref': v.All(v.Coerce(str)),
    'transaction_receiver-org.text': v.All(v.Coerce(str)),
    'transaction_receiver-org.type': v.All(v.Coerce(str)),
    'transaction_receiver-org.receiver-activity-id': v.All(v.Coerce(str)),
    'start-date__gt': apidate,
    'start-date__lt': apidate,
    'end-date__gt': apidate,
    'end-date__lt': apidate,
    'last-change__gt': apidate,
    'last-change__lt': apidate,
    'last-updated-datetime__gt': apidate,
    'last-updated-datetime__lt': apidate,
    'registry-dataset': v.All(v.Coerce(str)),
    'participating-org-role-1': v.All(v.Coerce(str)),
    'participating-org-role-1.ref': v.All(v.Coerce(str)),
    'participating-org-role-1.text': v.All(v.Coerce(str)),
    'participating-org-role-1.type': v.All(v.Coerce(str)),
    'participating-org-role-2': v.All(v.Coerce(str)),
    'participating-org-role-2.ref': v.All(v.Coerce(str)),
    'participating-org-role-2.text': v.All(v.Coerce(str)),
    'participating-org-role-2.type': v.All(v.Coerce(str)),
    'participating-org-role-3': v.All(v.Coerce(str)),
    'participating-org-role-3.ref': v.All(v.Coerce(str)),
    'participating-org-role-3.text': v.All(v.Coerce(str)),
    'participating-org-role-3.type': v.All(v.Coerce(str)),
    'participating-org-role-4': v.All(v.Coerce(str)),
    'participating-org-role-4.ref': v.All(v.Coerce(str)),
    'participating-org-role-4.text': v.All(v.Coerce(str)),
    'participating-org-role-4.type': v.All(v.Coerce(str)),
}
activity_api_args = v.Schema({**pagination_schema, **activity_api_schema})

about_dataset_schema = {
    "detail": v.All(v.Coerce(bool)),
}
about_dataset_args = v.Schema({**pagination_schema, **about_dataset_schema})
