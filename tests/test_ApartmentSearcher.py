from pathlib import Path
from requests_html import HTML, HTMLSession, Element
from properties_map.apartment import ApartmentSearcher,Immobilienscout24, Immowelt, Immonet, DatabaseEntry
from properties_map.apartment import DB
from properties_map.template import _sample_templates, templates

import unittest

class TestApartmentSearcher(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        sample_db = DB(_sample_templates,Path('apartments/database/testing.db'))
        self.sample_db = sample_db
        self.insert_web_sql = sample_db.templates.web.get_insert_sql()
        self.insert_expose_sql = sample_db.templates.expose.get_insert_sql()
        sample_db.c.execute('select html from web where website="immobilienscout24"')
        _html = sample_db.c.fetchone()[0]
        self.immobilienscout = HTML(html=_html)
        sample_db.c.execute('select html from expose where website="immobilienscout24"')
        _html = sample_db.c.fetchone()[0]
        self.immobilienscout_expose = HTML(html=_html)

        sample_db.c.execute('select html from web where website="immowelt"')
        _html = sample_db.c.fetchone()[0]
        self.immowelt = HTML(html=_html)
        sample_db.c.execute('select html from expose where website="immowelt"')
        _html = sample_db.c.fetchone()[0]
        self.immowelt_expose = HTML(html=_html)

        sample_db.c.execute('select html from web where website="immonet"')
        _html = sample_db.c.fetchone()[0]
        self.immonet = HTML(html=_html)
        sample_db.c.execute('select html from expose where website="immonet"')
        _html = sample_db.c.fetchone()[0]
        self.immonet_expose = HTML(html=_html)
        s = HTMLSession()
        self.immob_searcher = Immobilienscout24(s,templates.apartment, templates.image)
        self.immow_searcher = Immowelt(s,templates.apartment, templates.image)
        self.immon_searcher = Immonet(s,templates.apartment, templates.image)
        self.previews_immob = self.immob_searcher.get_preview_elements(self.immobilienscout)
        self.previews_immow = self.immow_searcher.get_preview_elements(self.immowelt)
        self.previews_immon = self.immon_searcher.get_preview_elements(self.immonet)
        _prem = '<div><div class="js-object listitem_wrap blickfang">\n<div class="listitem premium clear relative js-listitem">\n<a href="/expose/2anx74p?bc=13"></a>\n<div class="listimage relative js-listitem-image has_my_logo">\n<div class="img_center_wrapper">\n<div class="img_center">\n\n\n<source></source>\n<source media="(max-width: 980px), (min-width: 640px)"></source>\n\n<img alt="Leipzig Wohnungen, Leipzig Wohnung mieten" class="js_listimage" src="https://media-pics1.immowelt.org/6/e/7/a/318bdcf6e06844c18530ec9b097ba7e6.jpg">\n\n</div>\n</div>\n<span class="iw_flag_new">\n<img src="/App_Themes/GLOBAL_RWD/image/misc/iw_flag_new.svg">\n</span>\n<div class="premium_images clear">\n<div class="image_small clear">\n<img src="https://media-thumbs2.immowelt.org/B/A/9/8/300_3D0F8A41BB8F42A991A3998DA15289AB.jpg" class="js_listimage">\n</div>\n<div class="image_small clear">\n<img src="https://media-thumbs1.immowelt.org/7/E/C/B/300_5BC3B9F387E44C47844E60BE3AC9BCE7.jpg" class="js_listimage">\n</div>\n<div class="image_small clear">\n<img src="https://media-thumbs1.immowelt.org/1/6/4/6/300_16D2BB2E05F14265A4D9B0658F266461.jpg" class="js_listimage">\n</div>\n</div>\n</div>\n<div class="listcontent clear">\n<h2 class="js-premiumTitle">Schn&#xE4;ppchen, sehr ruhige, gr&#xFC;ne und sonnige 3 RW  ab sofort zu vermieten</h2>\n<div class="details">\n<div class="listlocation ellipsis relative" title="Genauer Standort in der Kartenansicht sichtbar">\n<span class="icon-map-marker location_exact"></span>&#13;\n04347 Leipzig (Sch&#xF6;nefeld-Abtnaundorf), Dimpfelstr.55&#13;\n                    &#13;\n&#13;\n                </div>\n<ul class="js-EqList eq_list clear">\n<li>Balkon</li>\n<li>Stellplatz</li>\n<li>Bad mit Wanne</li>\n<li>Kelleranteil</li>\n<li>renoviert</li>\n<li>saniert</li>\n<li>frei</li>\n<li>WG geeignet</li>\n</ul>\n<div class="clear"></div>\n</div>\n<div class="hardfacts_3 clear">\n<div class="hardfact price_rent">\n<div class="hardfactlabel">&#13;\nKaltmiete zzgl. NK        </div>\n<strong>&#13;\n                480 &#x20AC;&#13;\n            </strong>\n</div>\n<div class="hardfact square_meters">\n<div class="hardfactlabel">&#13;\nWohnfl&#xE4;che (ca.)        </div>&#13;\n&#13;\n81,36 m&#xB2;    </div>\n<div class="hardfact rooms">\n<div class="hardfactlabel">&#13;\nZimmer        </div>&#13;\n&#13;\n3    </div>\n</div>\n<div class="my_logo_wrap clear">\n<div class="type">Privater <br class="no_s">Anbieter</div>\n</div>\n<a title="F&#xFC;gt dieses Objekt zum Merkzettel hinzu." class="js-remember btn_remember icon-heart-empty" href="#">\n</a>\n<div id="remember-42637237" class="arrow_tooltip arrow_right_top">&#13;\n                Das Objekt wurde Ihrem<br>\n<a href="">Merkzettel</a> hinzugef&#xFC;gt.&#13;\n            </div>\n</div>\n</div>\n</div></div>'
        self.preview_premium_immow = HTML(html=_prem)
        self.base_template = DatabaseEntry(_sample_templates.web)

    def test_base_template_parse_price(self):
        price = self.base_template.parse_price('10 €')
        self.assertEqual(10.0, price)
        price = self.base_template.parse_price('100 €')
        self.assertEqual(100.0, price)
        price = self.base_template.parse_price('10.50 €')
        self.assertEqual(10.5, price)
        price = self.base_template.parse_price('$ 109.50')
        self.assertEqual(109.5, price)
        price = self.base_template.parse_price('€ 109,88 €')
        self.assertEqual(109.88, price)
        price = self.base_template.parse_price('1.050,00 €')
        self.assertEqual(1050.00, price)
    
    def test_immobilienscout_get_pages(self):
        pages = self.immob_searcher.get_pages(self.immobilienscout)
        self.assertEqual(pages, 5)
    def test_immowelt_get_pages(self):
        pages = self.immow_searcher.get_pages(self.immowelt)
        self.assertEqual(pages, 3)

    def test_immonet_get_pages(self):
        pages = self.immon_searcher.get_pages(self.immonet)
        self.assertEqual(pages, 3)

    def test_immobilienscout_preload(self):
        results = self.immob_searcher.preload(self.immobilienscout,test=True)
        self.assertEqual(results[1].split('&')[-1], 'pagenumber=2')
        self.assertEqual(len(results), 5)

    def test_immowelt_preload(self):
        results = self.immow_searcher.preload(self.immowelt,test=True)
        # preload has only 1 result but with all previews
        # because it loads them after with a post
        self.assertEqual(results[0].split('&')[-1], 'cp=1')
        self.assertEqual(len(results), 1)
    def test_immonet_preload(self):
        results = self.immon_searcher.preload(self.immonet,test=True)
        self.assertEqual(results[1].split('&')[-1], 'page=2')
        self.assertEqual(len(results), 3)

    def test_immobilienscout_get_preview_elements(self):
        previews = self.immob_searcher.get_preview_elements(self.immobilienscout)
        self.assertEqual(len(previews), 20)
        self.assertEqual(type(previews[0]), Element)
        self.assertEqual(type(previews[-1]), Element)

    def test_immowelt_get_preview_elements(self):
        previews = self.immow_searcher.get_preview_elements(self.immowelt)
        self.assertEqual(len(previews), 4)
        self.assertEqual(type(previews[0]), Element)
        self.assertEqual(type(previews[-1]), Element)
        premium_preview = self.immow_searcher.get_preview_elements(self.preview_premium_immow)
        self.assertEqual(len(premium_preview), 1)

    
    def test_immonet_get_preview_elements(self):
        previews = self.immon_searcher.get_preview_elements(self.immonet)
        self.assertEqual(len(previews), 26)
        self.assertEqual(type(previews[0]), Element)
        self.assertEqual(type(previews[-1]), Element)

        

    def test_immobilienscout_get_title(self):
        title = self.immob_searcher.get_title(self.previews_immob[0])
        self.assertEqual(title, 'Schöne 3-Zwhg ca. 69m², Tageslichtbad und Laminatboden')
        title_with_new = self.immob_searcher.get_title(self.previews_immob[6])
        self.assertEqual(title_with_new, 'LIVIA-IMMO.DE :-) +SUPER AUSBLICK! ERSTBEZUG+NEUBAU+3 ZIMMER+LOGGIA+FuBo-HEIZUNG')

    def test_immowelt_get_title(self):
        title = self.immow_searcher.get_title(self.previews_immow[0])
        premium_title = self.immow_searcher.get_title(self.preview_premium_immow)
        self.assertEqual(premium_title, 'Schnäppchen, sehr ruhige, grüne und sonnige 3 RW ab sofort zu vermieten')
        self.assertEqual(title, '3-Zimmerwohnung im Leipziger Osten')
    
    def test_immonet_get_title(self):
        title = self.immon_searcher.get_title(self.previews_immon[0])
        self.assertEqual(title, 'hochwertige Wohnung mit Balkon in Schönefeld')
        title = self.immon_searcher.get_title(self.previews_immon[1])
        self.assertEqual(title, 'Balkon + Loggia - 3-Raum-Wohung im schönen Fliederhof')


    def test_immobilienscout_get_preview_img(self):
        preview_img = self.immob_searcher.get_preview_img(self.previews_immob[0])
        self.assertEqual(preview_img, 'https://pictures.immobilienscout24.de/listings/0aca4653-6460-4e39-adee-b6389983a906-1127251492.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80')
        preview_img = self.immob_searcher.get_preview_img(self.previews_immob[2])
        self.assertEqual(preview_img, 'https://pictures.immobilienscout24.de/listings/1bb2cc3b-756c-46f4-9b5e-bd79db776fa0-1370478128.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80')
    def test_immowelt_get_preview_img(self):
        preview_img = self.immow_searcher.get_preview_img(self.previews_immow[0])
        self.assertEqual(preview_img, 'https://media-pics2.immowelt.org/9/5/b/6/622df664effd4029a5a08b0e26016b59.jpg')
    
    def test_immonet_get_preview_img(self):
        preview_img = self.immon_searcher.get_preview_img(self.previews_immon[0])
        self.assertEqual(preview_img, 'https://i.immonet.de/94/62/05/637946205_280x374.jpg')
        premium_preview_img = self.immow_searcher.get_preview_img(self.preview_premium_immow)
        self.assertEqual(premium_preview_img, 'https://media-pics1.immowelt.org/6/e/7/a/318bdcf6e06844c18530ec9b097ba7e6.jpg')

    def test_immobilienscout_get_address(self):
        address = self.immob_searcher.get_address(self.previews_immob[0])
        self.assertEqual(address, 'Heinrichstr. 29, Reudnitz-Thonberg, Leipzig')

    def test_immowelt_get_address(self):
        address = self.immow_searcher.get_address(self.previews_immow[0])
        self.assertEqual(address, '04318 Leipzig (Sellerhausen-Stünz), Permoserstr. 24 2,1 km')
        premium_address = self.immow_searcher.get_address(self.preview_premium_immow)
        self.assertEqual(premium_address, '04347 Leipzig (Schönefeld-Abtnaundorf), Dimpfelstr.55')

    def test_immonet_get_address(self):
        address = self.immon_searcher.get_address(self.previews_immon[0])
        self.assertEqual(address, None)
    
    def test_immobilienscout_get_expose_src(self):
        expose_src = self.immob_searcher.get_expose_src(self.previews_immob[0])
        self.assertEqual(expose_src, 'https://example.org/expose/64607085')

    def test_immowelt_get_expose_src(self):
        expose_src = self.immow_searcher.get_expose_src(self.previews_immow[0])
        self.assertEqual(expose_src, 'https://example.org/expose/2vtbg4e')
        premium_expose_src = self.immow_searcher.get_expose_src(self.preview_premium_immow)
        self.assertEqual(premium_expose_src, 'https://example.org/expose/2anx74p?bc=13')
    
    def test_immonet_get_expose_src(self):
        expose_src = self.immon_searcher.get_expose_src(self.previews_immon[0])
        self.assertEqual(expose_src, 'https://example.org/angebot/40899848')


    def test_immobilienscout_get_expose_category(self):
        total_rent = self.immob_searcher.get_expose_category(self.immobilienscout_expose, self.immob_searcher.total_rent_sel)
        self.assertEqual(total_rent, '520 €')
        cold_rent = self.immob_searcher.get_expose_category(self.immobilienscout_expose, self.immob_searcher.cold_rent_sel)
        self.assertEqual(cold_rent, '380 €')
        add_costs = self.immob_searcher.get_expose_category(self.immobilienscout_expose, self.immob_searcher.add_costs_sel)
        self.assertEqual(add_costs, '+ 140 €')
        deposit = self.immob_searcher.get_expose_category(self.immobilienscout_expose, self.immob_searcher.deposit_sel)
        self.assertEqual(deposit, '760 EUR')
        living_area = self.immob_searcher.get_expose_category(self.immobilienscout_expose, self.immob_searcher.living_area_sel)
        self.assertEqual(living_area, '62 m²')
        rooms = self.immob_searcher.get_expose_category(self.immobilienscout_expose, self.immob_searcher.rooms_sel)
        self.assertEqual(rooms, '3')
        description = self.immob_searcher.get_expose_category(self.immobilienscout_expose, self.immob_searcher.description_sel)
        self.assertEqual(description, 'In der Leonhard-Frank-Straße / Max-Borsdorf-Straße wurde in den letzten Jahren ein GEBÄUDEENSEMBLE aus drei 5 - geschossigen WOHNBLÖCKEN der 80- er Jahre (bekannt als WBS 70) energieeffizient und zeitgemäß modernisiert. Im 2013 modernisierten Abschnitt der Leonard-Frank-Str.9-11a steht ab Juli wieder eine 3 Raum Wohnung zur Verfügung.')
        energy_usage = self.immob_searcher.get_expose_category(self.immobilienscout_expose, self.immob_searcher.energy_usage_sel)
        self.assertEqual(energy_usage, None)
        available = self.immob_searcher.get_expose_category(self.immobilienscout_expose, self.immob_searcher.available_sel)
        self.assertEqual(available, '01.07.20')
        deposit = self.immob_searcher.get_expose_category(self.immobilienscout_expose, self.immob_searcher.deposit_sel)
        self.assertEqual(deposit, '760 EUR')
        extras = self.immob_searcher._get_extras(self.immobilienscout_expose)
        self.assertEqual(extras, 'Balkon/ Terrasse\nKeller\nGarten/ -mitbenutzung\nWG-geeignet')

    # def test_test(self):
        # _costs = self.immow_searcher._get_costs(self.immowelt_expose)
        # _facts = self.immow_searcher._get_hardfacts(self.immowelt_expose)
        # _desc = self.immow_searcher._get_description(self.immowelt_expose)
        # _energy = self.immow_searcher._get_energy(self.immowelt_expose)
        # _apartment = self.immow_searcher._parse_wohnung(self.immowelt_expose)
        # categories = self.immon_searcher.get_expose_categories(self.immonet_expose)
        # self.assertDictEqual(categories['parsed'], check_parsed)

    def test_immowelt_get_expose_categories(self):
        check_parsed = {'Wohnfläche (ca.)': '76,43 m²', 'Zimmer': '3,5', 'Kaltmiete': '480 €', 'Nebenkosten': '210 €', 'Heizkosten': 'in Warmmiete enthalten', 'Warmmiete': '690 €', 'Preis/m²': '6,28 €', 'Ausstattung': '- Einbauküche (monatlicher Aufpreis: 30,00 €)\n- Tageslichtbad mit Wanne\n- dunkles Laminat\n- geräumiger Flur', 'Objekt': 'Die hier angebotene 3,5 - Raumwohnung befindet sich in der 2. Etage eines Mehrfamilienhauses im Stadtteil Anger-Crottendorf.\n\nAuf einer Wohnfläche von ca. 76 m² erwarten Sie helle Räume, eine separate Küche inkl. Einbauküche (+ 30,00 € / Monat) mit Fenster sowie ein Tageslichtbad mit Badewanne.\n\nDie Wohnräume sind mit ansprechendem Laminatboden (in Parkettoptik) ausgestattet.\n\nDie nächste S-Bahn-Haltestelle erreichen Sie in nur wenigen Gehminuten. Erholung finden Sie im nur 600 Meter entfernten Liselotte-Herrmann-Park. Den nächsten Supermarkt erreichen Sie in 10 Minuten zu Fuß.\n\nGern stehen wir Ihnen für Fragen oder Terminabsprachen telefonisch unter 0341-900 44 00 zur Verfügung!', 'Stichworte': 'Anzahl der Badezimmer: 1', 'Energieausweistyp': 'Verbrauchsausweis', 'Gebäudetyp': 'Wohngebäude', 'Baujahr laut Energieausweis': '1934', 'Endenergieverbrauch': '122,40 kWh/(m²·a) - Warmwasser enthalten', 'Energieeffizienzklasse': 'D', 'Gültigkeit': 'bis 27.12.2027', 'Kaution': '960,00 €', 'Etage': '2. Geschoss', 'Wohnungstyp': 'Etagenwohnung', 'Bezugsfrei': 'frei ab sofort', 'extras': 'Bad mit Fenster und Wanne\nEinbauküche\nWG-geeignet\nBöden: Laminat\nZustand: saniert\nAusstattung: Standard\nWeitere Räume: Kelleranteil'}
        check_categories = {'living_area': '76,43 m²', 'rooms': '3,5', 'extras': 'Bad mit Fenster und Wanne\nEinbauküche\nWG-geeignet\nBöden: Laminat\nZustand: saniert\nAusstattung: Standard\nWeitere Räume: Kelleranteil', 'deposit': '960,00 €', 'cold_rent': '480 €', 'add_costs': '210 €', 'total_rent': '690 €', 'description': 'Die hier angebotene 3,5 - Raumwohnung befindet sich in der 2. Etage eines Mehrfamilienhauses im Stadtteil Anger-Crottendorf.\n\nAuf einer Wohnfläche von ca. 76 m² erwarten Sie helle Räume, eine separate Küche inkl. Einbauküche (+ 30,00 € / Monat) mit Fenster sowie ein Tageslichtbad mit Badewanne.\n\nDie Wohnräume sind mit ansprechendem Laminatboden (in Parkettoptik) ausgestattet.\n\nDie nächste S-Bahn-Haltestelle erreichen Sie in nur wenigen Gehminuten. Erholung finden Sie im nur 600 Meter entfernten Liselotte-Herrmann-Park. Den nächsten Supermarkt erreichen Sie in 10 Minuten zu Fuß.\n\nGern stehen wir Ihnen für Fragen oder Terminabsprachen telefonisch unter 0341-900 44 00 zur Verfügung!', 'energy_usage': '122,40 kWh/(m²·a) - Warmwasser enthalten', 'available': 'frei ab sofort'}
        categories = self.immow_searcher.get_expose_categories(self.immowelt_expose)
        self.assertDictEqual(categories['parsed'], check_parsed)
        del categories['parsed']
        self.assertDictEqual(categories, check_categories)

    def test_immonet_get_expose_categories(self):
        check_parsed = {'Miete zzgl. NK': '405.86€', 'Miete inkl. NK': '569.86€', 'Mietpreis/ m²': '7.0€', 'Nebenkosten': '98.0€', 'Heizkosten': '66.0€', 'Zimmer': '3.0', 'Wohnfläche ca.': '57.98m²', 'Baujahr': '1960', 'Verfügbar ab': '01.08.2020', 'Endenergieverbrauch': '90.0 kWh/(m²*a)', 'Energieausweis': 'Energieverbrauchsausweis', 'Ausgestellt': 'ab dem 1.5.2014', 'Heizungsart': 'Zentralheizung', 'Befeuerungsart': 'Gas', 'Objektbeschreibung': 'Das Gebäude wurde im Jahr 1960 erbaut und im Jahr 1995 umfangreich modernisiert. Das Gebäude umfasst 30 Wohneinheiten, welche allesamt mit Balkon und Tageslichtbad ausgestattet sind.', 'Lage': "Im geschichtsträchtigen Gohliser Süden finden Sie ein zentrumsnahes Zuhause in grüner Umgebung. Der besonders bei Familien beliebte Stadtteil hat viel Sehenswertes zu bieten, so z. B. das im Rokokostil erbaute 'Gohliser Schlösschen' oder das 'Schiller-Haus'. Auch der 'Leipziger Zoo' ist nur einen Katzensprung entfernt. Kleine Parks sowie das 'Rosenthal' laden zum Spazierengehen und Fahrradfahren ein. Der gut angebundene Stadtteil besticht durch ein gepflegtes Umfeld. Entlang der Grünflächen entlang der Elster und Luppe entspannen Sie vom Alltag.", 'Sonstiges': 'Stichworte:\nAnzahl Balkone: 1, 5 Etagen, Wohnungsnr.: 60/3/21, modernisiert'}
        check_categories = {'energy_usage': '90.0 kWh/(m²*a)','address':'Prellerstr. 63 04155 Leipzig','extras': 'Bad: Bad mit Fenster\nBalkon\nFußboden: PVC/Linoleum\nKeller', 'cold_rent': '405.86€', 'deposit': None, 'total_rent': '569.86€', 'add_costs': '98.0€', 'living_area': '57.98m²', 'available': '01.08.2020', 'description': 'Das Gebäude wurde im Jahr 1960 erbaut und im Jahr 1995 umfangreich modernisiert. Das Gebäude umfasst 30 Wohneinheiten, welche allesamt mit Balkon und Tageslichtbad ausgestattet sind.'}
        categories = self.immon_searcher.get_expose_categories(self.immonet_expose)
        self.assertDictEqual(categories['parsed'], check_parsed)
        del categories['parsed']
        self.assertDictEqual(categories, check_categories)

    def test_immobilienscout_get_expose_categories(self):
        # check_parsed = {'Miete zzgl. NK': '405.86€', 'Miete inkl. NK': '569.86€', 'Mietpreis/ m²': '7.0€', 'Nebenkosten': '98.0€', 'Heizkosten': '66.0€', 'Zimmer': '3.0', 'Wohnfläche ca.': '57.98m²', 'Baujahr': '1960', 'Verfügbar ab': '01.08.2020', 'Endenergieverbrauch': '90.0 kWh/(m²*a)', 'Energieausweis': 'Energieverbrauchsausweis', 'Ausgestellt': 'ab dem 1.5.2014', 'Heizungsart': 'Zentralheizung', 'Befeuerungsart': 'Gas', 'Objektbeschreibung': 'Das Gebäude wurde im Jahr 1960 erbaut und im Jahr 1995 umfangreich modernisiert. Das Gebäude umfasst 30 Wohneinheiten, welche allesamt mit Balkon und Tageslichtbad ausgestattet sind.', 'Lage': "Im geschichtsträchtigen Gohliser Süden finden Sie ein zentrumsnahes Zuhause in grüner Umgebung. Der besonders bei Familien beliebte Stadtteil hat viel Sehenswertes zu bieten, so z. B. das im Rokokostil erbaute 'Gohliser Schlösschen' oder das 'Schiller-Haus'. Auch der 'Leipziger Zoo' ist nur einen Katzensprung entfernt. Kleine Parks sowie das 'Rosenthal' laden zum Spazierengehen und Fahrradfahren ein. Der gut angebundene Stadtteil besticht durch ein gepflegtes Umfeld. Entlang der Grünflächen entlang der Elster und Luppe entspannen Sie vom Alltag.", 'Sonstiges': 'Stichworte:\nAnzahl Balkone: 1, 5 Etagen, Wohnungsnr.: 60/3/21, modernisiert'}
        check_categories = {'total_rent': '520 €', 'cold_rent': '380 €', 'add_costs': '+ 140 €', 'living_area': '62 m²', 'rooms': '3', 'description': 'In der Leonhard-Frank-Straße / Max-Borsdorf-Straße wurde in den letzten Jahren ein GEBÄUDEENSEMBLE aus drei 5 - geschossigen WOHNBLÖCKEN der 80- er Jahre (bekannt als WBS 70) energieeffizient und zeitgemäß modernisiert. Im 2013 modernisierten Abschnitt der Leonard-Frank-Str.9-11a steht ab Juli wieder eine 3 Raum Wohnung zur Verfügung.', 'energy_usage': None, 'available': '01.07.20', 'extras': 'Balkon/ Terrasse\nKeller\nGarten/ -mitbenutzung\nWG-geeignet'}
        categories = self.immob_searcher.get_expose_categories(self.immobilienscout_expose)
        self.assertDictEqual(categories, check_categories)
        # del categories['parsed']
        # self.assertDictEqual(categories, check_categories)
    
    def test_immobilienscout_previews(self):
        """Tests all methods above on all preview elements"""
        
        check_titles = ['Schöne 3-Zwhg ca. 69m², Tageslichtbad und Laminatboden',
                'Helle 3-Raum-Wohnung mit offener Küche, Balkon, Tageslichtbad und PKW-Stellplatz',
                'I gemütliche 3-RW im Dachgeschoss I Parkett I Wannenbad I',
                'ZENTRUMSNAHE FAMILIENWOHNUNG MIT GEPFLEGTEM INNENHOF...',
                '3-Zi-EG-Whg mit Laminat, Dusche verfügbar nach Badsanierung',
                'Top 3-Raum-Dachgeschosswohnung mit EBK in Schönefeld zu vermieten',
                'LIVIA-IMMO.DE :-) +SUPER AUSBLICK! ERSTBEZUG+NEUBAU+3 ZIMMER+LOGGIA+FuBo-HEIZUNG',
                'Frisch renoviert im ruhigen Schönefeld',
                'Helle Dachgeschosswohnung mit Laminat und Duschbad!',
                'frisch renoviert, in einer beliebten Lage in Reudnitz',
                'Zentrumsnah - 3-Raum-Wohnung WE 05',
                'Schicke Familienwohnung im zentrum Südost',
                'ENERGIEeffizient | MODERN | GRÜNE Umgebung | KLASSE Infrastruktur | In KÜRZE zu haben',
                'Fällt Ihnen das Treppensteigen schwer?',
                '3-Zimmer-Wohnung in TOP Lage mit Balkon',
                'Erstbezug nach Renovierung *KEINTREPPENSTEIGEN',
                '*** Sanierte 3-Raumwohnung mit Balkon ***',
                '*** Bezugsfertige 3-Raumwohnung mit Balkon ***',
                '*** Bezugsfertige 3-Raumwohnung mit Balkon ***',
                'Ihr neues Zuhause in Schönefeld']
        titles = []
        check_preview_imgs = ['https://pictures.immobilienscout24.de/listings/0aca4653-6460-4e39-adee-b6389983a906-1127251492.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/ca326829-bc9d-4551-869e-70d3467b9266-1371852426.png/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/1bb2cc3b-756c-46f4-9b5e-bd79db776fa0-1370478128.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/49aa062b-e056-4a1a-ae22-8cb5bbabe10f-1374869455.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/6ce05ec2-26b5-4588-bae0-2d372b26f603-1366197305.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/c8958379-da5b-4d7f-a3eb-d7b56eb3088b-1367861979.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/b92c86ed-c3da-4916-85c7-0d68d84ede1a-1375955770.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/bbe51709-1bb7-458e-9d00-5dc1a55b35fd-1375795120.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/27f743a3-b512-42a0-9a3b-69154ff9ce75-1375322295.png/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/3ce75393-f0ac-4941-bbcd-c754f9e0f2ed-1375229060.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/644aa6dc-1efe-4528-bf46-5aa6af1ffb2a-1375175571.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/ebe37de9-3841-41a1-9e6e-0b11d99d18ce-1374779315.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/a5a4d3e6-6ebc-4012-8d95-2bcb7d0d6339-1374637383.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/a491422c-0b2a-49a1-a1b3-928644dd5849-1376100428.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/d34c622a-390a-41f5-8ed3-b00344474a46-1374142693.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/e9086570-81e5-45d2-8afc-8aa4aa159117-1374186314.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/24c2dcd0-d051-4ed8-ad3f-f5bf99546ec4-1373541448.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/8e059d5c-711b-48ed-ba34-8127b95482a0-1373541226.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/267b7fab-7b47-4bde-adb2-bcc6fc3c09f7-1373541126.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80',
            'https://pictures.immobilienscout24.de/listings/019ff08d-35ef-4624-80f4-2240f0be11d0-1376098853.jpg/ORIG/legacy_thumbnail/420x315/format/jpg/quality/80']
        preview_imgs = []

        check_addresses = ['Heinrichstr. 29, Reudnitz-Thonberg, Leipzig',
            'Schönefeld-Abtnaundorf, Leipzig',
            'Schirmerstraße 27, Anger-Crottendorf, Leipzig',
            'Rackwitzer-Straße 32c, Schönefeld-Abtnaundorf, Leipzig',
            'Ludwigstraße 92, Volkmarsdorf, Leipzig',
            'Schmidt-Rühl-Straße 23, Schönefeld-Abtnaundorf, Leipzig',
            'Volbedingstraße 17, Schönefeld-Abtnaundorf, Leipzig',
            'Friedrich-Wolf-Str. 10, Schönefeld-Ost, Leipzig',
            'Gorkistraße 82, Schönefeld-Abtnaundorf, Leipzig',
            'Mierendorffstraße 30, Anger-Crottendorf, Leipzig',
            'Johannisallee 18, Reudnitz-Thonberg, Leipzig',
            'Straße des 18. Oktober 35, Zentrum-Südost, Leipzig',
            'Leonhard-Frank-Straße 11, Sellerhausen-Stünz, Leipzig',
            'Stöckelstr. 17, Schönefeld-Abtnaundorf, Leipzig',
            'Stannebeinplatz 1, Schönefeld-Abtnaundorf, Leipzig',
            'Lazarusstr. 21, Schönefeld-Abtnaundorf, Leipzig',
            'Leonhard-Frank-Str. 56, Sellerhausen-Stünz, Leipzig',
            'Bästleinstr. 21, Schönefeld-Ost, Leipzig',
            'Bästleinstr. 3, Schönefeld-Ost, Leipzig',
            'Schwantesstr. 21, Schönefeld-Ost, Leipzig']
        addresses = []

        check_expose_srcs = ['https://example.org/expose/64607085',
            'https://example.org/expose/118873596',
            'https://example.org/expose/117001389',
            'https://example.org/expose/86961052',
            'https://example.org/expose/77570872',
            'https://example.org/expose/118117443',
            'https://example.org/expose/119668777',
            'https://example.org/expose/119642213',
            'https://example.org/expose/119529142',
            'https://example.org/expose/119509129',
            'https://example.org/expose/119502536',
            'https://example.org/expose/119435866',
            'https://example.org/expose/119414259',
            'https://example.org/expose/119360657',
            'https://example.org/expose/119332040',
            'https://example.org/expose/119329174',
            'https://example.org/expose/119195176',
            'https://example.org/expose/119195150',
            'https://example.org/expose/119195141',
            'https://example.org/expose/118949905']
        expose_srcs = []
        for pre in self.previews_immob:
            titles.append(self.immob_searcher.get_title(pre, self.immob_searcher.title_sel))
            preview_imgs.append(self.immob_searcher.get_preview_img(pre, self.immob_searcher.preview_img_sel))
            addresses.append(self.immob_searcher.get_address(pre, self.immob_searcher.address_sel))
            expose_srcs.append(self.immob_searcher.get_expose_src(pre))
        self.assertListEqual(titles, check_titles)
        self.assertListEqual(preview_imgs, check_preview_imgs)
        self.assertListEqual(addresses, check_addresses)
        self.assertListEqual(expose_srcs, check_expose_srcs)

    def test_immowelt_previews(self):
        """Tests all methods above on all preview elements"""
        
        check_titles = ['3-Zimmerwohnung im Leipziger Osten',
        '* tolle 3-Raumwohnung über 2 Etagen sofort bezugsfertig *',
        '++ Schicke 3-Raumwohnung im Erdgeschoss in Zentrumsnähe ++',
        'Schöne 3-Raum-Wohnung mit Balkon / Erstbezug nach Ausbau!']
        titles = []
        check_preview_imgs = ['https://media-pics2.immowelt.org/9/5/b/6/622df664effd4029a5a08b0e26016b59.jpg',
            'https://media-pics2.immowelt.org/b/c/b/6/548fbdfff11a44baa7757ede397b6bcb.jpg',
            'https://media-pics2.immowelt.org/9/0/b/6/6bfc14f5e62542fd9b478d85f0dc6b09.jpg',
            'https://media-pics1.immowelt.org/3/7/7/7/f821b235932146f3b7c845ff89a97773.jpg']
        preview_imgs = []

        check_addresses = ['04318 Leipzig (Sellerhausen-Stünz), Permoserstr. 24 2,1 km',
                '04315 Leipzig (Neustadt-Neuschönefeld), Eisenbahnstraße 11 2,2 km',
                '04315 Leipzig (Neustadt-Neuschönefeld), Eisenbahnstraße 11 2,2 km',
                '04347 Leipzig (Schönefeld-Ost), Schwantesstr. 31 2,5 km']
        addresses = []

        check_expose_srcs = ['https://example.org/expose/2vtbg4e',
            'https://example.org/expose/2v7bv47',
            'https://example.org/expose/2ua3z4w',
            'https://example.org/expose/2vax643?slide=1&bc=12']
        expose_srcs = []
        for pre in self.previews_immow:
            titles.append(self.immow_searcher.get_title(pre, self.immow_searcher.title_sel))
            preview_imgs.append(self.immow_searcher.get_preview_img(pre, self.immow_searcher.preview_img_sel))
            addresses.append(self.immow_searcher.get_address(pre, self.immow_searcher.address_sel))
            expose_srcs.append(self.immow_searcher.get_expose_src(pre))
        self.assertListEqual(titles, check_titles)
        self.assertListEqual(preview_imgs, check_preview_imgs)
        self.assertListEqual(addresses, check_addresses)
        self.assertListEqual(expose_srcs, check_expose_srcs)
    
    def test_immonet_previews(self):
        """Tests all methods above on all preview elements"""
        
        check_titles = ['hochwertige Wohnung mit Balkon in Schönefeld', 'Balkon + Loggia - 3-Raum-Wohung im schönen Fliederhof', 'Familienfreundlich wohnen', 'Moderne 3-Raum-Wohnung mit Einbauküche im Musikviertel', 'Wohnanlage für Alt und Jung', 'neu ausgebaute Wohnung mit Balkon', 'Wohnen im schönen Fliederhof - 3-Raum-Wohung in der...', '3-Raumwohnung am Stephaniepark', 'I gemütliche 3-RW im Dachgeschoss I Parkett I Wannenba...', 'Frisch renoviert im ruhigen Schönefeld', '!!!GEMÜTLICHE MAISONETTE-DACHGESCHOSSWOHNUNG IN UNI-NÄ...', '3-Zimmerwohnung im Leipziger Osten', 'Helle 3 Zimmerwohnung im Herzen von Leipzig', 'Kleine 3 - Zimmer - Wohnung', 'Familienfreundlich wohnen', 'Fällt Ihnen das Treppensteigen schwer?', 'Moderne 3-Raum-Wohnung im Herzen des Musikviertel', 'Erstbezug nach Renovierung *KEINTREPPENSTEIGEN', '*** Bezugsfertige 3-Raumwohnung mit Balkon ***', '3-Zimmer mit Balkon *saniert*', 'I gemütliche 3-RW im Dachgeschoss I Parkett I Wannenba...', 'Schönefeld-Abtnaundorf * tolle 3 Zi.-Whg. mit Balkon*...', '3-Raum-Wohnung mit Balkon in Schönefeld', 'Ihr neues Zuhause in Schönefeld', 'Citynah wohnen!', 'Zweitbezug in TOP-Lage!']
        titles = []
        check_preview_imgs = ['https://i.immonet.de/94/62/05/637946205_280x374.jpg', 'https://i.immonet.de/89/03/90/637890390_280x210.jpg', 'https://i.immonet.de/45/01/91/637450191_280x187.jpg', 'https://i.immonet.de/45/01/14/637450114_280x187.jpg', 'https://i.immonet.de/44/98/02/637449802_280x166.jpg', 'https://i.immonet.de/44/95/43/637449543_279x210.jpg', 'https://i.immonet.de/32/64/97/637326497_280x210.jpg', 'https://i.immonet.de/21/77/84/637217784_280x186.jpg', 'https://i.immonet.de/37/80/20/636378020_280x210.jpg', 'https://i.immonet.de/11/33/33/636113333_280x187.jpg', 'https://i.immonet.de/46/43/86/635464386_280x374.jpg', 'https://i.immonet.de/08/10/94/635081094_280x210.jpg', 'https://i.immonet.de/96/97/57/634969757_280x210.jpg', 'https://i.immonet.de/88/66/90/634886690_280x373.jpg', 'https://i.immonet.de/59/33/94/634593394_280x187.jpg', 'https://i.immonet.de/44/99/27/637449927_280x188.jpg', 'https://i.immonet.de/96/35/29/637963529_280x187.jpg', 'https://i.immonet.de/74/03/11/636740311_280x374.jpg', 'https://i.immonet.de/21/90/21/637219021_280x210.jpg', 'https://i.immonet.de/50/87/65/633508765_280x187.jpg', 'https://i.immonet.de/44/39/00/633443900_280x210.jpg', 'https://i.immonet.de/33/04/28/633330428_280x210.jpg', 'https://i.immonet.de/38/95/17/632389517_280x187.jpg', 'https://i.immonet.de/38/94/52/632389452_280x187.jpg', 'https://i.immonet.de/38/94/21/632389421_280x208.jpg', 'https://i.immonet.de/82/71/60/636827160_280x210.jpg']
        preview_imgs = []
        # immonet previes have no addresses
        check_addresses = [None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None]
        addresses = []
        check_expose_srcs = ['https://example.org/angebot/40899848', 'https://example.org/angebot/40896669', 'https://example.org/angebot/40877978', 'https://example.org/angebot/40877975', 'https://example.org/angebot/40877961', 'https://example.org/angebot/40877954', 'https://example.org/angebot/40872071', 'https://example.org/angebot/40865230', 'https://example.org/angebot/40818532', 'https://example.org/angebot/40804732', 'https://example.org/angebot/40775033', 'https://example.org/angebot/40755407', 'https://example.org/angebot/40749914', 'https://example.org/angebot/40746535', 'https://example.org/angebot/40734604', 'https://example.org/angebot/40734596', 'https://example.org/angebot/40734581', 'https://example.org/angebot/40722089', 'https://example.org/angebot/40692200', 'https://example.org/angebot/40679359', 'https://example.org/angebot/40676290', 'https://example.org/angebot/40671274', 'https://example.org/angebot/40618969', 'https://example.org/angebot/40618964', 'https://example.org/angebot/40618960', 'https://example.org/angebot/40585320']
        expose_srcs = []
        for pre in self.previews_immon:
            titles.append(self.immon_searcher.get_title(pre))
            preview_imgs.append(self.immon_searcher.get_preview_img(pre))
            addresses.append(self.immon_searcher.get_address(pre))
            expose_srcs.append(self.immon_searcher.get_expose_src(pre))
        self.assertListEqual(titles, check_titles)
        self.assertListEqual(preview_imgs, check_preview_imgs)
        self.assertListEqual(addresses, check_addresses)
        self.assertListEqual(expose_srcs, check_expose_srcs)


if __name__ == "__main__":
        unittest.main()