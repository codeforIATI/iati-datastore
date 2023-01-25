from unittest import TestCase

from iatilib import codelists as cl

class TestSectorCodelist(TestCase):
    def test_sector_codelist(self):
        self.assertEquals(
            cl.by_major_version['2'].Sector.primary_education.value,
            "11220"
            )
        self.assertEquals(
            cl.by_major_version['2'].Sector.primary_education.description,
            "Primary education"
            )

    def test_sector_codelist_es(self):
        self.assertEquals(
            cl.by_major_version['2'].Sector.primary_education.translations['es'],
            "Educación primaria"
            )

    def test_sector_codelist_fr(self):
        self.assertEquals(
            cl.by_major_version['2'].Sector.primary_education.translations['fr'],
            "Enseignement primaire"
            )

    def test_sector_codelist_pt(self):
        self.assertEquals(
            cl.by_major_version['2'].Sector.primary_education.translations['pt'],
            "Ensino primário"
            )


class TestRegionCodelist(TestCase):
    def test_region_codelist(self):
        self.assertEquals(
            cl.by_major_version['2'].Region.eastern_africa_regional.value,
            "1027"
            )
        self.assertEquals(
            cl.by_major_version['2'].Region.eastern_africa_regional.description,
            "Eastern Africa, regional"
            )

    def test_region_codelist_es(self):
        self.assertEquals(
            cl.by_major_version['2'].Region.eastern_africa_regional.translations['es'],
            "África Oriental, regional"
            )

    def test_region_codelist_fr(self):
        self.assertEquals(
            cl.by_major_version['2'].Region.eastern_africa_regional.translations['fr'],
            "Afrique de l'est, régional"
            )

    def test_region_codelist_pt(self):
        self.assertEquals(
            cl.by_major_version['2'].Region.eastern_africa_regional.translations['pt'],
            "África Oriental, regional"
            )
