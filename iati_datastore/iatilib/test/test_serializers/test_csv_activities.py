import datetime
import inspect
from unittest import TestCase
from collections import namedtuple

from . import CSVTstMixin as _CSVTstMixin

from iatilib.test import factories as fac


from iatilib.frontend import serialize
from iatilib import codelists as cl


class TestCSVStream(TestCase):
    def test_stream(self):
        self.assertTrue(inspect.isgenerator(serialize.csv([])))


class CSVTstMixin(_CSVTstMixin):
    def serialize(self, data):
        return serialize.csv(data)


class TestCSVSerializer(CSVTstMixin, TestCase):
    def test_empty(self):
        data = self.process([])
        self.assertEqual(0, len(data))

    def test_len_one(self):
        data = self.process([fac.ActivityFactory.build()])
        self.assertEqual(1, len(data))

    def test_len_many(self):
        data = self.process([
            fac.ActivityFactory.build(),
            fac.ActivityFactory.build()
        ])
        self.assertEqual(2, len(data))

    def test_date_field(self):
        data = self.process([fac.ActivityFactory.build(
            start_planned=datetime.date(2012, 1, 1))
        ])
        self.assertField({"start-planned": "2012-01-01"}, data[0])

    def test_date_field_empty(self):
        data = self.process([fac.ActivityFactory.build(
            start_planned=None
        )])
        self.assertField({"start-planned": ""}, data[0])

    def test_quoting(self):
        data = self.process([fac.ActivityFactory.build(
            reporting_org=fac.OrganisationFactory.build(
                name=u"l,r"
            )
        )])
        self.assertField({"reporting-org": "l,r"}, data[0])

    def test_unicode(self):
        data = self.process([fac.ActivityFactory.build(
            reporting_org=fac.OrganisationFactory.build(
                name=u"\u2603"
            )
        )])
        self.assertField({"reporting-org": u"\u2603"}, data[0])

    def test_no_description(self):
        # Description is an optional thing
        data = self.process([fac.ActivityFactory.build(description="")])
        self.assertField({"description": ""}, data[0])


class TestCSVExample(CSVTstMixin, TestCase):
    # these tests are based around an example from IATI
    # https://docs.google.com/a/okfn.org/spreadsheet/ccc?key=0AqR8dXc6Ji4JdHJIWDJtaXhBV0IwOG56N0p1TE04V2c#gid=4

    def test_iati_identifier(self):
        data = self.process([
            fac.ActivityFactory.build(iati_identifier=u"GB-1-123")
        ])
        self.assertField({"iati-identifier": "GB-1-123"}, data[0])

    def test_title(self):
        data = self.process([
            fac.ActivityFactory.build(title=u"Project 123")
        ])
        self.assertField({"title": "Project 123"}, data[0])

    def test_description(self):
        data = self.process([fac.ActivityFactory.build(
            description=u"Description of Project 123")
        ])
        self.assertField({"description": "Description of Project 123"}, data[0])

    def test_start_planned(self):
        data = self.process([fac.ActivityFactory.build(
            start_planned=datetime.date(2011, 1, 1))
        ])
        self.assertField({"start-planned": "2011-01-01"}, data[0])

    def test_end_planned(self):
        data = self.process([fac.ActivityFactory.build(
            end_planned=datetime.date(2012, 1, 2))
        ])
        self.assertField({"end-planned": "2012-01-02"}, data[0])

    def test_start_actual(self):
        data = self.process([fac.ActivityFactory.build(
            start_actual=datetime.date(2012, 1, 3))
        ])
        self.assertField({"start-actual": "2012-01-03"}, data[0])

    def test_end_actual(self):
        data = self.process([fac.ActivityFactory.build(
            end_actual=datetime.date(2012, 1, 4))
        ])
        self.assertField({"end-actual": "2012-01-04"}, data[0])

    def test_recepient_country_code(self):
        data = self.process([fac.ActivityFactory.build(
            recipient_country_percentages=[
                fac.CountryPercentageFactory.build(country=cl.Country.kenya),
                fac.CountryPercentageFactory.build(country=cl.Country.uganda),
            ]
        )])
        self.assertField({
            "recipient-country-code": "KE;UG"}, data[0])

    def test_recepient_country(self):
        data = self.process([fac.ActivityFactory.build(
            recipient_country_percentages=[
                fac.CountryPercentageFactory.build(country=cl.Country.kenya),
                fac.CountryPercentageFactory.build(country=cl.Country.uganda),
            ]
        )])
        self.assertField({"recipient-country": "Kenya;Uganda"}, data[0])

    def test_recepient_country_percentage(self):
        data = self.process([fac.ActivityFactory.build(
            recipient_country_percentages=[
                fac.CountryPercentageFactory.build(percentage=80),
                fac.CountryPercentageFactory.build(percentage=20),
            ]
        )])
        self.assertField({"recipient-country-percentage": "80;20"}, data[0])

    def test_recipient_region_code(self):
        data = self.process([fac.ActivityFactory.build(
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                        region=cl.Region.europe_regional),
                fac.RegionPercentageFactory.build(
                        region=cl.Region.africa_regional),
            ]
        )])
        self.assertField({
            "recipient-region-code": "89;298"}, data[0])

    def test_recipient_region(self):
        data = self.process([fac.ActivityFactory.build(
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                        region=cl.Region.europe_regional),
                fac.RegionPercentageFactory.build(
                        region=cl.Region.africa_regional),
            ]
        )])
        self.assertField(
                {"recipient-region": "Europe, regional;Africa, regional"},
                data[0]
        )

    def test_recipient_region_percentage(self):
        data = self.process([fac.ActivityFactory.build(
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(percentage=80),
                fac.RegionPercentageFactory.build(percentage=20),
            ]
        )])
        self.assertField({"recipient-region-percentage": "80;20"}, data[0])

    def test_reporting_org(self):
        data = self.process([fac.ActivityFactory.build(
            reporting_org=fac.OrganisationFactory.build(
                name='rep',
                ref='rep_ref', type=cl.OrganisationType.foundation),
        )])
        self.assertField({"reporting-org": "rep"}, data[0])
        self.assertField({"reporting-org-ref": "rep_ref"}, data[0])
        self.assertField({"reporting-org-type": "Foundation"}, data[0])
        self.assertField({"reporting-org-type-code": "60"}, data[0])

    def test_accountable_org(self):
        data = self.process([fac.ActivityFactory.build(
            participating_orgs=[
                fac.ParticipationFactory.build(
                    organisation=fac.OrganisationFactory.build(name='acc', ref='acc_ref', type=cl.OrganisationType.foundation),
                    role=cl.OrganisationRole.accountable,

                ),
                fac.ParticipationFactory.build(
                    role=cl.OrganisationRole.funding),
                fac.ParticipationFactory.build(
                    role=cl.OrganisationRole.implementing),
            ]
        )])
        self.assertField({"participating-org (Accountable)": "acc"}, data[0])
        self.assertField({"participating-org-ref (Accountable)": "acc_ref"}, data[0])
        self.assertField({"participating-org-type (Accountable)": "Foundation"}, data[0])
        self.assertField({"participating-org-type-code (Accountable)": "60"}, data[0])

    def test_funding_org(self):
        data = self.process([fac.ActivityFactory.build(
            participating_orgs=[
                fac.ParticipationFactory.build(
                    organisation=fac.OrganisationFactory.build(
                        name='fund',
                        ref='fund_ref', type=cl.OrganisationType.foundation),
                    role=cl.OrganisationRole.funding),
            ]
        )])
        self.assertField({"participating-org (Funding)": "fund"}, data[0])
        self.assertField({"participating-org-ref (Funding)": "fund_ref"}, data[0])
        self.assertField({"participating-org-type (Funding)": "Foundation"}, data[0])
        self.assertField({"participating-org-type-code (Funding)": "60"}, data[0])

    def test_implementing_org(self):
        data = self.process([fac.ActivityFactory.build(
            participating_orgs=[
                fac.ParticipationFactory.build(
                    organisation=fac.OrganisationFactory.build(
                        name='impl',
                        ref="impl_ref", type=cl.OrganisationType.foundation),
                    role=cl.OrganisationRole.implementing),
            ]
        )])
        self.assertField({"participating-org (Implementing)": "impl"}, data[0])
        self.assertField({"participating-org-ref (Implementing)": "impl_ref"}, data[0])
        self.assertField({"participating-org-type (Implementing)": "Foundation"}, data[0])
        self.assertField({"participating-org-type-code (Implementing)": "60"}, data[0])

    def test_extending_org(self):
        data = self.process([fac.ActivityFactory.build(
            participating_orgs=[
                fac.ParticipationFactory.build(
                    organisation=fac.OrganisationFactory.build(
                        name='ext',
                        ref="ext_ref", type=cl.OrganisationType.foundation),
                    role=cl.OrganisationRole.extending),
            ]
        )])
        self.assertField({"participating-org (Extending)": "ext"}, data[0])
        self.assertField({"participating-org-ref (Extending)": "ext_ref"}, data[0])
        self.assertField({"participating-org-type (Extending)": "Foundation"}, data[0])
        self.assertField({"participating-org-type-code (Extending)": "60"}, data[0])

    def test_sector_code(self):
        data = self.process([fac.ActivityFactory.build(
            sector_percentages=[
                fac.SectorPercentageFactory.build(
                    sector=cl.Sector.teacher_training),
                fac.SectorPercentageFactory.build(
                    sector=cl.Sector.primary_education),
            ]
        )])
        self.assertField({"sector-code": "11130;11220"}, data[0])

    def test_sector_vocabulary(self):
        data = self.process([fac.ActivityFactory.build(
            sector_percentages=[
                fac.SectorPercentageFactory.build(
                    sector=cl.Sector.teacher_training,
                    vocabulary=cl.Vocabulary.aiddata),
                fac.SectorPercentageFactory.build(
                    sector=cl.Sector.primary_education,
                    vocabulary=cl.Vocabulary.world_bank),
            ]
        )])
        self.assertField({"sector-vocabulary": "AidData;World Bank"}, data[0])
        self.assertField({"sector-vocabulary-code": "ADT;WB"}, data[0])

    def test_sector(self):
        data = self.process([fac.ActivityFactory.build(
            sector_percentages=[
                fac.SectorPercentageFactory.build(
                    sector=cl.Sector.teacher_training),
                fac.SectorPercentageFactory.build(
                    sector=cl.Sector.primary_education),
            ]
        )])
        self.assertField(
            {"sector": u"Teacher training;Primary education"},
            data[0])

    def test_sector_blank(self):
        data = self.process([fac.ActivityFactory.build(
            sector_percentages=[
                fac.SectorPercentageFactory.build(sector=None)
            ]
        )])
        self.assertField({"sector": u""}, data[0])

    def test_sector_percentage(self):
        data = self.process([fac.ActivityFactory.build(
            sector_percentages=[
                fac.SectorPercentageFactory.build(percentage=60),
                fac.SectorPercentageFactory.build(percentage=40)
            ]
        )])
        self.assertField({"sector-percentage": "60;40"}, data[0])

    def test_default_currency(self):
        data = self.process([fac.ActivityFactory.build(
            default_currency=cl.Currency.us_dollar
        )])
        self.assertField({"default-currency": "USD"}, data[0])

    def test_currency(self):
        data = self.process([fac.ActivityFactory.build(
            transactions=[
                fac.TransactionFactory.build(
                    value_currency=cl.Currency.us_dollar
                )
            ]
        )])
        self.assertField({"currency": "USD"}, data[0])

    def test_currency_mixed(self):
        data = self.process([fac.ActivityFactory.build(
            transactions=[
                fac.TransactionFactory.build(
                    value_currency=cl.Currency.us_dollar
                ),
                fac.TransactionFactory.build(
                    value_currency=cl.Currency.australian_dollar
                ),
            ]
        )])
        self.assertField({"currency": "!Mixed currency"}, data[0])

    def test_activity_status(self):
        data = self.process([fac.ActivityFactory.build(
            activity_status=cl.ActivityStatus.pipelineidentification
        )])
        self.assertField({'activity-status-code': "1"}, data[0])

    def test_collaboration_type(self):
        data = self.process([fac.ActivityFactory.build(
            collaboration_type=cl.CollaborationType.bilateral
        )])
        self.assertField({'collaboration-type-code': "1"}, data[0])

    def test_default_finance_type(self):
        data = self.process([fac.ActivityFactory.build(
            default_finance_type=cl.FinanceType.bank_bonds
        )])
        self.assertField({'default-finance-type-code': "810"}, data[0])

    def test_default_flow_type(self):
        data = self.process([fac.ActivityFactory.build(
            default_flow_type=cl.FlowType.private_development_finance
        )])
        self.assertField({'default-flow-type-code': "30"}, data[0])

    def test_default_aid_type(self):
        data = self.process([fac.ActivityFactory.build(
            default_aid_type=cl.AidType.debt_relief
        )])
        self.assertField({'default-aid-type-code': "F01"}, data[0])

    def test_default_tied_status(self):
        data = self.process([fac.ActivityFactory.build(
            default_tied_status=cl.TiedStatus.tied
        )])
        self.assertField({'default-tied-status-code': "4"}, data[0])

    def test_hierarchy(self):
        data = self.process([fac.ActivityFactory.build(
            hierarchy=1
        )])
        self.assertField({'hierarchy': "1"}, data[0])

    def test_default_language(self):
        data = self.process([fac.ActivityFactory.build(
            default_language=cl.Language.english
        )])
        self.assertField({'default-language': "en"}, data[0])

    def test_last_updated_datetime(self):
        data = self.process([fac.ActivityFactory.build(
            last_updated_datetime=datetime.date(2012, 1, 1)
        )])
        self.assertField({'last-updated-datetime': "2012-01-01"}, data[0])

    def test_currency_missing(self):
        # If there is no default currency specified on the activity and
        # none on the transaction then we end up with a missing currency.
        data = self.process([fac.ActivityFactory.build(
            default_currency=None,
            transactions=[
                fac.TransactionFactory.build(
                    value_currency=None
                )
            ]
        )])
        self.assertField({"currency": ""}, data[0])

    def test_mixed_transation_types(self):
        data = self.process([fac.ActivityFactory.build(
            transactions=[
                fac.TransactionFactory.build(
                    type=cl.TransactionType.disbursement,
                    value_amount=1,
                ),
                fac.TransactionFactory.build(
                    type=cl.TransactionType.expenditure,
                    value_amount=2
                ),
            ]
        )])
        self.assertField({"currency": "USD"}, data[0])
        self.assertField({"total-Disbursement": "1"}, data[0])
        self.assertField({"total-Expenditure": "2"}, data[0])

    def test_column_list(self):
        data = self.process([
            fac.ActivityFactory.build(iati_identifier=u"GB-1-123")
        ])
        cols = [
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
            "recipient-region-code",
            "recipient-region",
            "recipient-region-percentage",
            "sector-code",
            "sector",
            "sector-percentage",
            "sector-vocabulary",
            "sector-vocabulary-code",
            "collaboration-type-code",
            "default-finance-type-code",
            "default-flow-type-code",
            "default-aid-type-code",
            "default-tied-status-code",
            "currency",
            "total-Commitment",
            "total-Disbursement",
            "total-Expenditure",
            "total-Incoming Funds",
            "total-Interest Repayment",
            "total-Loan Repayment",
            "total-Reimbursement"
        ]
        for col in cols:
            self.assertIn(col, data[0].keys(), msg="Missing col %s" % col)


cl2 = cl.by_major_version['2']


class TestCSVExample2(CSVTstMixin, TestCase):
    def test_sector_vocabulary(self):
        data = self.process([fac.ActivityFactory.build(
            sector_percentages=[
                fac.SectorPercentageFactory.build(
                    sector=cl2.Sector.teacher_training,
                    vocabulary=cl2.Vocabulary.aiddata),
                fac.SectorPercentageFactory.build(
                    sector=cl2.Sector.primary_education,
                    vocabulary=cl2.Vocabulary.oecd_dac_crs_purpose_codes_5_digit),
            ]
        )])
        self.assertField({"sector-vocabulary": "AidData;OECD DAC CRS Purpose Codes (5 digit)"}, data[0])
        self.assertField({"sector-vocabulary-code": "6;1"}, data[0])

    def test_accountable_org(self):
        data = self.process([fac.ActivityFactory.build(
            participating_orgs=[
                fac.ParticipationFactory.build(
                    organisation=fac.OrganisationFactory.build(name='acc', ref='acc_ref', type=cl2.OrganisationType.foundation),
                    role=cl2.OrganisationRole.accountable,

                ),
                fac.ParticipationFactory.build(
                    role=cl2.OrganisationRole.funding),
                fac.ParticipationFactory.build(
                    role=cl2.OrganisationRole.implementing),
            ],
            major_version='2'
        )])
        self.assertField({"participating-org (Accountable)": "acc"}, data[0])
        self.assertField({"participating-org-ref (Accountable)": "acc_ref"}, data[0])
        self.assertField({"participating-org-type (Accountable)": "Foundation"}, data[0])
        self.assertField({"participating-org-type-code (Accountable)": "60"}, data[0])

    def test_funding_org(self):
        data = self.process([fac.ActivityFactory.build(
            participating_orgs=[
                fac.ParticipationFactory.build(
                    organisation=fac.OrganisationFactory.build(
                        name='fund',
                        ref='fund_ref', type=cl2.OrganisationType.foundation),
                    role=cl2.OrganisationRole.funding),
            ],
            major_version='2'
        )])
        self.assertField({"participating-org (Funding)": "fund"}, data[0])
        self.assertField({"participating-org-ref (Funding)": "fund_ref"}, data[0])
        self.assertField({"participating-org-type (Funding)": "Foundation"}, data[0])
        self.assertField({"participating-org-type-code (Funding)": "60"}, data[0])

    def test_implementing_org(self):
        data = self.process([fac.ActivityFactory.build(
            participating_orgs=[
                fac.ParticipationFactory.build(
                    organisation=fac.OrganisationFactory.build(
                        name='impl',
                        ref="impl_ref", type=cl2.OrganisationType.foundation),
                    role=cl2.OrganisationRole.implementing),
            ],
            major_version='2'
        )])
        self.assertField({"participating-org (Implementing)": "impl"}, data[0])
        self.assertField({"participating-org-ref (Implementing)": "impl_ref"}, data[0])
        self.assertField({"participating-org-type (Implementing)": "Foundation"}, data[0])
        self.assertField({"participating-org-type-code (Implementing)": "60"}, data[0])

    def test_extending_org(self):
        data = self.process([fac.ActivityFactory.build(
            participating_orgs=[
                fac.ParticipationFactory.build(
                    organisation=fac.OrganisationFactory.build(
                        name='ext',
                        ref="ext_ref", type=cl2.OrganisationType.foundation),
                    role=cl2.OrganisationRole.extending),
            ],
            major_version='2'
        )])
        self.assertField({"participating-org (Extending)": "ext"}, data[0])
        self.assertField({"participating-org-ref (Extending)": "ext_ref"}, data[0])
        self.assertField({"participating-org-type (Extending)": "Foundation"}, data[0])
        self.assertField({"participating-org-type-code (Extending)": "60"}, data[0])


class ActivityExample(object):
    def example(self):
        activity = fac.ActivityFactory.build(
            iati_identifier=u"GB-1-123",
            title=u"Project 123",
            description=u"Desc 123",
            recipient_country_percentages=[
                fac.CountryPercentageFactory.build(
                    country=cl.Country.kenya,
                    percentage=80
                ),
                fac.CountryPercentageFactory.build(
                    country=cl.Country.uganda,
                    percentage=20
                ),
            ],
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                        region=cl.Region.europe_regional,
                        percentage=70
                ),
                fac.RegionPercentageFactory.build(
                        region=cl.Region.africa_regional,
                        percentage=30
                ),
            ],
            sector_percentages=[
                fac.SectorPercentageFactory.build(
                    sector=cl.Sector.teacher_training,
                    percentage=60),
                fac.SectorPercentageFactory.build(
                    sector=cl.Sector.primary_education,
                    percentage=40),
            ],
            transactions=[
                fac.TransactionFactory.build(
                    value_currency=cl.Currency.pound_sterling,
                    type=cl.TransactionType.commitment,
                    value_amount=130000
                )
            ]
        )
        return activity


class TestActivityByCountry(CSVTstMixin, ActivityExample, TestCase):
    def serialize(self, data):
        return serialize.csv_activity_by_country(data)

    def example(self):
        activity = super().example()
        NT = namedtuple('ActivityCountryPercentage', 'Activity CountryPercentage')
        return [
            NT(activity, activity.recipient_country_percentages[0]),
            NT(activity, activity.recipient_country_percentages[1])
        ]

    def test_column_list(self):
        NT = namedtuple('ActivityCountryPercentage', 'Activity CountryPercentage')
        data = self.process([
            NT(
                fac.ActivityFactory.build(iati_identifier=u"GB-1-123"),
                fac.CountryPercentageFactory.build()
            )
        ])
        cols = [
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
            "recipient-region-code",
            "recipient-region",
            "recipient-region-percentage",
            "sector-code",
            "sector",
            "sector-percentage",
            "sector-vocabulary",
            "sector-vocabulary-code",
            "collaboration-type-code",
            "default-finance-type-code",
            "default-flow-type-code",
            "default-aid-type-code",
            "default-tied-status-code",
            "currency",
            "total-Commitment",
            "total-Disbursement",
            "total-Expenditure",
            "total-Incoming Funds",
            "total-Interest Repayment",
            "total-Loan Repayment",
            "total-Reimbursement"
        ]
        for col in cols:
            self.assertIn(col, data[0].keys(), msg="Missing col %s" % col)

    def test_no_rows(self):
        data = self.process(self.example())
        self.assertEqual(2, len(data))

    def test_country_code_0(self):
        data = self.process(self.example())
        self.assertField({"recipient-country-code": u"KE"}, data[0])

    def test_country_code_1(self):
        data = self.process(self.example())
        self.assertField({"recipient-country-code": u"UG"}, data[1])

    def test_country(self):
        data = self.process(self.example())
        self.assertField({"recipient-country": u"Kenya"}, data[0])

    def test_recipient_country_percentage_0(self):
        data = self.process(self.example())
        self.assertField({"recipient-country-percentage": u"80"}, data[0])

    def test_recipient_country_percentage_1(self):
        data = self.process(self.example())
        self.assertField({"recipient-country-percentage": u"20"}, data[1])

    def test_recipient_region_code_0(self):
        data = self.process(self.example())
        self.assertField({"recipient-region-code": u"89;298"}, data[0])

    def test_recipient_region_code_1(self):
        data = self.process(self.example())
        self.assertField({"recipient-region-code": u"89;298"}, data[1])

    def test_recipient_region(self):
        data = self.process(self.example())
        self.assertField(
                {"recipient-region": u"Europe, regional;Africa, regional"},
                data[0]
        )

    def test_recipient_region_percentage_0(self):
        data = self.process(self.example())
        self.assertField({"recipient-region-percentage": u"70;30"}, data[0])

    def test_recipient_region_percentage_1(self):
        data = self.process(self.example())
        self.assertField({"recipient-region-percentage": u"70;30"}, data[1])

    def test_identifier(self):
        data = self.process(self.example())
        self.assertField({"iati-identifier": u"GB-1-123"}, data[0])

    def test_title(self):
        data = self.process(self.example())
        self.assertField({"title": u"Project 123"}, data[0])

    def test_description(self):
        data = self.process(self.example())
        self.assertField({"description": u"Desc 123"}, data[0])

    def test_sector_code_0(self):
        data = self.process(self.example())
        self.assertField({"sector-code": u"11130;11220"}, data[0])

    def test_sector_code_1(self):
        data = self.process(self.example())
        self.assertField({"sector-code": u"11130;11220"}, data[1])

    def test_sector(self):
        data = self.process(self.example())
        self.assertField(
            {"sector": u"Teacher training;Primary education"},
            data[1])

    def test_sector_percentage(self):
        data = self.process(self.example())
        self.assertField({"sector-percentage": u"60;40"}, data[1])

    def test_currency(self):
        data = self.process(self.example())
        self.assertField({"currency": u"GBP"}, data[1])

    def test_total_commitment(self):
        data = self.process(self.example())
        self.assertField({"total-Commitment": u"130000"}, data[0])


class TestActivityBySector(CSVTstMixin, ActivityExample, TestCase):
    def serialize(self, data):
        return serialize.csv_activity_by_sector(data)

    def example(self):
        activity = super().example()
        NT = namedtuple('ActivitySectorPercentage', 'Activity SectorPercentage')
        return [
            NT(activity, activity.sector_percentages[0]),
            NT(activity, activity.sector_percentages[1])
        ]

    def test_column_list(self):
        NT = namedtuple('ActivitySectorPercentage', 'Activity SectorPercentage')
        data = self.process([
            NT(
                fac.ActivityFactory.build(iati_identifier=u"GB-1-123"),
                fac.SectorPercentageFactory.build()
            )
        ])
        cols = [
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
            "recipient-region-code",
            "recipient-region",
            "recipient-region-percentage",
            "sector-code",
            "sector",
            "sector-percentage",
            "sector-vocabulary",
            "sector-vocabulary-code",
            "collaboration-type-code",
            "default-finance-type-code",
            "default-flow-type-code",
            "default-aid-type-code",
            "default-tied-status-code",
            "currency",
            "total-Commitment",
            "total-Disbursement",
            "total-Expenditure",
            "total-Incoming Funds",
            "total-Interest Repayment",
            "total-Loan Repayment",
            "total-Reimbursement"
        ]
        for col in cols:
            self.assertIn(col, data[0].keys(), msg="Missing col %s" % col)

    def test_no_rows(self):
        data = self.process(self.example())
        self.assertEqual(2, len(data))

    def test_sector_code_0(self):
        data = self.process(self.example())
        self.assertField({"sector-code": u"11130"}, data[0])

    def test_sector_code_1(self):
        data = self.process(self.example())
        self.assertField({"sector-code": u"11220"}, data[1])

    def test_sector_0(self):
        data = self.process(self.example())
        self.assertField({"sector": u"Teacher Training"}, data[0])

    def test_sector_1(self):
        data = self.process(self.example())
        self.assertField({"sector": u"Primary Education"}, data[1])

    def test_sector_percentage_0(self):
        data = self.process(self.example())
        self.assertField({"sector-percentage": u"60"}, data[0])

    def test_sector_percentage_1(self):
        data = self.process(self.example())
        self.assertField({"sector-percentage": u"40"}, data[1])

    def test_identifier(self):
        data = self.process(self.example())
        self.assertField({"iati-identifier": u"GB-1-123"}, data[0])

    def test_recipient_region_code_0(self):
        data = self.process(self.example())
        self.assertField({"recipient-region-code": u"89;298"}, data[0])

    def test_recipient_region_code_1(self):
        data = self.process(self.example())
        self.assertField({"recipient-region-code": u"89;298"}, data[1])

    def test_recipient_region(self):
        data = self.process(self.example())
        self.assertField(
                {"recipient-region": u"Europe, regional;Africa, regional"},
                data[0]
        )


class TotalFieldMixin(object):
    cl = cl

    # There are six total fields that behave identicaly
    def test_total(self):
        data = self.process([fac.ActivityFactory.build(
            transactions=[
                fac.TransactionFactory.build(
                    type=self.transaction_type,
                    value_amount=130000
                ),
            ]
        )])
        self.assertField({self.csv_field: "130000"}, data[0])

    def test_many_trans(self):
        data = self.process([fac.ActivityFactory.build(
            transactions=[
                fac.TransactionFactory.build(
                    type=self.transaction_type,
                    value_amount=2
                ),
                fac.TransactionFactory.build(
                    type=self.transaction_type,
                    value_amount=1
                ),
            ]
        )])
        self.assertField({self.csv_field: "3"}, data[0])

    def test_many_currencies(self):
        data = self.process([fac.ActivityFactory.build(
            transactions=[
                fac.TransactionFactory.build(
                    type=self.transaction_type,
                    value_amount=2,
                    value_currency=self.cl.Currency.us_dollar,
                ),
                fac.TransactionFactory.build(
                    type=self.transaction_type,
                    value_amount=1,
                    value_currency=self.cl.Currency.australian_dollar
                ),
            ]
        )])
        self.assertField({self.csv_field: "!Mixed currency"}, data[0])


class TestTotalDisbursement(CSVTstMixin, TotalFieldMixin, TestCase):
    transaction_type = cl.TransactionType.disbursement
    transaction_code = "D"
    csv_field = "total-Disbursement"


class TestTotalExpenditure(CSVTstMixin, TotalFieldMixin, TestCase):
    transaction_type = cl.TransactionType.expenditure
    csv_field = "total-Expenditure"


class TestTotalIncomingFunds(CSVTstMixin, TotalFieldMixin, TestCase):
    transaction_type = cl.TransactionType.incoming_funds
    csv_field = "total-Incoming Funds"


class TestTotalInterestRepayment(CSVTstMixin, TotalFieldMixin, TestCase):
    transaction_type = cl.TransactionType.interest_repayment
    csv_field = "total-Interest Repayment"


class TestTotalLoanRepayment(CSVTstMixin, TotalFieldMixin, TestCase):
    transaction_type = cl.TransactionType.loan_repayment
    csv_field = "total-Loan Repayment"


class TestTotalReimbursement(CSVTstMixin, TotalFieldMixin, TestCase):
    transaction_type = cl.TransactionType.reimbursement
    csv_field = "total-Reimbursement"


class TestTotalDisbursement2(CSVTstMixin, TotalFieldMixin, TestCase):
    cl = cl2
    transaction_type = cl2.TransactionType.disbursement
    csv_field = "total-Disbursement"


class TestTotalExpenditure2(CSVTstMixin, TotalFieldMixin, TestCase):
    cl = cl2
    transaction_type = cl2.TransactionType.expenditure
    csv_field = "total-Expenditure"


class TestTotalIncomingFunds2(CSVTstMixin, TotalFieldMixin, TestCase):
    cl = cl2
    transaction_type = cl2.TransactionType.incoming_funds
    csv_field = "total-Incoming Funds"


class TestTotalInterestRepayment2(CSVTstMixin, TotalFieldMixin, TestCase):
    cl = cl2
    transaction_type = cl2.TransactionType.interest_payment
    csv_field = "total-Interest Repayment"


class TestTotalLoanRepayment2(CSVTstMixin, TotalFieldMixin, TestCase):
    cl = cl2
    transaction_type = cl2.TransactionType.loan_repayment
    csv_field = "total-Loan Repayment"


class TestTotalReimbursement2(CSVTstMixin, TotalFieldMixin, TestCase):
    cl = cl2
    transaction_type = cl2.TransactionType.reimbursement
    csv_field = "total-Reimbursement"
