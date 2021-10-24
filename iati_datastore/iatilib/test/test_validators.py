import datetime
from unittest import TestCase

from iatilib.frontend import validators
from iatilib import codelists


class TestApiDate(TestCase):
    def test_valid_date(self):
        self.assertEqual(
            validators.apidate("2007-01-25"),
            datetime.date(2007, 1, 25)
            )

    def test_invalid_date(self):
        with self.assertRaises(validators.Invalid):
            validators.apidate("1-1-2012")


class TestCodelist(TestCase):
    def test_valid_organisation_role(self):
        self.assertEqual(
            validators.organisation_role("implementing"),
            [codelists.OrganisationRole.implementing]
        )

    def test_multiple_codes(self):
        self.assertEqual(
            validators.reporting_org_type("10|40"),
            [codelists.OrganisationType.government, codelists.OrganisationType.multilateral]
        )

    def test_multiple_codes_values(self):
        self.assertEqual(
            [x.value for x in validators.reporting_org_type("10|xx")],
            ['10', 'xx']
        )


class TestApiSchema(TestCase):
    def test_max_per_page(self):
        with self.assertRaises(validators.MultipleInvalid):
            validators.activity_api_args({"limit": 1000000})

    def test_per_page_string(self):
        self.assertEqual(
            validators.activity_api_args({"limit": "10"}),
            {"limit": 10}
            )

    def test_limit_zero(self):
        """
        [#96] offset of zero should be allowed!
        """
        self.assertEqual(
            validators.activity_api_args({"offset": "0"}),
            {"offset": 0}
            )

    def test_date(self):
        self.assertEqual(
            validators.activity_api_args({"date": "2007-05-25"}),
            {"date": datetime.date(2007, 5, 25)}
            )

    def test_stream(self):
        self.assertEqual(
            validators.activity_api_args({"stream": "t"}),
            {"stream": True}
        )
