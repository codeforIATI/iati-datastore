import datetime

from . import AppTestCase, factories as fac

from iatilib import codelists as cl
from iatilib.frontend import dsfilter


class TestActivityFilter(AppTestCase):
    def test_by_iati_identifier(self):
        act_in = fac.ActivityFactory.create(iati_identifier='AAA')
        act_not = fac.ActivityFactory.create(iati_identifier='ZZZ')
        activities = dsfilter.activities({
            "iati-identifier": u"AAA"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_activity_status(self):
        act_in = fac.ActivityFactory.create(activity_status='2')
        act_not = fac.ActivityFactory.create(activity_status='BOO')
        activities = dsfilter.activities({
            "activity-status": u"2"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_title(self):
        act_in = fac.ActivityFactory.create(title='Technical Assistance to Support Improved Aid Effectiveness in Bangladesh')
        act_not = fac.ActivityFactory.create(title='Accelerating Improved Nutrition for Extreme Poor in Bangladesh')
        activities = dsfilter.activities({
            "title": u"technical assistance"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_description(self):
        act_in = fac.ActivityFactory.create(description='To improve dialogue and coordination at national, sectoral and programme levels, with greater aid predictability and increased alignment of Government-donor policies and systems')
        act_not = fac.ActivityFactory.create(description='To reduce undernutrition in extreme poor household in Bangladesh. Improved nutrient intake and health status of adolescent girls, pregnant and breastfeeding women and young children.')
        activities = dsfilter.activities({
            "description": u"improve dialogue"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_country_code(self):
        act_in = fac.ActivityFactory.create(
            recipient_country_percentages=[
                fac.CountryPercentageFactory.build(
                    country=cl.Country.libya),
            ])
        act_not = fac.ActivityFactory.create(
            recipient_country_percentages=[
                fac.CountryPercentageFactory.build(
                    country=cl.Country.zambia),
            ])
        activities = dsfilter.activities({
            "recipient-country": cl.Country.from_string(u"LY")
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_transaction_country_code(self):
        act_in = fac.ActivityFactory.create()
        act_not = fac.ActivityFactory.create()
        fac.TransactionFactory.create(
            activity=act_in,
            ref="12345",
            recipient_country_percentages=[
                fac.CountryPercentageFactory.build(
                    country=cl.Country.libya),
            ])
        fac.TransactionFactory.create(
            activity=act_not,
            ref="12345",
            recipient_country_percentages=[
                fac.CountryPercentageFactory.build(
                    country=cl.Country.zambia),
            ])
        activities = dsfilter.activities({
            "recipient-country": cl.Country.from_string(u"LY")
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_country_name(self):
        act_not = fac.ActivityFactory.create(
            recipient_country_percentages=[
                fac.CountryPercentageFactory.build(
                    name="Libya",
                    country=cl.Country.libya),
            ])
        act_in = fac.ActivityFactory.create(
            recipient_country_percentages=[
                fac.CountryPercentageFactory.build(
                    name="Zambia",
                    country=cl.Country.zambia
                    )
            ])
        activities = dsfilter.activities({
            "recipient-country.text": u"Zambia"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_transaction_country_name(self):
        act_in = fac.ActivityFactory.create()
        act_not = fac.ActivityFactory.create()
        fac.TransactionFactory.create(
            activity=act_in,
            ref="12345",
            recipient_country_percentages=[
                fac.CountryPercentageFactory.build(
                    name="Libya",
                    country=cl.Country.libya),
            ])
        fac.TransactionFactory.create(
            activity=act_not,
            ref="12345",
            recipient_country_percentages=[
                fac.CountryPercentageFactory.build(
                    name="Zambia",
                    country=cl.Country.zambia),
            ])
        activities = dsfilter.activities({
            "recipient-country.text": u"Libya"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_reporting_org_ref(self):
        act_in = fac.ActivityFactory.create(
            reporting_org=fac.OrganisationFactory.build(
                ref=u"AAA"
            ))
        act_not = fac.ActivityFactory.create(
            reporting_org=fac.OrganisationFactory.build(
                ref=u"ZZZ"
            ))
        activities = dsfilter.activities({
            "reporting-org": u"AAA"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_reporting_org_text(self):
        act_in = fac.ActivityFactory.create(
            reporting_org=fac.OrganisationFactory.build(
                ref=u"AAA",
                name=u"aaa"
            ))
        act_not = fac.ActivityFactory.create(
            reporting_org=fac.OrganisationFactory.build(
                ref=u"ZZZ",
                name=u"zzz"
            ))
        activities = dsfilter.activities({
            "reporting-org.text": u"aaa"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_reporting_org_type(self):
        act_in = fac.ActivityFactory.create(
            reporting_org=fac.OrganisationFactory.build(
                type=cl.OrganisationType.government
            ))
        act_not = fac.ActivityFactory.create(
            reporting_org=fac.OrganisationFactory.build(
                type=cl.OrganisationType.foundation
            ))
        activities = dsfilter.activities({
            "reporting-org.type": cl.OrganisationType.from_string(u"10")
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_recipient_region_code(self):
        act_in = fac.ActivityFactory.create(
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                    region=cl.Region.africa_regional),
            ])
        act_not = fac.ActivityFactory.create(
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                    region=cl.Region.oceania_regional
                ),
            ])
        activities = dsfilter.activities({
            "recipient-region": cl.Region.from_string(u"298")
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_transaction_recipient_region_code(self):
        act_in = fac.ActivityFactory.create()
        act_not = fac.ActivityFactory.create()
        fac.TransactionFactory.create(
            activity=act_in,
            ref="12345",
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                    region=cl.Region.africa_regional,
                ),
            ])
        fac.TransactionFactory.create(
            activity=act_not,
            ref="12345",
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                    region=cl.Region.oceania_regional,
                ),
            ])
        activities = dsfilter.activities({
            "recipient-region": cl.Region.from_string(u"298")
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_recipient_region_name(self):
        act_in = fac.ActivityFactory.create(
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                    region=cl.Region.africa_regional,
                    name="Africa"
                )
            ])
        act_not = fac.ActivityFactory.create(
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                    region=cl.Region.oceania_regional,
                    name="Oceania"
                ),
            ])
        activities = dsfilter.activities({
            "recipient-region.text": u"Africa"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_transaction_recipient_region_name(self):
        act_in = fac.ActivityFactory.create()
        act_not = fac.ActivityFactory.create()
        fac.TransactionFactory.create(
            activity=act_in,
            ref="12345",
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                    region=cl.Region.africa_regional,
                    name="Africa"
                ),
            ])
        fac.TransactionFactory.create(
            activity=act_not,
            ref="12345",
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                    region=cl.Region.oceania_regional,
                    name="Oceania"
                ),
            ])
        activities = dsfilter.activities({
            "recipient-region.text": u"Africa"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_recipient_region_code_not_in_list(self):
        # https://github.com/IATI/iati-datastore/issues/184
        act_not = fac.ActivityFactory.create(
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                    region=cl.Region.oceania_regional
                ),
            ])
        activities = dsfilter.activities({
            "recipient-region": cl.Region.from_string(u"xxx")
        })
        self.assertEqual([], activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_or_filter(self):
        act_a = fac.ActivityFactory.create(
            reporting_org=fac.OrganisationFactory.build(
                ref=u"AAA"
            ))
        act_b = fac.ActivityFactory.create(
            reporting_org=fac.OrganisationFactory.build(
                ref=u"BBB"
            ))
        act_not = fac.ActivityFactory.create(
            reporting_org=fac.OrganisationFactory.build(
                ref=u"ZZZ"
            ))
        activities = dsfilter.activities({
            "reporting-org": u"AAA|BBB"
        })
        self.assertIn(act_a, activities.all())
        self.assertIn(act_b, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_recipient_region_text(self):
        act_in = fac.ActivityFactory.create(
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                    name="Africa",
                    region=cl.Region.africa_regional),
            ])
        act_not = fac.ActivityFactory.create(
            recipient_region_percentages=[
                fac.RegionPercentageFactory.build(
                    name="Oceania, regional",
                    region=cl.Region.oceania_regional
                ),
            ])
        activities = dsfilter.activities({
            "recipient-region.text": u"Africa"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_sector(self):
        act_in = fac.ActivityFactory.create(
            sector_percentages=[
                fac.SectorPercentageFactory.build(
                    sector=cl.Sector.primary_education),
            ])
        act_not = fac.ActivityFactory.create(
            sector_percentages=[
                fac.SectorPercentageFactory.build(
                    sector=cl.Sector.secondary_education
                ),
            ])
        activities = dsfilter.activities({
            "sector": cl.Sector.from_string(u"11220")
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_transaction_sector(self):
        act_in = fac.ActivityFactory.create()
        act_not = fac.ActivityFactory.create()
        fac.TransactionFactory.create(
            activity=act_in,
            ref="12345",
            sector_percentages=[
                fac.SectorPercentageFactory.build(
                    sector=cl.Sector.primary_education),
            ])
        fac.TransactionFactory.create(
            activity=act_not,
            ref="12345",
            sector_percentages=[
                fac.SectorPercentageFactory.build(
                    sector=cl.Sector.secondary_education),
            ])
        activities = dsfilter.activities({
            "sector": cl.Sector.from_string(u"11220")
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_sector_name(self):
        act_in = fac.ActivityFactory.create(
            sector_percentages=[
                fac.SectorPercentageFactory.build(
                    text="Primary",
                    sector=cl.Sector.primary_education),
            ])
        act_not = fac.ActivityFactory.create(
            sector_percentages=[
                fac.SectorPercentageFactory.build(
                    text="Secondary",
                    sector=cl.Sector.secondary_education
                ),
            ])
        activities = dsfilter.activities({
            "sector.text": u"Primary"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_by_transaction_sector_name(self):
        act_in = fac.ActivityFactory.create()
        act_not = fac.ActivityFactory.create()
        fac.TransactionFactory.create(
            activity=act_in,
            ref="12345",
            sector_percentages=[
                fac.SectorPercentageFactory.build(
                    text="Primary",
                    sector=cl.Sector.primary_education),
            ])
        fac.TransactionFactory.create(
            activity=act_not,
            ref="12345",
            sector_percentages=[
                fac.SectorPercentageFactory.build(
                    text="Secondary",
                    sector=cl.Sector.secondary_education),
            ])
        activities = dsfilter.activities({
            "sector.text": u"Primary"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_transaction_ref(self):
        trans_in = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(),
            ref="12345"
        )
        trans_not = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(),
            ref="0123"
        )
        activity = dsfilter.activities({
            "transaction.ref": u"12345"
        })

        self.assertIn(trans_in.activity, activity.all())
        self.assertNotIn(trans_not.activity, activity.all())

    def test_provider_org(self):
        org_in = fac.OrganisationFactory.build(
            ref="GB-1",
            name="an org",
        )
        org_out = fac.OrganisationFactory.build(
            ref="GB-2",
            name="another org",
        )
        trans_in = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(),
            provider_org=org_in,
            provider_org_activity_id=u"GB-1-AAA",
        )
        trans_not = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(),
            provider_org=org_out,
            provider_org_activity_id=u"GB-2-ZZZ",
        )
        activity = dsfilter.activities({
            "transaction_provider-org": u"GB-1"
        })

        self.assertIn(trans_in.activity, activity.all())
        self.assertNotIn(trans_not.activity, activity.all())

        text = dsfilter.activities({
            "transaction_provider-org.text": u"an org"
        })
        self.assertIn(trans_in.activity, text.all())
        self.assertNotIn(trans_not.activity, text.all())

        provider_activity_id = dsfilter.activities({
            "transaction_provider-org.provider-activity-id": u"GB-1-AAA"
        })
        self.assertIn(trans_in.activity, provider_activity_id.all())
        self.assertNotIn(trans_not.activity, provider_activity_id.all())

    def test_receiver_org(self):
        org_in = fac.OrganisationFactory.build(
            ref="GB-1",
            name="an org",
        )
        org_out = fac.OrganisationFactory.build(
            ref="GB-2",
            name="another org",
        )
        trans_in = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(),
            receiver_org=org_in,
            receiver_org_activity_id=u"GB-1-AAA",
        )
        trans_not = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(),
            receiver_org=org_out,
            receiver_org_activity_id=u"GB-2-ZZZ",
        )
        activity = dsfilter.activities({
            "transaction_receiver-org": u"GB-1"
        })

        self.assertIn(trans_in.activity, activity.all())
        self.assertNotIn(trans_not.activity, activity.all())

        text = dsfilter.activities({
            "transaction_receiver-org.text": u"an org"
        })
        self.assertIn(trans_in.activity, text.all())

        receiver_activity_id = dsfilter.activities({
            "transaction_receiver-org.receiver-activity-id": u"GB-1-AAA"
        })
        self.assertIn(trans_in.activity, receiver_activity_id.all())
        self.assertNotIn(trans_not.activity, receiver_activity_id.all())

    def test_policy_markers(self):
        act_in = fac.ActivityFactory.create(
                policy_markers=[fac.PolicyMarkerFactory.build()],
        )
        act_not = fac.ActivityFactory.create(
                policy_markers=[fac.PolicyMarkerFactory.build(
                    code=cl.PolicyMarker.trade_development)
                ],
        )
        activities = dsfilter.activities({
            "policy-marker": cl.PolicyMarker.from_string(u"1")
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_policy_markers_significance(self):
        act_in = fac.ActivityFactory.create(
                policy_markers=[fac.PolicyMarkerFactory.build()],
        )
        act_not = fac.ActivityFactory.create(
                policy_markers=[fac.PolicyMarkerFactory.build(
                    code=cl.PolicyMarker.trade_development,
                    significance=cl.PolicySignificance.not_targeted)
                ],
        )
        activities = dsfilter.activities({
            "policy-marker.significance": cl.PolicySignificance.from_string(u"4")
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_related_activities(self):
        act_in = fac.ActivityFactory.create(
                related_activities=[fac.RelatedActivityFactory.build(ref="ra-1")])
        act_not = fac.ActivityFactory.create(
                related_activities=[fac.RelatedActivityFactory.build(ref="ra-2")])
        activities = dsfilter.activities({
            "related-activity": u"ra-1"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_start_actual_greater_than(self):
        act_a = fac.ActivityFactory.create(start_actual=datetime.date(2013, 1, 1))
        act_b = fac.ActivityFactory.create(start_planned=datetime.date(2013, 2, 1))
        act_c = fac.ActivityFactory.create(start_actual=datetime.date(2013, 3, 1))
        act_not = fac.ActivityFactory.create(start_actual=datetime.date(2000, 1, 1))
        activities = dsfilter.activities({
            "start-date__gt": datetime.date(2012, 12, 31)
        })
        self.assertIn(act_a, activities.all())
        self.assertIn(act_b, activities.all())
        self.assertIn(act_c, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_end_actual_greater_than(self):
        act_a = fac.ActivityFactory.create(end_actual=datetime.date(2013, 1, 1))
        act_b = fac.ActivityFactory.create(end_planned=datetime.date(2013, 2, 1))
        act_c = fac.ActivityFactory.create(end_actual=datetime.date(2013, 3, 1))
        act_not = fac.ActivityFactory.create(end_actual=datetime.date(2000, 1, 1))
        activities = dsfilter.activities({
            "end-date__gt": datetime.date(2010, 1, 1)
        })
        self.assertIn(act_a, activities.all())
        self.assertIn(act_b, activities.all())
        self.assertIn(act_c, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_start_actual_lesser_than(self):
        act_in = fac.ActivityFactory.create(start_actual=datetime.date(2000, 1, 1))
        act_not = fac.ActivityFactory.create(start_actual=datetime.date(2013, 1, 1))
        activities = dsfilter.activities({
            "start-date__lt": datetime.date(2010, 1, 1)

        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_end_actual_lesser_than(self):
        act_in = fac.ActivityFactory.create(end_actual=datetime.date(2000, 1, 1))
        act_not = fac.ActivityFactory.create(end_actual=datetime.date(2013, 1, 1))
        activities = dsfilter.activities({
            "end-date__lt": datetime.date(2010, 1, 1)

        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_last_change_lesser_than(self):
        act_in = fac.ActivityFactory.create(last_change_datetime=datetime.date(2000, 1, 1))
        act_not = fac.ActivityFactory.create(last_change_datetime=datetime.date(2013, 1, 1))
        activities = dsfilter.activities({
            "last-change__lt": datetime.date(2010, 1, 1)

        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_last_change_actual_greater_than(self):
        act_in = fac.ActivityFactory.create(last_change_datetime=datetime.date(2013, 1, 1))
        act_not = fac.ActivityFactory.create(last_change_datetime=datetime.date(2000, 1, 1))
        activities = dsfilter.activities({
            "last-change__gt": datetime.date(2010, 1, 1)

        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_last_updated_lesser_than(self):
        act_in = fac.ActivityFactory.create(last_updated_datetime=datetime.date(2000, 1, 1))
        act_not = fac.ActivityFactory.create(last_updated_datetime=datetime.date(2013, 1, 1))
        activities = dsfilter.activities({
            "last-updated-datetime__lt": datetime.date(2010, 1, 1)

        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_last_updated_actual_greater_than(self):
        act_in = fac.ActivityFactory.create(last_updated_datetime=datetime.date(2013, 1, 1))
        act_not = fac.ActivityFactory.create(last_updated_datetime=datetime.date(2000, 1, 1))
        activities = dsfilter.activities({
            "last-updated-datetime__gt": datetime.date(2010, 1, 1)

        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_participating_org_role(self):
        act_in = fac.ActivityFactory.create(
                participating_orgs=[
                    fac.ParticipationFactory.build(
                        organisation__ref=u"AAA",
                        role=cl.OrganisationRole.implementing)
                ])
        act_not = fac.ActivityFactory.create(
                participating_orgs=[
                    fac.ParticipationFactory.build(
                        organisation__ref=u"BBB",
                        role=cl.OrganisationRole.funding)
                ])
        activities = dsfilter.activities({
            "participating-org.role": cl.OrganisationRole.implementing
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())

    def test_registry_dataset(self):
        fac.DatasetFactory.create(name=u"aaa", resources=[])
        fac.DatasetFactory.create(name=u"zzz", resources=[])
        act_in = fac.ActivityFactory.create(
                resource=fac.ResourceFactory.build(
                    url=u"http://test.com",
                    dataset_id=u"aaa")
                )
        act_not = fac.ActivityFactory.create(
                resource=fac.ResourceFactory.build(
                    url=u"http://test2.com",
                    dataset_id=u"zzz")
                )
        activities = dsfilter.activities({
            "registry-dataset": u"aaa"
        })
        self.assertIn(act_in, activities.all())
        self.assertNotIn(act_not, activities.all())


class TestTransactionFilter(AppTestCase):
    def test_by_country_code(self):
        trans_in = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(
                recipient_country_percentages=[
                    fac.CountryPercentageFactory.build(
                        country=cl.Country.libya),
                ])
        )
        trans_not = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(
                recipient_country_percentages=[
                    fac.CountryPercentageFactory.build(
                        country=cl.Country.zambia),
                ])
        )
        transactions = dsfilter.transactions({
            "recipient-country": cl.Country.from_string(u"LY")
        })
        self.assertIn(trans_in, transactions.all())
        self.assertNotIn(trans_not, transactions.all())

    def test_by_reporting_org_ref(self):
        trans_in = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(
                reporting_org=fac.OrganisationFactory.build(
                    ref=u"AAA"
                ))
            )
        trans_not = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(
                reporting_org=fac.OrganisationFactory.build(
                    ref=u"ZZZ"
                ))
            )
        transactions = dsfilter.transactions({
            "reporting-org": u"AAA"
        })
        self.assertIn(trans_in, transactions.all())
        self.assertNotIn(trans_not, transactions.all())

    def test_by_participating_org_ref(self):
        trans_in = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(
                participating_orgs=[
                    fac.ParticipationFactory.build(
                        organisation__ref=u"AAA")
                ]))
        trans_not = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(
                participating_orgs=[
                    fac.ParticipationFactory.build(
                        organisation__ref=u"ZZZ")
                ]))

        transactions = dsfilter.transactions({
            "participating-org": u"AAA"
        })
        self.assertIn(trans_in, transactions.all())
        self.assertNotIn(trans_not, transactions.all())

    def test_by_participating_org_text(self):
        trans_in = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(
                participating_orgs=[
                    fac.ParticipationFactory.build(
                        organisation__ref=u"AAA", organisation__name=u"aaa")
                ]))
        trans_not = fac.TransactionFactory.create(
            activity=fac.ActivityFactory.build(
                participating_orgs=[
                    fac.ParticipationFactory.build(
                        organisation__ref=u"ZZZ", organisation__name=u"zzz")
                ]))

        transactions = dsfilter.transactions({
            "participating-org.text": u"aaa"
        })
        self.assertIn(trans_in, transactions.all())
        self.assertNotIn(trans_not, transactions.all())


class TestBudgetFilter(AppTestCase):
    def test_by_country_code(self):
        budget_in = fac.BudgetFactory.create(
            activity=fac.ActivityFactory.build(
                recipient_country_percentages=[
                    fac.CountryPercentageFactory.build(
                        country=cl.Country.libya),
                ])
        )
        budget_not = fac.BudgetFactory.create(
            activity=fac.ActivityFactory.build(
                recipient_country_percentages=[
                    fac.CountryPercentageFactory.build(
                        country=cl.Country.zambia),
                ])
        )
        budgets = dsfilter.budgets({
            "recipient-country": cl.Country.from_string(u"LY")
        })
        self.assertIn(budget_in, budgets.all())
        self.assertNotIn(budget_not, budgets.all())

    def test_by_reporting_org_ref(self):
        budget_in = fac.BudgetFactory.create(
            activity=fac.ActivityFactory.build(
                reporting_org=fac.OrganisationFactory.build(
                    ref=u"AAA"
                ))
            )
        budget_not = fac.BudgetFactory.create(
            activity=fac.ActivityFactory.build(
                reporting_org=fac.OrganisationFactory.build(
                    ref=u"ZZZ"
                ))
            )
        budgets = dsfilter.budgets({
            "reporting-org": u"AAA"
        })
        self.assertIn(budget_in, budgets.all())
        self.assertNotIn(budget_not, budgets.all())

    def test_by_participating_org_ref(self):
        budget_in = fac.BudgetFactory.create(
            activity=fac.ActivityFactory.build(
                participating_orgs=[
                    fac.ParticipationFactory.build(
                        organisation__ref=u"AAA")
                ]))
        budget_not = fac.BudgetFactory.create(
            activity=fac.ActivityFactory.build(
                participating_orgs=[
                    fac.ParticipationFactory.build(
                        organisation__ref=u"ZZZ")
                ]))

        budgets = dsfilter.budgets({
            "participating-org": u"AAA"
        })
        self.assertIn(budget_in, budgets.all())
        self.assertNotIn(budget_not, budgets.all())
