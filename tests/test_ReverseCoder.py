from pathlib import Path
from properties_map.template import apartment_db_templates as at
from properties_map.osm import ReverseCoder
from properties_map.apartment import Address, Apartment, DB
import unittest, re

class TestReverseCoder(unittest.TestCase):
    def setUp(self):
        # db_path = Path('apartments/database/testing.db')
        # self.db = DB(apartment_db_templates, db_path)
        self.addresses = []
        self.add1_str = 'Zweenfurther Strasse 7,04318,Leipzig'
        self.add1 = Address(street='Zweenfurther Strasse',nr= '7', city='Leipzig')
        self.ap1 = Apartment(at.apartment ,id=0, address=self.add1_str)
        self.addresses.append(self.ap1)
        
        self.add2_str = '04318 Leipzig (Sellerhausen-Stünz), Plaussiger Str. 9'
        self.add2 = Address(street='Plaussiger Str',nr= '9', city='Leipzig')
        self.ap2 = Apartment(at.apartment ,id=1, address=self.add2_str)
        self.addresses.append(self.ap2)

        self.add3_str = '04105 Leipzig (Zentrum-Nord), Erich-Weinert-Strasse 22'
        self.add3 = Address(street='Erich-Weinert-Strasse',nr= '22', city='Leipzig')
        self.ap3 = Apartment(at.apartment ,id=2, address=self.add3_str)
        self.addresses.append(self.ap3)

        self.add4_str = 'Straße des 18. Oktober 19, 04103,Leizpig'
        self.add4 = Address(street='Straße des 18. Oktober',nr= '19', city='Leipzig')
        self.ap4 = Apartment(at.apartment ,id=3, address=self.add4_str)
        self.addresses.append(self.ap4)

        self.add5_str = 'Delitzscher Str. 7f, Zentrum-Nord, Leipzig'
        self.add5 = Address(street='Delitzscher Str. 7f',nr= '7f', city='Leipzig')
        self.ap5 = Apartment(at.apartment ,id=4, address=self.add5_str)
        self.addresses.append(self.ap5)

        self.add6_str = 'Fliederhof 6, Schönefeld-Abtnaundorf, Leipzig'
        self.add6 = Address(street='Fliederhof 6',nr= '6', city='Leipzig')
        self.ap6 = Apartment(at.apartment ,id=5, address=self.add6_str)
        self.addresses.append(self.ap6)

        self.add7_str = 'Sandmännchenweg 9, Marienbrunn, Leipzig'
        self.add7 = Address(street='Sandmännchenweg 9',nr= '9', city='Leipzig')
        self.ap7 = Apartment(at.apartment ,id=6, address=self.add7_str)
        self.addresses.append(self.ap7)

        self.add8_str = 'Zentrum-West, Leipzig'
        self.add8 = Address(street=None, nr=None, city='Leipzig')
        self.ap8 = Apartment(at.apartment ,id=7, address=self.add8_str)
        self.addresses.append(self.ap8)

        self.rc = ReverseCoder(self.addresses)
        # self._re_street_nr = re.compile('([a-zA-ZäöüÄÖÜß\s.\-]+(?=\d))(\d{,3}\w?)')
    def test_parse_address(self):
        p1 = self.rc._parse_address(self.add1_str)
        self.assertEqual(p1.street, 'Zweenfurther Strasse')
        self.assertEqual(p1.nr, '7')
        p2 = self.rc._parse_address(self.add2_str)
        self.assertEqual(p2.street, 'Plaussiger Str.')
        self.assertEqual(p2.nr, '9')
        p3 = self.rc._parse_address(self.add3_str)
        self.assertEqual(p3.street, 'Erich-Weinert-Strasse')
        self.assertEqual(p3.nr, '22')
        p4 = self.rc._parse_address(self.add4_str)
        self.assertEqual(p4.street, 'Straße des 18. Oktober')
        self.assertEqual(p4.nr, '19')
        p5 = self.rc._parse_address(self.add5_str)
        self.assertEqual(p5.street, 'Delitzscher Str.')
        self.assertEqual(p5.nr, '7f')
        p6 = self.rc._parse_address(self.add6_str)
        self.assertEqual(p6.street, 'Fliederhof')
        self.assertEqual(p6.nr, '6')
        p7 = self.rc._parse_address(self.add7_str)
        self.assertEqual(p7.street, 'Sandmännchenweg')
        self.assertEqual(p7.nr, '9')
        p8 = self.rc._parse_address(self.add8_str)
        self.assertEqual(p8, None)



    def test_make_tag_filter(self):
        tag1 = self.rc._make_tag_filter(self.add1)
        self.assertIsNotNone(re.search(tag1['addr:street'],self.add1.street))
        self.assertIsNotNone(re.search(tag1['addr:housenumber'],self.add1.nr))
        self.assertIsNotNone(re.search(tag1['addr:city'],self.add1.city))
        tag2 = self.rc._make_tag_filter(self.add2)
        self.assertIsNotNone(re.search(tag2['addr:street'],self.add2.street))
        self.assertIsNotNone(re.search(tag2['addr:housenumber'],self.add2.nr))
        self.assertIsNotNone(re.search(tag2['addr:city'],self.add2.city))
        tag3 = self.rc._make_tag_filter(self.add3)
        self.assertIsNotNone(re.search(tag3['addr:street'],self.add3.street))
        self.assertIsNotNone(re.search(tag3['addr:housenumber'],self.add3.nr))
        self.assertIsNotNone(re.search(tag3['addr:city'],self.add3.city))
        tag4 = self.rc._make_tag_filter(self.add4)
        self.assertIsNotNone(re.search(tag4['addr:street'],self.add4.street))
        self.assertIsNotNone(re.search(tag4['addr:housenumber'],self.add4.nr))
        self.assertIsNotNone(re.search(tag4['addr:city'],self.add4.city))
        tag5 = self.rc._make_tag_filter(self.add5)
        self.assertIsNotNone(re.search(tag5['addr:street'],self.add5.street))
        self.assertIsNotNone(re.search(tag5['addr:housenumber'],self.add5.nr))
        self.assertIsNotNone(re.search(tag5['addr:city'],self.add5.city))
        tag6 = self.rc._make_tag_filter(self.add6)
        self.assertIsNotNone(re.search(tag6['addr:street'],self.add6.street))
        self.assertIsNotNone(re.search(tag6['addr:housenumber'],self.add6.nr))
        self.assertIsNotNone(re.search(tag6['addr:city'],self.add6.city))
        tag7 = self.rc._make_tag_filter(self.add7)
        self.assertIsNotNone(re.search(tag7['addr:street'],self.add7.street))
        self.assertIsNotNone(re.search(tag7['addr:housenumber'],self.add7.nr))
        self.assertIsNotNone(re.search(tag7['addr:city'],self.add7.city))