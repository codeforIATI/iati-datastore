import datetime
from collections import namedtuple

from . import CSVTstMixin as _CSVTstMixin

from iatilib.test import factories as fac, AppTestCaseNoDb
from iatilib.frontend import serialize
from iatilib import codelists as cl


class CSVTstMixin(_CSVTstMixin):
    def serialize(self, data):
        return serialize.budget_csv(data)


def example():
    activity = fac.ActivityFactory.build(
        iati_identifier="GB-1-123",
        title="Project 123",
        description="Desc project 123",
        recipient_country_percentages=[
            fac.CountryPercentageFactory.build(
                country=cl.Country.kenya,
                percentage=80,
            ),
            fac.CountryPercentageFactory.build(
                country=cl.Country.uganda,
                percentage=20,
            )
        ],
        sector_percentages=[
            fac.SectorPercentageFactory.build(
                sector=cl.Sector.teacher_training,
                percentage=60
            ),
            fac.SectorPercentageFactory.build(
                sector=cl.Sector.primary_education,
                percentage=40
            ),

        ]
    )

    budgets = [
        fac.BudgetFactory.build(
            period_start=datetime.datetime(2012, 1, 1),
            period_end=datetime.datetime(2012, 12, 31),
            value_amount=100000,
            type=cl.BudgetType.original,
        ),
        fac.BudgetFactory.build(
            period_start=datetime.datetime(2012, 1, 1),
            period_end=datetime.datetime(2012, 12, 31),
            value_amount=200000,
            type=cl.BudgetType.revised,
        ),
        fac.BudgetFactory.build(
            period_start=datetime.datetime(2012, 1, 1),
            period_end=datetime.datetime(2012, 12, 31),
            value_amount=500000,
            type=None,
        )


    ]
    for budget in budgets:
        budget.activity = activity
    activity.budgets = budgets
    return activity


class TestCSVBudgetExample(AppTestCaseNoDb, CSVTstMixin):
    # See example here: https://docs.google.com/a/okfn.org/spreadsheet/ccc?key=0AqR8dXc6Ji4JdHJIWDJtaXhBV0IwOG56N0p1TE04V2c&usp=sharing#gid=5
    def test_start(self):
        data = self.process([
            fac.BudgetFactory.build(period_start=datetime.date(2012, 1, 1))
        ])
        self.assertField({"budget-period-start-date": "2012-01-01"}, data[0])

    def test_end(self):
        data = self.process([
            fac.BudgetFactory.build(period_end=datetime.date(2012, 1, 1))
        ])
        self.assertField({"budget-period-end-date": "2012-01-01"}, data[0])

    def test_value(self):
        data = self.process([
            fac.BudgetFactory.build(value_amount=100000)
        ])
        self.assertField({"budget-value": "100000"}, data[0])

    def test_type(self):
        data = self.process([
            fac.BudgetFactory.build(type=cl.BudgetType.original)
        ])
        self.assertField({"budget-type": "original"}, data[0])

    def test_iati_identifier(self):
        data = self.process([
            fac.BudgetFactory.build(
                value_amount=100000,
                activity=fac.ActivityFactory.build(iati_identifier="GB-123")
            )
        ])
        self.assertField({"iati-identifier": "GB-123"}, data[0])

    def test_title(self):
        data = self.process([
            fac.BudgetFactory.build(
                value_amount=100000,
                activity=fac.ActivityFactory.build(title="Project 123")
            )
        ])
        self.assertField({"title": "Project 123"}, data[0])

    def test_description(self):
        data = self.process([
            fac.BudgetFactory.build(
                activity=fac.ActivityFactory.build(description="Desc 123")
            )
        ])
        self.assertField({"description": "Desc 123"}, data[0])

    def test_recepient_country_code(self):
        data = self.process([
            fac.BudgetFactory.build(
                activity=fac.ActivityFactory.build(
                    recipient_country_percentages=[
                        fac.CountryPercentageFactory.build(
                            country=cl.Country.nigeria
                            )
                    ]
                )
            )
        ])
        self.assertField({"recipient-country-code": "NG"}, data[0])

    def test_recepient_country(self):
        data = self.process([
            fac.BudgetFactory.build(
                activity=fac.ActivityFactory.build(
                    recipient_country_percentages=[
                        fac.CountryPercentageFactory.build(
                            country=cl.Country.nigeria
                            )
                    ]
                )
            )
        ])
        self.assertField({"recipient-country": "Nigeria"}, data[0])

    def test_recepient_country_percentage(self):
        data = self.process([
            fac.BudgetFactory.build(
                activity=fac.ActivityFactory.build(
                    recipient_country_percentages=[
                        fac.CountryPercentageFactory.build(
                            country=cl.Country.nigeria,
                            percentage=20
                            )
                    ]
                )
            )
        ])
        self.assertField({"recipient-country-percentage": "20"}, data[0])

    def test_sector_code(self):
        data = self.process([
            fac.BudgetFactory.build(
                activity=fac.ActivityFactory.build(
                    sector_percentages=[
                        fac.SectorPercentageFactory.build(
                            sector=cl.Sector.teacher_training
                            )
                    ]
                )
            )
        ])
        self.assertField({"sector-code": "11130"}, data[0])

    def test_sector(self):
        data = self.process([
            fac.BudgetFactory.build(
                activity=fac.ActivityFactory.build(
                    sector_percentages=[
                        fac.SectorPercentageFactory.build(
                            sector=cl.Sector.teacher_training
                            )
                    ]
                )
            )
        ])
        self.assertField({"sector": "Teacher training"}, data[0])

    def test_sector_percentage(self):
        data = self.process([
            fac.BudgetFactory.build(
                activity=fac.ActivityFactory.build(
                    sector_percentages=[
                        fac.SectorPercentageFactory.build(
                            percentage=20
                            )
                    ]
                )
            )
        ])
        self.assertField({"sector-percentage": "20"}, data[0])


class TestBudgetByCountry(AppTestCaseNoDb, CSVTstMixin):
    def serialize(self, data):
        return serialize.csv_budget_by_country(data)

    def example(self):
        ret = []
        act = example()
        NT = namedtuple('CountryBudget', 'Budget CountryPercentage')
        for budget in act.budgets:
            for country in act.recipient_country_percentages:
                ret.append(NT(budget, country))
        return ret

    def test_rec_country_code_0(self):
        data = self.process(self.example())
        self.assertField({"recipient-country-code": "KE"}, data[0])

    def test_rec_country_code_1(self):
        data = self.process(self.example())
        self.assertField({"recipient-country-code": "UG"}, data[1])

    def test_budget_start_date(self):
        data = self.process(self.example())
        self.assertField(
            {"budget-period-start-date": "2012-01-01"},
            data[0])

    def test_type_0(self):
        data = self.process(self.example())
        self.assertField({"budget-type": "original"}, data[0])

    def test_type_1(self):
        data = self.process(self.example())
        self.assertField({"budget-type": "revised"}, data[2])

    def test_type_none(self):
        data = self.process(self.example())
        self.assertField({"budget-type": ""}, data[5])

    def test_identifier(self):
        data = self.process(self.example())
        self.assertField({"iati-identifier": "GB-1-123"}, data[2])


class TestBudgetBySector(AppTestCaseNoDb, CSVTstMixin):
    def serialize(self, data):
        return serialize.csv_budget_by_sector(data)

    def example(self):
        ret = []
        act = example()
        NT = namedtuple('SectorBudget', 'Budget SectorPercentage')
        for budget in act.budgets:
            for sector in act.sector_percentages:
                ret.append(NT(budget, sector))
        return ret

    def test_sector_code_0(self):
        data = self.process(self.example())
        self.assertField({"sector-code": "11130"}, data[0])

    def test_sector_code_1(self):
        data = self.process(self.example())
        self.assertField({"sector-code": "11220"}, data[1])

    def test_budget_start_date(self):
        data = self.process(self.example())
        self.assertField(
            {"budget-period-start-date": "2012-01-01"},
            data[0])

    def test_type_0(self):
        data = self.process(self.example())
        self.assertField({"budget-type": "original"}, data[0])

    def test_type_1(self):
        data = self.process(self.example())
        self.assertField({"budget-type": "revised"}, data[2])

    def test_type_none(self):
        data = self.process(self.example())
        self.assertField({"budget-type": ""}, data[4])

    def test_identifier(self):
        data = self.process(self.example())
        self.assertField({"iati-identifier": "GB-1-123"}, data[2])

    # def test_recepient_country_code(self):
    #     data = self.process(self.example())
    #     self.assertField({"recipient-country-code": "KE;UG"}, data[0])
