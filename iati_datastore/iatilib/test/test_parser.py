import datetime
from decimal import Decimal
from unittest import TestCase

import mock
from lxml import etree as ET

from iatilib.test import db, AppTestCase, fixture_filename
from iatilib import parse, codelists as cl
from iatilib import model
cl2 = cl.by_major_version['2']


def fixture(fix_name, encoding='utf-8'):
    return open(fixture_filename(fix_name), encoding=encoding).read()


def parse_fixture(fix_name, encoding='utf-8'):
    return ET.parse(fixture_filename(fix_name))


class TestParse2xxActivity(AppTestCase):
    def setUp(self):
        super().setUp()
        self.activities = list(parse.document_from_file(fixture_filename("2.01-example-annotated.xml")))
        self.act = self.activities[0]

    def test_id(self):
        self.assertEqual(
            u"AA-AAA-123456789-ABC123",
            self.act.iati_identifier)

    def test_title(self):
        self.assertEqual(
            u"Activity title",
            self.act.title)

    def test_last_updated_time(self):
        self.assertEqual(datetime.date(2014, 9, 10), self.act.last_updated_datetime)

    def test_description(self):
        self.assertTrue(self.act.description.startswith(
            u"General activity description text."))

    def test_reporting_org_ref(self):
        self.assertEqual(u"AA-AAA-123456789", self.act.reporting_org.ref)

    def test_reporting_org_type(self):
        self.assertEqual(
            cl2.OrganisationType.multilateral,
            self.act.reporting_org.type
        )

    def test_reporting_org_name(self):
        self.assertEqual(
            self.act.reporting_org.name,
            u"Organisation name"
        )

    def test_default_currency(self):
        self.assertEqual(
            cl2.Currency.us_dollar,
            self.act.default_currency
        )

    def test_participating_org(self):
        self.assertEqual(
            cl2.OrganisationRole.funding,
            self.act.participating_orgs[0].role)
        self.assertEqual(
            cl2.OrganisationType.multilateral,
            self.act.participating_orgs[0].organisation.type)
        self.assertEqual(
            cl2.OrganisationType.multilateral,
            self.act.participating_orgs[0].organisation.type)
        self.assertEqual(
            u"BB-BBB-123456789",
            self.act.participating_orgs[0].organisation.ref)
        self.assertEqual(
            u"Name of Agency B",
            self.act.participating_orgs[0].organisation.name)

        self.assertEqual(
            cl2.OrganisationRole.accountable,
            self.act.participating_orgs[1].role)
        self.assertEqual(
            cl2.OrganisationType.government,
            self.act.participating_orgs[1].organisation.type)
        self.assertEqual(
            u"CC-CCC-123456789",
            self.act.participating_orgs[1].organisation.ref)
        self.assertEqual(
            u"Name of Agency C",
            self.act.participating_orgs[1].organisation.name)

        self.assertEqual(
            cl2.OrganisationRole.extending,
            self.act.participating_orgs[2].role)
        self.assertEqual(
            cl2.OrganisationType.international_ngo,
            self.act.participating_orgs[2].organisation.type)
        self.assertEqual(
            u"AA-AAA-123456789",
            self.act.participating_orgs[2].organisation.ref)
        self.assertEqual(
            u"Name of Agency A",
            self.act.participating_orgs[2].organisation.name)

    def test_recipient_country_percentages(self):
        act = self.act
        self.assertEqual(2, len(self.act.recipient_country_percentages))
        self.assertEqual(
            cl2.Country.afghanistan,
            act.recipient_country_percentages[0].country)
        self.assertEqual(
            cl2.Country.antigua_and_barbuda,
            act.recipient_country_percentages[1].country)
        self.assertEqual(
            25,
            act.recipient_country_percentages[0].percentage)
        self.assertEqual(
            25,
            act.recipient_country_percentages[1].percentage)

    def test_recipient_region_percentages(self):
        act = self.act
        self.assertEqual(2, len(act.recipient_region_percentages))
        self.assertEqual(
            cl2.Region.south_america_regional,
            act.recipient_region_percentages[0].region)
        self.assertEqual(
            cl2.Region.south_of_sahara_regional,
            act.recipient_region_percentages[1].region)
        self.assertEqual(
            25,
            act.recipient_region_percentages[0].percentage)
        self.assertEqual(
            25,
            act.recipient_region_percentages[1].percentage)

    def test_misc_narratives(self):
        act = parse.activity(ET.XML(
            u'''<iati-activity>
                    <iati-identifier>AAA-AA</iati-identifier>
                    <reporting-org ref="AAA"/>
                    <recipient-country code="XX">
                        <narrative>N1</narrative>
                    </recipient-country>
                    <recipient-region code="XXX">
                        <narrative>N2</narrative>
                    </recipient-region>
                    <sector vocabulary="RO">
                        <narrative>N3</narrative>
                    </sector>
                    <policy-marker>
                        <narrative>N4</narrative>
                    </policy-marker>
                    <related-activity ref="">
                        <narrative>N5</narrative>
                    </related-activity>
                </iati-activity>'''
        ), major_version='2')
        self.assertEqual(
            "N1", act.recipient_country_percentages[0].name)
        self.assertEqual(
            "N2", act.recipient_region_percentages[0].name)
        self.assertEqual(
            "N3", act.sector_percentages[0].text)
        self.assertEqual(
            "N4", act.policy_markers[0].text)
        self.assertEqual(
            "N5", act.related_activities[0].text)

    def test_transaction_count(self):
        self.assertEqual(1, len(self.act.transactions))

    def test_transaction_type(self):
        self.assertEqual(
            cl2.TransactionType.incoming_funds,
            self.act.transactions[0].type)

    def test_transaction_date(self):
        self.assertEqual(
            datetime.date(2012, 1, 1),
            self.act.transactions[0].date)

    def test_transaction_value_date(self):
        self.assertEqual(
            datetime.date(2012, 1, 1),
            self.act.transactions[0].value_date)

    def test_transaction_value_amount(self):
        self.assertEqual(
            1000,
            self.act.transactions[0].value_amount)

    def test_transaction_currency(self):
        self.assertEqual(
            cl2.Currency.euro,
            self.act.transactions[0].value_currency)

    def test_transaction_value_composite(self):
        self.assertEqual(
            (datetime.date(2012, 1, 1), 1000, cl2.Currency.euro),
            self.act.transactions[0].value)

    def test_transaction_ref(self):
        self.assertEqual(u'1234', self.act.transactions[0].ref)

    def test_transaction_description(self):
        self.assertEqual(u'Transaction description text',
                          self.act.transactions[0].description)

    def test_transaction_provider_org_ref(self):
        self.assertEqual(u'BB-BBB-123456789',
                          self.act.transactions[0].provider_org.ref)

    def test_transaction_provider_org_name(self):
        self.assertEqual(u'Agency B',
                          self.act.transactions[0].provider_org.name)

    def test_transaction_reciever_org_ref(self):
        self.assertEqual(u'AA-AAA-123456789',
                          self.act.transactions[0].receiver_org.ref)

    def test_transaction_reciever_org_name(self):
        self.assertEqual(u'Agency A',
                          self.act.transactions[0].receiver_org.name)

    def test_transaction_new_elements(self):
        act = self.act
        self.assertEqual(1, len(act.transactions[0].recipient_region_percentages))
        self.assertEqual(1, len(act.transactions[0].recipient_country_percentages))
        self.assertEqual(1, len(act.transactions[0].sector_percentages))
        self.assertEqual(
            cl2.Country.afghanistan,
            act.transactions[0].recipient_country_percentages[0].country)
        self.assertEqual(
            u'456',
            act.transactions[0].recipient_region_percentages[0].region.value)
        self.assertEqual(
            u'111',
            act.transactions[0].sector_percentages[0].sector.value)

    def test_date_start_planned(self):
        self.assertEqual(datetime.date(2012, 4, 15), self.act.start_planned)

    def test_date_start_actual(self):
        self.assertEqual(datetime.date(2012, 4, 28), self.act.start_actual)

    def test_date_end_planned(self):
        self.assertEqual(datetime.date(2015, 12, 31), self.act.end_planned)

    def test_date_end_actual(self):
        self.assertEqual(None, self.act.end_actual)

    def test_raw_xml(self):
        norm_xml = ET.tostring(ET.parse(fixture_filename("2.01-example-annotated.xml")).find('iati-activity'), encoding='utf-8').decode("utf-8")
        self.assertEqual(norm_xml, self.act.raw_xml)

    def test_budget(self):
        self.assertEqual(1, len(self.act.budgets))

    def test_policy_markers(self):
        self.assertEqual(2, len(self.act.policy_markers))
        self.assertEqual(cl2.PolicyMarker.aid_to_environment, self.act.policy_markers[0].code)
        self.assertEqual(cl2.PolicyMarker.gender_equality, self.act.policy_markers[1].code)

    def test_policy_markers_significance(self):
        self.assertEqual(2, len(self.act.policy_markers))
        self.assertEqual(cl2.PolicySignificance.principal_objective_and_in_support_of_an_action_programme, self.act.policy_markers[0].significance)
        self.assertEqual(cl2.PolicySignificance.explicit_primary_objective, self.act.policy_markers[1].significance)

    def test_related_activity(self):
        self.assertEqual(1, len(self.act.related_activities))
        self.assertEqual("AA-AAA-123456789-6789", self.act.related_activities[0].ref)

    def test_activity_status(self):
        self.assertEqual(cl2.ActivityStatus.implementation, self.act.activity_status)

    def test_collaboration_type(self):
        self.assertEqual(cl2.CollaborationType.bilateral, self.act.collaboration_type)

    def test_default_finance_type(self):
        self.assertEqual(cl2.FinanceType.standard_grant,
                          self.act.default_finance_type)

    def test_default_flow_type(self):
        self.assertEqual(cl2.FlowType.oda, self.act.default_flow_type)

    def test_default_aid_type(self):
        self.assertEqual(cl2.AidType.general_budget_support,
                          self.act.default_aid_type)

    def test_default_tied_status(self):
        self.assertEqual(cl2.TiedStatus.partially_tied, self.act.default_tied_status)

    def test_default_hierarchy(self):
        self.assertEqual(1, self.act.hierarchy)

    def test_default_language(self):
        self.assertEqual(cl2.Language.english, self.act.default_language)


class TestParseActivity(AppTestCase):
    def setUp(self):
        super().setUp()
        self.act = parse.activity(parse_fixture("default_currency.xml"))

    def test_bad_xml(self):
        with self.assertRaises(ET.LxmlError):
            parse.activity(parse_fixture("broken.xml"))

    def test_id(self):
        self.assertEqual(
            u"47045-ARM-202-G05-H-00",
            self.act.iati_identifier)

    def test_title(self):
        self.assertEqual(
            (u"Support to the National Program on the Response to HIV " +
             u"Epicemic in the Republic of Armenia"),
            self.act.title)

    def test_last_updated_time(self):
        self.assertEqual(datetime.date(2012, 9, 25), self.act.last_updated_datetime)

    def test_description(self):
        self.assertTrue(self.act.description.startswith(
            u"While Armenia is still a country with a concentrated HIV"))

    def test_reporting_org_ref(self):
        self.assertEqual(u"47045", self.act.reporting_org.ref)

    def test_reporting_org_type(self):
        self.assertEqual(
            cl.OrganisationType.multilateral,
            self.act.reporting_org.type
        )

    def test_activity_websites(self):
        self.assertEqual(
            [u"http://portfolio.theglobalfund.org/en/Grant/Index/ARM-202-G05-H-00"],
            self.act.websites)

    def test_default_currency(self):
        self.assertEqual(
            cl.Currency.us_dollar,
            self.act.default_currency
        )

    def test_participating_org(self):
        self.assertEqual(
            cl.OrganisationRole.funding,
            self.act.participating_orgs[0].role)

    def test_accepts_participatng_org_without_ref(self):
        self.assertEqual(2, len(self.act.participating_orgs))

    def test_recipient_country_percentages(self):
        self.assertEqual(1, len(self.act.recipient_country_percentages))
        self.assertEqual(
            cl.Country.armenia,
            self.act.recipient_country_percentages[0].country)
        self.assertEqual(
            "Armenia", self.act.recipient_country_percentages[0].name)
        self.assertEqual(
            None,
            self.act.recipient_country_percentages[0].percentage)

    def test_recipient_region_percentages(self):
        act = parse.activity(parse_fixture("iati_activity_JP.xml"))
        self.assertEqual(1, len(act.recipient_region_percentages))
        self.assertEqual(
            cl.Country.japan,
            act.recipient_country_percentages[0].country)
        self.assertEqual(
            "Far East Asia, regional", act.recipient_region_percentages[0].name)
        self.assertEqual(
            100,
            act.recipient_region_percentages[0].percentage)

    def test_transaction_count(self):
        self.assertEqual(1, len(self.act.transactions))

    def test_transaction_type(self):
        self.assertEqual(
            cl.TransactionType.commitment,
            self.act.transactions[0].type)

    def test_transaction_date(self):
        self.assertEqual(
            datetime.date(2009, 10, 1),
            self.act.transactions[0].date)

    def test_transaction_value_date(self):
        self.assertEqual(
            datetime.date(2009, 10, 1),
            self.act.transactions[0].value_date)

    def test_transaction_value_amount(self):
        self.assertEqual(
            3991675,
            self.act.transactions[0].value_amount)

    def test_transaction_currency(self):
        # currency is picked up from default currency
        act = parse.activity(parse_fixture("transaction_provider.xml"))
        self.assertEqual(
            cl.Currency.pound_sterling,
            act.transactions[0].value_currency)

    def test_transaction_value_composite(self):
        act = parse.activity(parse_fixture("transaction_provider.xml"))
        self.assertEqual(
            (datetime.date(2011, 8, 19), 29143, cl.Currency.pound_sterling),
            act.transactions[0].value)

    def test_transaction_ref(self):
        act = parse.activity(parse_fixture("transaction_ref.xml"))
        self.assertEqual(u'36258', act.transactions[0].ref)
        self.assertEqual(None, act.transactions[1].ref)

    def test_transaction_provider_org_ref(self):
        act = parse.activity(parse_fixture("transaction_provider.xml"))
        self.assertEqual(u'GB-1-201242-101',
                          act.transactions[0].provider_org.ref)

    def test_transaction_reciever_org_ref(self):
        act = parse.activity(parse_fixture("transaction_provider.xml"))
        self.assertEqual(u'GB-CHC-313139',
                          act.transactions[0].receiver_org.ref)

    def test_date_start_planned(self):
        self.assertEqual(datetime.date(2009, 10, 3), self.act.start_planned)

    def test_date_start_actual(self):
        self.assertEqual(datetime.date(2009, 10, 1), self.act.start_actual)

    def test_date_end_planned(self):
        self.assertEqual(datetime.date(2009, 10, 4), self.act.end_planned)

    def test_date_end_actual(self):
        self.assertEqual(datetime.date(2009, 10, 2), self.act.end_actual)

    def test_sector_percentage_count(self):
        act = next(parse.document_from_file(
            fixture_filename("complex_example_dfid.xml")))
        self.assertEqual(5, len(act.sector_percentages))

    def test_raw_xml(self):
        norm_xml = ET.tostring(ET.parse(fixture_filename("default_currency.xml"))).decode("utf-8")
        self.assertEqual(norm_xml, self.act.raw_xml)

    def test_no_start_actual(self):
        activities = parse.document_from_file(fixture_filename("missing_dates.xml"))
        act = {a.iati_identifier: a for a in activities}
        self.assertEqual(None, act[u"GB-CHC-272465-680"].start_actual)

    def test_budget(self):
        self.assertEqual(6, len(self.act.budgets))

    def test_policy_markers(self):
        activities = [a for a in parse.document_from_file(fixture_filename("CD.xml"))]

        self.assertEqual(8, len(activities[1].policy_markers))
        self.assertEqual(cl.PolicyMarker.gender_equality, activities[1].policy_markers[0].code)
        self.assertEqual(cl.PolicyMarker.aid_to_environment, activities[1].policy_markers[1].code)
        self.assertEqual(
            cl.PolicyMarker.participatory_developmentgood_governance,
            activities[1].policy_markers[2].code)
        self.assertEqual(cl.PolicyMarker.trade_development, activities[1].policy_markers[3].code)

    def test_policy_markers_significance(self):
        activities = [a for a in parse.document_from_file(fixture_filename("CD.xml"))]

        self.assertEqual(8, len(activities[1].policy_markers))
        self.assertEqual(cl.PolicySignificance.significant_objective, activities[1].policy_markers[0].significance)
        self.assertEqual(cl.PolicySignificance.not_targeted, activities[1].policy_markers[1].significance)
        self.assertEqual(
            cl.PolicySignificance.significant_objective,
            activities[1].policy_markers[2].significance)
        self.assertEqual(cl.PolicySignificance.not_targeted, activities[1].policy_markers[3].significance)

    def test_related_activity(self):
        activities = [a for a in parse.document_from_file(fixture_filename("CD.xml"))]
        self.assertEqual(4, len(activities[0].related_activities))
        self.assertEqual("GB-1-105838-101", activities[0].related_activities[0].ref)

    def test_activity_status(self):
        activities = [a for a in parse.document_from_file(fixture_filename("default_currency.xml"))]
        self.assertEqual(cl.ActivityStatus.implementation, activities[0].activity_status)

    def test_collaboration_type(self):
        activities = [a for a in parse.document_from_file(fixture_filename("CD.xml"))]
        self.assertEqual(cl.CollaborationType.bilateral, activities[1].collaboration_type)

    def test_default_finance_type(self):
        activities = [a for a in parse.document_from_file(fixture_filename("CD.xml"))]
        self.assertEqual(
            cl.FinanceType.standard_grant,
            activities[1].default_finance_type)

    def test_default_flow_type(self):
        activities = [a for a in parse.document_from_file(fixture_filename("CD.xml"))]
        self.assertEqual(cl.FlowType.oda, activities[1].default_flow_type)

    def test_default_aid_type(self):
        activities = [a for a in parse.document_from_file(fixture_filename("CD.xml"))]
        self.assertEqual(
            cl.AidType.projecttype_interventions,
            activities[1].default_aid_type)

    def test_default_tied_status(self):
        activities = [a for a in parse.document_from_file(fixture_filename("CD.xml"))]
        self.assertEqual(cl.TiedStatus.untied, activities[1].default_tied_status)

    def test_default_hierarchy(self):
        activities = [a for a in parse.document_from_file(fixture_filename("default_currency.xml"))]
        self.assertEqual(1, activities[0].hierarchy)

    def test_default_language(self):
        activities = [a for a in parse.document_from_file(fixture_filename("default_currency.xml"))]
        self.assertEqual(cl.Language.english, activities[0].default_language)

    def test_default_language_none(self):
        default_language = parse.default_language(
            ET.XML('<iati-activity xml:lang="en" default-currency="GBP" hierarchy="1"/>'))
        self.assertEqual(cl.Language.english, default_language)
        no_default_language = parse.default_language(
            ET.XML('<iati-activity default-currency="GBP" hierarchy="1"/>'))
        self.assertEqual(None, no_default_language)


class TestFunctional(AppTestCase):
    def test_save_parsed_activity(self):
        act = parse.activity(parse_fixture("default_currency.xml"))
        db.session.add(act)
        db.session.commit()

    def test_save_parsed_201(self):
        activities = parse.document_from_file(fixture_filename("2.01-example-annotated.xml"))
        db.session.add_all(activities)
        db.session.commit()

    def test_save_complex_example(self):
        acts = parse.document_from_file(
            fixture_filename("complex_example_dfid.xml"))
        db.session.add_all(acts)
        db.session.commit()

    def test_save_repeated_participation(self):
        activities = parse.document_from_file(fixture_filename("repeated_participation.xml"))
        db.session.add_all(activities)
        db.session.commit()

    def test_different_roles(self):
        activities = parse.document_from_file(fixture_filename("same_orgs_different_roles.xml"))
        db.session.add_all(activities)
        db.session.commit()

    def test_big_values(self):
        activities = parse.document_from_file(fixture_filename("big_value.xml"))
        db.session.add_all(activities)
        db.session.commit()

    def test_decimal_percentages(self):
        act = parse.activity(ET.XML(
            u'''<iati-activity>
                    <iati-identifier>AAA-BBB</iati-identifier>
                    <reporting-org ref="AAA"/>
                    <recipient-country code="AF" percentage="24.5" />
                    <recipient-country code="AG" percentage="25.5" />
                    <recipient-region code="798" percentage="26.5" />
                    <recipient-region code="889" percentage="23.5" />
                    <sector code="11130" percentage="49.5" />
                    <sector code="11182" percentage="50.5" />
                </iati-activity>'''
        ))
        db.session.add(act)
        db.session.commit()

        self.assertEqual(
            24.5,
            db.session.query(model.CountryPercentage).filter(model.CountryPercentage.country==cl.Country.afghanistan).first().percentage
        )
        self.assertEqual(
            25.5,
            db.session.query(model.CountryPercentage).filter(model.CountryPercentage.country==cl.Country.antigua_and_barbuda).first().percentage
        )

        self.assertEqual(
            26.5,
            db.session.query(model.RegionPercentage).filter(model.RegionPercentage.region==cl.Region.asia_regional).first().percentage
        )
        self.assertEqual(
            23.5,
            db.session.query(model.RegionPercentage).filter(model.RegionPercentage.region==cl.Region.oceania_regional).first().percentage
        )

        self.assertEqual(
            49.5,
            db.session.query(model.SectorPercentage).filter(model.SectorPercentage.sector==cl.Sector.teacher_training).first().percentage
        )
        self.assertEqual(
            50.5,
            db.session.query(model.SectorPercentage).filter(model.SectorPercentage.sector==cl.Sector.educational_research).first().percentage
        )

    def test_version_stored_1(self):
        act = parse.activity(ET.XML(
            u'''<iati-activity>
                    <iati-identifier>AAA-BBB</iati-identifier>
                    <reporting-org ref="AAA"/>
                </iati-activity>'''
            ), major_version='1', version='1.05')
        db.session.add(act)
        db.session.commit()

        self.assertEqual(
            '1',
            db.session.query(model.Activity).first().major_version
        )
        self.assertEqual(
            '1.05',
            db.session.query(model.Activity).first().version
        )

    def test_version_stored_2(self):
        act = parse.activity(ET.XML(
            u'''<iati-activity>
                    <iati-identifier>AAA-BBB</iati-identifier>
                    <reporting-org ref="AAA"/>
                </iati-activity>'''
            ), major_version='2', version='2.01')
        db.session.add(act)
        db.session.commit()

        self.assertEqual(
            '2',
            db.session.query(model.Activity).first().major_version
        )
        self.assertEqual(
            '2.01',
            db.session.query(model.Activity).first().version
        )


class TestSector(AppTestCase):
    def test_code(self):
        sec = parse.sector_percentages(ET.XML(
            u'<wrapper><sector vocabulary="DAC" code="16010">Child Protection Systems Strengthening</sector></wrapper>'
        ))[0]
        self.assertEqual(cl.Sector.social_protection, sec.sector)
        self.assertEqual(u"Child Protection Systems Strengthening", sec.text)

    def test_missing_code(self):
        sec = parse.sector_percentages(ET.XML(
            u'<wrapper><sector vocabulary="DAC">Child Protection Systems Strengthening</sector></wrapper>'
        ))[0]
        self.assertEqual(None, sec.sector)

    def test_missing_everything(self):
        sec = parse.sector_percentages(ET.XML(
            u'<wrapper><sector /></wrapper>'
        ))
        self.assertEqual([], sec)


class TestPercentages(AppTestCase):
    def test_recipient_country_percentages(self):
        recipient_country_percentages = parse.recipient_country_percentages(ET.XML(
            u'<wrapper><recipient-country code="BD" percentage="3"></recipient-country></wrapper>'
        ))
        self.assertEqual(3, recipient_country_percentages[0].percentage)

    def test_recipient_region_percentages(self):
        recipient_region_percentages = parse.recipient_region_percentages(ET.XML(
            u"""<wrapper>
                    <recipient-region code="998" percentage="4"></recipient-region>
                    <recipient-region code="998"></recipient-region>
                </wrapper>"""
        ))
        self.assertEqual(4, recipient_region_percentages[0].percentage)
        self.assertEqual(None, recipient_region_percentages[1].percentage)


class TestOrganisation(AppTestCase):
    def test_org_role_looseness(self):
        # organisationrole should be "Implementing" but can be "implementing"
        orgrole = parse.participating_orgs(ET.XML(
            u'<wrap><participating-org role="implementing" ref="test" /></wrap>'
        ))[0]
        self.assertEqual(orgrole.role, cl.OrganisationRole.implementing)

    def test_org_type(self):
        orgtype = parse.reporting_org(ET.XML(
            u"""<wrap><reporting-org ref="GB-CHC-202918" type="21" /></wrap>"""
        ))
        self.assertEqual(cl.OrganisationType.international_ngo, orgtype.type)

    def test_org_type_missing(self):
        orgtype = parse.reporting_org(ET.XML(
            u"""<wrap><reporting-org ref="GB-CHC-202918" /></wrap>"""
        ))
        self.assertEqual(None, orgtype.type)


class TestParticipation(AppTestCase):
    def test_repeated_participation(self):
        # Identical participations should be filtered
        participations = parse.participating_orgs(
            ET.XML(u"""
                <wrap>
                <participating-org ref="GB-CHC-272465" role="implementing" type="21">Concern Universal</participating-org>
            <participating-org ref="GB-CHC-272465" role="implementing" type="21">Concern Universal</participating-org>
                </wrap>
                """),
        )
        self.assertEqual(1, len(participations))

    def test_same_org_different_role(self):
        participations = parse.participating_orgs(
            ET.XML(u"""<wrap>
            <participating-org ref="GB-CHC-272465" role="implementing" type="21">Concern Universal</participating-org>
            <participating-org ref="GB-CHC-272465" role="Funding" type="21">Concern Universal</participating-org>
            </wrap>
            """)
        )
        self.assertEqual(2, len(participations))


class TestActivity(AppTestCase):
    def test_missing_id(self):
        # missing activity id means don't parse
        activities = parse.document_from_bytes(
            b'''
              <iati-activities>
                <iati-activity default-currency="GBP" xml:lang="en">
                    <reporting-org ref="GB-2" type="15">CDC Group plc</reporting-org>
                    <activity-status code="2">Implementation</activity-status>
                </iati-activity>
              </iati-activities>
                ''')
        self.assertEqual(0, len(list(activities)))

    def test_dates(self):
        activities = list(parse.document_from_file(fixture_filename("CD.xml")))
        self.assertEqual(datetime.date(2004, 1, 1), activities[0].start_planned)
        self.assertEqual(datetime.date(2004, 1, 1), activities[0].start_actual)
        self.assertEqual(datetime.date(2010, 12, 31), activities[0].end_planned)
        self.assertEqual(datetime.date(2010, 12, 31), activities[0].end_actual)

    def test_missing_reporting_org(self):
        # missing reporting org should still parse
        activities = list(parse.document_from_bytes(
            b'''
              <iati-activities>
                <iati-activity default-currency="GBP" xml:lang="en">
                    <iati-identifier>AAA-AA</iati-identifier>
                    <activity-status code="2">Implementation</activity-status>
                </iati-activity>
              </iati-activities>
                '''))
        self.assertEqual(1, len(activities))
        self.assertEqual(u"AAA-AA", activities[0].iati_identifier)


class TestTransaction(AppTestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.codelists = """
            <activity><transaction>
              <transaction-type code="C"/>
              <value value-date="2012-12-31">4119000</value>
              <transaction-date iso-date="2012-12-31"/>
              <flow-type code="30"/>
              <finance-type code="110"/>
              <aid-type code="B01"/>
              <disbursement-channel code="2"/>
              <tied-status code="5"/>
            </transaction></activity>
        """

    def test_missing_code(self):
        transactions = parse.transactions(
            ET.XML(u'''<activity><transaction>
                <transaction-date iso-date="31/12/2011" />
                <description>test</description>
                <value value-date="31/12/2011">116,017</value>
                <transaction-type>Disbursement</transaction-type>
                </transaction></activity>''')
        )
        self.assertEqual(1, len(transactions))

    def test_big_value(self):
        transaction = parse.transactions(
            ET.XML(u'''<activity><transaction>
                <transaction-date iso-date="31/12/2011" />
                <description>test</description>
                <value value-date="31/12/2011">2663000000</value>
                <transaction-type code="D">Disbursement</transaction-type>
                </transaction></activity>''')
        )[0]
        self.assertEqual(2663000000, transaction.value_amount)

    @mock.patch('iatilib.parse.iati_decimal')
    def test_iati_int_called(self, mock):
        parse.transactions(
            ET.XML(u'''<activity><transaction>
                <transaction-date iso-date="31/12/2011" />
                <description>test</description>
                <value value-date="31/12/2011">-1000</value>
                <transaction-type code="D">Disbursement</transaction-type>
                </transaction></activity>''')
        )[0]
        self.assertEqual(1, mock.call_count)

    def test_provider_activity_id(self):
        sample = """<activity><transaction>
          <transaction-type code="IF"/>
          <provider-org ref="GB-1" provider-activity-id="GB-1-202907">
            DFID
          </provider-org>
          <value value-date="2012-07-02" currency="GBP">51693</value>
          <transaction-date iso-date="2012-07-02"/>
        </transaction></activity>
        """
        transaction = parse.transactions(ET.XML(sample))[0]
        self.assertEqual(u'GB-1-202907', transaction.provider_org_activity_id)

    def test_provider_org_text(self):
        sample = """<activity><transaction>
          <transaction-type code="IF"/>
          <provider-org>DFID</provider-org>
          <value value-date="2012-07-02" currency="GBP">51693</value>
          <transaction-date iso-date="2012-07-02"/>
        </transaction></activity>
        """
        transaction = parse.transactions(ET.XML(sample))[0]
        self.assertEqual(u'DFID', transaction.provider_org_text)

    def test_receiver_activity_id(self):
        sample = """<activity><transaction>
          <transaction-type code="IF"/>
          <receiver-org ref="GB-CHC-1068839" receiver-activity-id="GB-CHC-1068839-dfid_ag_11-13">Bond</receiver-org>
          <value value-date="2011-06-01" currency="GBP">271111</value>
          <transaction-date iso-date="2012-03-31"/>
          </transaction></activity>
        """
        transaction = parse.transactions(ET.XML(sample))[0]
        self.assertEqual(u'GB-CHC-1068839-dfid_ag_11-13', transaction.receiver_org_activity_id)

    def test_receiver_org_text(self):
        sample = """<activity><transaction>
          <transaction-type code="IF"/>
          <receiver-org ref="GB-CHC-1068839" receiver-activity-id="GB-CHC-1068839-dfid_ag_11-13">Bond</receiver-org>
          <value value-date="2012-07-02" currency="GBP">51693</value>
          <transaction-date iso-date="2012-07-02"/>
        </transaction></activity>
        """
        transaction = parse.transactions(ET.XML(sample))[0]
        self.assertEqual(u'Bond', transaction.receiver_org_text)

    def test_description(self):
        sample = """<activity><transaction>
          <transaction-type code="IF"/>
          <value value-date="2011-08-19" currency="GBP">29143</value>
          <description>Funds received from DFID for activities in Aug- Sept 2011</description>
          <transaction-date iso-date="2011-08-19"/>
        </transaction></activity>"""
        transaction = parse.transactions(ET.XML(sample))[0]
        self.assertEqual(
                u'Funds received from DFID for activities in Aug- Sept 2011',
                transaction.description
        )

    def test_flow_type(self):
        transaction = parse.transactions(ET.XML(self.codelists))[0]
        self.assertEqual(u'30', transaction.flow_type.value)

    def test_finance_type(self):
        transaction = parse.transactions(ET.XML(self.codelists))[0]
        self.assertEqual(u'110', transaction.finance_type.value)

    def test_aid_type(self):
        transaction = parse.transactions(ET.XML(self.codelists))[0]
        self.assertEqual(u'B01', transaction.aid_type.value)

    def test_tied_status(self):
        transaction = parse.transactions(ET.XML(self.codelists))[0]
        self.assertEqual(u'5', transaction.tied_status.value)

    def test_disbursement_channel(self):
        transaction = parse.transactions(ET.XML(self.codelists))[0]
        self.assertEqual(u'2', transaction.disbursement_channel.value)


class TestBudget(TestCase):
    def parse_budget(self):
        return parse.budgets(ET.XML("""
            <wrapper>
            <budget type="1">
                <period-end iso-date="2010-03-31" />
                <value currency="USD">1840852</value>
            </budget>
            </wrapper>
        """))[0]

    def test_budget_type(self):
        budget = self.parse_budget()
        self.assertEqual(budget.type, cl.BudgetType.original)

    def test_budget_type_looser(self):
        budget = parse.budgets(ET.XML("""
            <wrapper>
            <budget type="Original">
                <period-end iso-date="2010-03-31" />
                <value currency="USD">1840852</value>
            </budget>
            </wrapper>
        """))[0]
        self.assertEqual(budget.type, cl.BudgetType.original)

    def test_budget_period_end(self):
        budget = self.parse_budget()
        self.assertEqual(budget.period_end, datetime.date(2010, 3, 31))

    def test_budget_period_start(self):
        budget = self.parse_budget()
        self.assertEqual(budget.period_start, None)

    def test_value_currency(self):
        budget = self.parse_budget()
        self.assertEqual(budget.value_currency, cl.Currency.us_dollar)

    def test_value_amount(self):
        budget = self.parse_budget()
        self.assertEqual(budget.value_amount, 1840852)


class TestDates(TestCase):
    def test_correct_date(self):
        self.assertEqual(
            datetime.date(2010, 1, 2),
            parse.iati_date("2010-01-02"))

    def test_variation_1(self):
        self.assertEqual(
            datetime.date(2011, 12, 31),
            parse.iati_date("31/12/2011"))

    def test_iso_date_with_z(self):
        self.assertEqual(
            datetime.date(2010, 1, 2),
            parse.iati_date("2010-01-02Z"))

    def test_iso_date_with_timezone(self):
        self.assertEqual(
            datetime.date(2010, 1, 2),
            parse.iati_date("2010-01-02+06:00"))
        self.assertEqual(
            datetime.date(2010, 1, 2),
            parse.iati_date("2010-01-02-06:00"))


class TestValue(TestCase):
    def test_thousand_sep(self):
        self.assertEqual(20026, parse.iati_int(u"20,026"))

    def test_sign(self):
        self.assertEqual(-20026, parse.iati_int(u"-20026"))

    def test_decimal_thousand_sep(self):
        self.assertEqual(Decimal('20026'), parse.iati_decimal(u"20,026"))

    def test_decimal_sign(self):
        self.assertEqual(Decimal('-20026'), parse.iati_decimal(u"-20026"))

    def test_decimal(self):
        self.assertEqual(Decimal('42479.4'), parse.iati_decimal(u"42479.4"))


class TestXVal(TestCase):
    def test_missing_val(self):
        with self.assertRaises(parse.MissingValue):
            parse.xval(ET.XML(u"<foo />"), "bar")

    def test_default_val(self):
        self.assertEqual(
            None,
            parse.xval(ET.XML(u"<foo />"), "bar", None))
