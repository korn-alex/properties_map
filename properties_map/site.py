from requests_html import HTMLSession, HTML
import inspect, json
from properties_map.apartment import DB, ApartmentSearcher, ExposeEntry, PreviewEntry
from properties_map.osm import ReverseCoder


class SiteData:
    """Class for loading and holding fetched website and expose data from a database."""
    def __init__(self, name:str, website_data_db:DB):
        """Inits site data and its database.

        Parameters
        ----------
        name : str,
            website name in database
        
        website_data_db : DB,
            database holding html data from result pages and exposes.
        """
        self.name = name
        self.db = website_data_db
        # self.db.c.execute(f'select distinct html,url from web where website="{name}" group by url')
        # _pages = self.db.c.fetchall()
        # self.main_pages = [HTML(html=p[0],url=p[1]) for p in _pages]
        self.main_pages = list()
        # self.db.c.execute(f'select distinct html,url from preview where website="{name}" group by url')
        # _previews = self.db.c.fetchall()
        # self.previews = [HTML(html=p[0],url=p[1]) for p in _previews]
        self.preview_entries = self.db.get_data_entries(self.db.templates.preview, PreviewEntry, sql_extra=f'where website="{name}"')
        if not self.preview_entries:
            self.preview_entries = []
        self.expose_entries = self.db.get_data_entries(self.db.templates.expose, ExposeEntry, sql_extra=f'where website="{name}"')
        if not self.expose_entries:
            self.expose_entries = []
        # self.db.c.execute(f'select distinct html,url from expose where website="{name}" group by url')
        # _exposes = self.db.c.fetchall()
        # self.exposes = [HTML(html=p[0],url=p[1]) for p in _exposes]
    
    def __repr__(self):
        return f'SiteData(name="{self.name}", main_pages=[{len(self.main_pages)}], preview_entries=[{len(self.preview_entries)}], expose_entries=[{len(self.expose_entries)}])'


class SiteManager:
    """Manages databases for `SiteData` and `ApartmentSearcher`.
    """
    def __init__(self, site_db:DB, apartment_db:DB, **kwargs):
        self.session = HTMLSession()
        self.site_db = site_db
        self.apartment_db = apartment_db
        for name,searcher_class in kwargs.items():
            site_data = SiteData(name, self.site_db)
            apartment_searcher = searcher_class(self.session, apartment_db.templates, name)
            setattr(self, f'{name}_data', site_data)
            setattr(self, f'{name}_searcher', apartment_searcher)
        self.data_members = None
        self.searcher_members = None
        self.new_preview_entries = None
        self.new_expose_entries = None
        self.new_ids = None
        self._load_data_members()
        self._load_searcher_members()
        self.apartments = list()
        self.images = list()
        # self._load_db_data()
        # self.update_site_db()
        # self._get_new_expose_srcs()

    def _load_data_members(self) -> list:
        """Searches _data attributes set in kwargs and 
        sets them to `self.data_members`.
        
        Returns
        ------
        data_members : list,
            attributes which were set in kwargs.
        """
        _members = inspect.getmembers(self)
        # names = [n[0] for n in _members if n[1] == SiteData]
        members = [n[1] for n in _members if n[1].__class__ == SiteData]
        # members = [getattr(self, m) for m in names]
        self.data_members = members

    def _load_searcher_members(self) -> list:
        """Searches _searcher attributes set in kwargs and 
        sets them to `self.searcher_members`.
        
        Returns
        ------
        searcher_members : list,
            attributes which were set in kwargs.
        """
        _members = inspect.getmembers(self)
        members = [n[1] for n in _members if issubclass(n[1].__class__, ApartmentSearcher)]
        # members = [getattr(self, m) for m in names]
        self.searcher_members = members

    def _load_db_data(self):
        # self._load_db_previews()
        # self._load_db_exposes()
        self._load_db_apartments()

    # def _load_db_previews(self):
    #     """Loads a previews to `self.searcher_member.preview_elements`.
    #     """
    #     self.site_db.c.execute('select')
    #     for dm,sm in zip(self.data_members,self.searcher_members):
    #         for page in dm.main_pages:
    #             sm.get_preview_elements(page)

    # def _load_db_exposes(self):
    #     """Loads a list of `tuple(preview, expose)` from `searcher_members`
    #     to `self.data_member.data`.
    #     """
    #     for dm,sm in zip(self.data_members, self.searcher_members):
    #         dm.data = []
    #         for preview in sm.preview_elements:
    #             src = sm.get_expose_src(preview)
    #             self.site_db.c.execute(f'select html from expose where url="{src}"')
    #             html = self.site_db.c.fetchone()
    #             if html is None:
    #                 continue
    #             expose = HTML(html=html[0],url=src)
    #             data = (preview, expose)
    #             dm.data.append(data)

    def _load_db_apartments(self):
        """Loads apartments with images from database to 
        `self.apartments` and `self.images`.
        """
        # apartment_id = 0
        # image_id = 0
        # new_db = []
        image_id = 0
        for dm,sm in zip(self.data_members, self.searcher_members):
            sm.exposes = []
            for prev,exp in zip(dm.preview_entries,dm.expose_entries):
                preview = prev.make_html()
                expose = exp.make_html()
                apartment = sm.get_apartment(prev.id, image_id, preview, expose)
                self.apartments.append(apartment)
                image_id = apartment.images[-1].id + 1
                self.images += apartment.images

    def update_site_db(self):
        """Sets `self.new_preview_entries`, `self.new_expose_entries`,
        `self.new_ids` and inserts data into `self.site_db`
        """
        preview_exposes = self._get_new_preview_exposes()
        self.preloaded_data = preview_exposes
        if not preview_exposes:
            print('no new exposes')
            # self.new_ids = []
            return
        else:
            print(f'found {len(preview_exposes)} new exposes')
        self.new_expose_entries = []
        self.new_preview_entries = []
        self.new_ids = []
        web_template = self.site_db.templates.web
        preview_template = self.site_db.templates.preview
        expose_template = self.site_db.templates.expose
        p_id = self.site_db.get_last_id('preview')
        for preview, expose, search_member, data_member in preview_exposes:
            preview_entry = PreviewEntry(preview_template,id=p_id,website=search_member.name,url=preview.url,html=preview.pq.html())
            expose_entry = ExposeEntry(expose_template,id=p_id,website=search_member.name,url=expose.url,html=expose.pq.html())
            data_member.preview_entries.append(preview_entry)
            data_member.expose_entries.append(expose_entry)
            self.new_preview_entries.append(preview_entry)
            self.new_expose_entries.append(expose_entry)
            self.new_ids.append(p_id)
            p_id += 1
        self.site_db.insert_many(self.new_preview_entries)
        self.site_db.insert_many(self.new_expose_entries)
        print(f'{len(self.new_preview_entries)} new exposes added')
        return f'{len(self.new_preview_entries)} neue Wohnungen gefunden.'
    
    def _missing_apartment_ids(self):
        """Checks if site_db has new data but misses apartment_db entries

        Returns
        -------
        list
            new_preview_ids
        """
        self.apartment_db.c.execute('select id from Apartment')
        apartment_ids = self.apartment_db.c.fetchall()
        _new_ids = [f'"{i[0]}"' for i in apartment_ids]
        # new_ids = [i[0] for i in apartment_ids]
        sql_ids = ','.join(_new_ids)
        self.site_db.c.execute(f'select id from preview where id NOT IN ({sql_ids})')
        site_ids = self.site_db.c.fetchall()
        if not site_ids:
            return
        else:
            new_ids = [i[0] for i in site_ids]
            return new_ids

    def update_apartment_db(self):
        # _new_ids = [f'"{i[0]}"' for i in site_ids]
        # sql_ids = ','.join(_new_ids)
        # sql = f'select p.id, p.website, p.url, p.html, e.url, e.html from preview as p, expose as e where p.id IN ({sql_ids})'
        # self.site_db.c.execute(sql)
        # to_parse = self.site_db.c.fetchall()
        # self.site_db.get_data_entries()
        if not self.new_ids:
            new_ids = self._missing_apartment_ids()
            if new_ids:
                self.new_ids = new_ids
            else:
                print('no new ids in site_db')
                return
        ap_template = self.apartment_db.templates.apartment
        img_template = self.apartment_db.templates.image
        apartments = []
        images = []
        img_start_id = self.apartment_db.get_last_id(img_template.table.name)
        # for ap_id,p_website,p_url,p_html,e_url,e_html in to_parse:
        for dm,sm in zip(self.data_members,self.searcher_members):
            for prev, exp in zip(dm.preview_entries,dm.expose_entries):
                if dm.name != prev.website:
                    continue
                if prev.id not in self.new_ids:
                    continue
                # preview = HTML(html=prev.html,url=prev.url)
                # expose = HTML(html=expose.html,url=expose.url)
                preview = prev.make_html()
                expose = exp.make_html()
                try:
                    apartment_entry = sm.get_apartment(prev.id, img_start_id, preview, expose=expose)
                    if not apartment_entry:
                        print(f'missing entry. id={exp.id}: {exp.url}')
                        continue
                    apartments.append(apartment_entry)
                    images += apartment_entry.images
                    img_start_id = images[-1].id + 1
                except:
                    print(f'parsing failed. id={exp.id}: {exp.url}')
                    continue
        self._get_coordinates(apartments)
        self.apartment_db.insert_many(apartments)
        self.apartment_db.insert_many(images)
        print(f'{len(apartments)} apartments added')
        print(f'{len(images)} images added')
        self.new_ids = []
        return f'{len(apartments)} Wohnungen hinzugefügt.'

    def _get_coordinates(self, apartments):
        self.reverse_coder = ReverseCoder(apartments)
        self.reverse_coder.prepare()
        self.reverse_coder.search()
        features = self.reverse_coder.nodes + self.reverse_coder.areas
        for apartment_ids, feature in features:
            coordinate = self.reverse_coder.get_coordinate(feature[0])
            if not coordinate:
                print(f'no coordinates: {apartment_ids} - {feature}',)
                continue
            coordinate_text = json.dumps(coordinate)
            for ap_id in apartment_ids:
                ap = self.reverse_coder.apartment_dict.get(ap_id)
                ap.coordinates = coordinate_text
            # print((apartment_ids, coordinate_text))
        return apartments

    def _get_new_preview_exposes(self) -> set:
        """Searches for new expose sources which are not in database.

        Returns
        -------
        list
            `[(preview:Element, expose:Element, search_member:ApartmentSearcher, data_member:SiteData), ...]`
        """
        preview_exposes = []
        for dm,sm in zip(self.data_members, self.searcher_members):
            name = sm.name
            sm.preload()
            # self.site_db.c.execute(f'SELECT DISTINCT url FROM expose WHERE website=="{name}"')
            # _db_srcs = self.site_db.c.fetchall()
            # db_srcs = [n[0] for n in _db_srcs]
            # if len(_db_srcs) == 0:
            #     continue
            # for page in dm.main_pages:
            db_srcs = [e.url for e in dm.expose_entries]
            for page in sm.main_pages:
                print('getting previews, exposes from ',page.url)
                previews = sm.get_preview_elements(page)
                for preview in previews:
                    src = sm.get_expose_src(preview)
                    if src not in db_srcs:
                        expose = sm.get_expose_element(src)
                        if not expose:
                            print('no expose',src)
                            return
                        preview_exposes.append((preview, expose, sm, dm))
                        # break
                # break
            # break
        return preview_exposes
