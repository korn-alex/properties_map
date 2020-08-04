from requests_html import HTMLSession, HTMLResponse, HtmlElement, HTML, Element
from dataclasses import dataclass, field
from pathlib import Path
import base64, datetime, sqlite3, re, json, geojson
from typing import NamedTuple
from properties_map.template import Template, Column, ApartmentTemplateCollection

class ReturnType:
    """Class for easier use of return_type in Selector.
    
    Parameters
    --------
    `element` : str
    
    `text`: str
    
    `attribute` : str
    
    `custom_name` : str

    `all` : str
    """
    element='element'
    text='text'
    attribute='attribute'
    custom_name='custom_name'
    all='all'

    @classmethod
    def empty_dict(cls):
        """Makes an empty dictionary of its values.

        Returns
        -------
        dict
            empty_dict
        """
        empty = {'element':[],
                'text':[],
                'attribute':[],
                'custom_name':[],
                'all':[]
                }
        return empty


class Selector:
    def __init__(self, find_selector, custom_name:str=None,
                return_type:ReturnType=ReturnType.all,
                first:bool=True, 
                clean:bool=True, containing:str=None, 
                text:bool=False, attributes:dict=None, **kwargs):
        """Creates easy selector to use in html.find().

        Parameters
        ----------
        find_selector : `str`
            html.find() string
        
        custom_name : `str`, optional
            To give a custom name to the found element, by default `None`
                    
        return_type : `str`
            Returns only this type, by default `all`
        
        first : `bool`, optional
            Argument for find(), returns first result, by default `True`
        
        clean : `bool`, optional
            Argument for find(), sanitizes text from style tags, by default `True`
        
        containing : `str`, optional
            Text to search in element, by default None
        
        text : `bool`, optional
            To return text from the element, by default False

        Optional Parameters
        ---------
        kwargs : {key : new_key_name}
            Searches for `attribute` as key in element.
            Returns found value with `new_key_name` as name.
        """
        self.find = find_selector
        self.custom_name = custom_name
        self.return_type = return_type
        self.first = first
        self.clean = clean
        self.containing = containing
        self.text = text
        self.attrs = attributes
        self.kwargs = {'first':self.first,
            'clean':self.clean,
            'containing':self.containing}
        # for attr, val in kwargs.items():
        #     setattr(self, attr, val)
        #     self.attrs[attr] = val
    
    def __repr__(self):
        strings = []
        for k,v in vars(self).items():
            _v = f"'{v}'" if type(v) == str else v
            strings.append(f'{k}={_v}')
        attributes = ', '.join(strings)
        return f'{self.__class__.__name__}({attributes})'

@dataclass
class SelectorDict:
    key:Selector
    value:Selector


class DatabaseEntry:
    """Base for Apartment and Image class."""
    def __init__(self, template:Template, **kwargs):
        self._template = template
        self._re:re.Pattern = re.compile('\d+([,.]\d+)?')
        self._re2:re.Pattern = re.compile('\d+[.]\d+,\d+')
        for col in template.column:
            setattr(self, col.name, None)
        for k,v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        strings = []
        for k,v in vars(self).items():
            if re.fullmatch('_template|_re|_re2',k):
                continue
            if type(v) == str:
                v = v.replace('\n','').replace('\t','').replace('\r','')
                if len(v) > 60:
                    _v = f"'{v[:56]} ...'"
                else:
                    _v = f"'{v}'"
            else:
                _v = v
            strings.append(f'{k}={_v}')
        attributes = '\n\t' + ',\n\t'.join(strings)
        return f'{self.__class__.__name__}({attributes})'

    def _valid(self):
        """Checks if column names from template are in this instance.
        
        If valid, nothing is raised.

        Raises
        ------
        AttributeError
            column_name not in this instance.
        """
        cols = self._template.column_names()
        for attr in cols:
            if not hasattr(self, attr):
                raise AttributeError(f'"{attr}" not in {self.__repr__()}')
    
    def parse_price(self, string:str=''):
        """Parses price using self._re pattern.

        Parameters
        ----------
        string : str, optional
            string to be parsed, by default ''

        Returns
        -------
        float
            parsed_price or 0 if no value found
        """
        if string is None:
            return 0
        _s = self._re2.search(string)
        if _s:
            parsed = _s.group().replace('.','').replace(',','.')
            return float(parsed)
        else:
            _s = self._re.search(string)
        if _s:
            parsed = _s.group().replace(',','.')
            return float(parsed)
        else:
            return 0

    def get_insert_values(self):
        """Makes attributes ready for database insert.

        Type conversion is based on self._template.

        Returns
        -------
        tuple
            entry_values
        """
        self._valid()
        entry = []
        for col in self._template.column:
            value = getattr(self, col.name)
            value = json.dumps(value) if type(value) == dict else value
            if col.type.upper() in ['INT','REAL'] and value is None:
                value = 0
            elif col.type.upper() == 'REAL' and type(value) == str:
                value = self.parse_price(value)
            # elif col.type.upper() == 'INT' and type(value) == str and value:
            #     value = int(value)
            elif col.type.upper() == 'INT' and type(value) == bool:
                value = 1 if value == True else 0
            entry.append(value)
            # print(f'{col.name}:{value} ({type(value)})')
        return tuple(entry)

    def get_feature(self):
        keys = self._template.column_names()
        if self.coordinates:
            point = geojson.Point(coordinates=json.loads(self.coordinates))
        else:
            return
        props = {}
        for k in keys:
            value = getattr(self, k)
            if k == 'parsed' and value:
                values = json.loads(value)
                props.update(values)
                continue
            props[k] = value
        feature = geojson.Feature(self.id, geometry=point, properties=props)
        return feature
        
    def get_json(self):
        props = self.get_dict()
        return json.dumps(props)
    
    def get_dict(self):
        keys = self._template.column_names()
        props = {}
        for k in keys:
            value = getattr(self, k)
            props[k] = value
        return props



# @dataclass
class Image(DatabaseEntry):
    def __init__(self, template:Template, **kwargs):
        super().__init__(template, **kwargs)
    # id:int = 0
    # src:str = ''
    # caption:str = ''
    # is_floorplan:bool = False
    # img_bytes:bytes = field(default_factory=bytes)
    # apartment_id:int = 0


# @dataclass
class Apartment(DatabaseEntry):
    def __init__(self, template:Template, **kwargs):
        super().__init__(template, **kwargs)
    # id:int = 0
    # title:str = ''
    # address:str = ''
    # preview_image:str = ''
    # expose:str = ''
    # list_page_url:str = ''
    # total_rent:str = ''
    # cold_rent:str = ''
    # add_costs:str = ''
    # deposit:str = ''
    # living_area:str = ''
    # rooms:str = ''
    # images:[dict] = field(default_factory=list)
    # # optional and additional
    # coordinates:dict = field(default_factory=dict)
    # description:str = ''
    # energy_usage:str = ''
    # available:str = ''
    # extras:dict = field(default_factory=dict)
    # parsed:dict = field(default_factory=dict)    


class WebEntry(DatabaseEntry):
    def __init__(self, template:Template, **kwargs):
        super().__init__(template, **kwargs)

class ExposeEntry(DatabaseEntry):
    def __init__(self, template, **kwargs):
        super().__init__(template, **kwargs)
    
    def make_html(self):
        return HTML(html=self.html, url=self.url)

class PreviewEntry(DatabaseEntry):
    def __init__(self, template, **kwargs):
        super().__init__(template, **kwargs)
    
    def make_html(self):
        return HTML(html=self.html, url=self.url)
        
@dataclass
class ApartmentSearcher:
    session:HTMLSession
    templates:ApartmentTemplateCollection
    name:str
    # apartment_template:Template
    # image_template:Template
    url:str = ''
    page_param:str=''
    page_el_sel:Selector=None
    main_pages:list = field(default_factory=list)

    element_sel:str=''
    title_sel:str=''
    address_sel:str=''
    preview_img_sel:str=''
    expose_sel:str=''
    extras_el_sel:str=''
    exposes:list = field(default_factory=list)
    # pice_r = re.compile('\ddd')
    missing_info:list = field(default_factory=list)
    preview_elements:list = field(default_factory=list)

    def __repr__(self):
        return f'{self.__class__.__name__}(url="{self.url}")'

    def _clean_text(self, text:str) -> str:
        """Removes \xa0 and \xad from text.

        Parameters
        ----------
        text : str
            text to be cleaned

        Returns
        -------
        str
            clean_text
        """
        return text.replace('\xad','').replace('\xa0','')

    def parse_element(self, element, selector):
        """Parses a single element with given criteria from selector.

        Parameters
        ----------
        element : Element
            html_element
        selector : Selector
            selector for this element

        Returns
        -------
        `list` or `str`
            Depends on `selector.return_type` and `selector.first`
        """
        # data = []
        data = {}
        el = element.find(selector.find, **selector.kwargs)
        if not el:
            return None, None
        # data['element'] = el
        if selector.text:
            text = el.text
            # data['text'] = text
            data['text'] = text
            # print(text)
        if selector.attrs:
            attributes = {}
            for at,val in selector.attrs.items():
                found_att = el.attrs.get(at)
                attributes[val] = found_att
            # data['attributes'] = attributes
            data['attribute'] = attributes
        if selector.custom_name:
            # data['name'] = selector.custom_name
            data['custom_name'] = selector.custom_name
        if selector.return_type == ReturnType.all:
            # return_data = []
            # for t,v in data.items():
            #     return_data.append(v)
            # return return_data
            return el, data
        elif selector.return_type == ReturnType.element:
            return el, None
        else:
            return el, data[selector.return_type]
        
    def parse_selectors(self, element, selectors:list):
        info = ReturnType.empty_dict()
        el = None
        key_el = None
        val_el = None
        for sel in selectors:
            if el is None:
                el = element
            # if type(sel) == list:
            #     grouped_info = []
            #     for se in sel:
            #         _, *p = self.parse_element(el, se)
            #         if len(p) == 1:
            #             grouped_info.append(p[0])
            #         elif not p:
            #             continue
            #         else:
            #             grouped_info.append(p)                    
            #     info.append(grouped_info)
            if type(sel) == SelectorDict:
                if sel.return_type == ReturnType.all:
                    key_el, _key, *_ = self.parse_element(el, sel.key)
                    val_el, _val, *_ = self.parse_element(el, sel.value)
                    _d = {_key:_val}
                    # info.append(_d)
                    return _d
                # _k = self.parse_element(el, sel.key)
                # _v = self.parse_element(el, sel.value)
                # _d = {_k['text']:_v['text']}
            else:
                return_type = sel.return_type
                el, p = self.parse_element(el, sel)
                if not p:
                        continue
                if return_type == ReturnType.all:
                    for k in info:
                        info[k].append(p[k])
                elif return_type == ReturnType.element:
                    continue
                else:
                    info[return_type].append(p)
        # SelectorDict is always last, its returned earlier no need to check
        # if key_el is not None and val_el is not None:
        #     return [key_el, val_el], el
        if return_type == ReturnType.all:
            return el, info
        else:
            return el, info[return_type]

    def preload(self, first_page:HTML=None, test=False) -> HTML:
        """Requests all pages with the previews. Stores found pages
        in `self.main_pages` and returns it.

        Parameters
        -------
        first_page : HTML, by default None
            Will not load first page with session if the first page is given.
    
        test : bool
            If True, no session.get will be called and `first_page` must be given.
            Stores url's in `result_list`
        
        Returns
        -------
        list
            `result_list`=[page_1.html, ...]
        """
        print(f'preloading {self.__class__.__name__}')
        if test:
            print(f'{self.__class__.__name__}.preload(first_page={first_page}) in testmode.')
            if not first_page:
                raise AttributeError(f'first_page argument must be HTML if testing.')
        results = []
        page = 1
        first_page_url = self.url.format(f'{self.page_param}={page}')
        if not first_page:
            first_page_response = self.session.get(first_page_url)
            if first_page_response.status_code != 200:
                print(f'{first_page_url} didnt load properly.')
                return None
            first_page = first_page_response.html
        pages = self.get_pages(first_page, self.page_el_sel)
        results.append(first_page)
        if pages > 1:
            for p in range(2, pages+1):
                url = self.url.format(f'{self.page_param}={p}')
                if test:
                    results.append(url)
                    page += 1
                    continue
                next_page = self.session.get(url)
                if next_page.status_code != 200:
                    print(f'{url} didnt load properly.')
                    results.append(None)
                    page += 1
                    continue
                results.append(next_page.html)
                page += 1
        self.main_pages = results[:]
        return results
    
    def get_pages(self, main_page:HTML, selectors:list=None):
        """Gets number of pages on main page.

        Parameters
        ----------
        main_page : HTML
            page_html
        
        selectors : list
            Selectors for the pages container.

        Returns
        -------
        int
            page_number
        """
        if not selectors:
            selectors = self.page_el_sel
        elements, _ = self.parse_selectors(main_page, selectors)
        _p = elements[-1].text
        pages = int(_p)
        if not pages:
            return
        else:
            return pages

    def get_preview_elements(self, main_page:HTML, selectors:list=None) -> list:
        """Searches preview apartments in main_page. 
        Stores its list in `self.previews` and returns it.

        Parameters
        ----------
        main_page : HTML
            Page with apartment results.
        
        selectors : list, optional
            selectors to find apartment elements, by default takes `self.element_sel`

        Returns
        -------
        list
            previews=[Element, ...]
        """
        if not selectors:
            selectors = self.element_sel
        elements, _ = self.parse_selectors(main_page, self.element_sel)
        self.preview_elements += elements[:]
        return elements

    def get_title(self, preview:Element, selectors:list=None):
        """Searches title in the preview element.

        Parameters
        ----------
        preview : Element
            Page with apartment results.
        
        selectors : list, optional
            selectors to find title, by default takes `self.title_sel`

        Returns
        -------
        str
            title
        """
        if not selectors:
            selectors = self.title_sel
        element, title = self.parse_selectors(preview, self.title_sel)
        if not title:
            return None
        else:
            new = title[0][:3]
            if new == 'NEU':
                title = title[0][3:].strip()
            else:
                title = title[0]
            return title

    def get_preview_img(self, preview:Element, selectors:list=None):
        """Searches preview image in the preview element.

        Parameters
        ----------
        preview : Element
            Page with apartment results.
        
        selectors : list, optional
            selectors to find preview image, by default takes `self.preview_img_sel`

        Returns
        -------
        str
            preview image
        """
        if not selectors:
            selectors = self.preview_img_sel
        element, preview_img = self.parse_selectors(preview, self.preview_img_sel)
        if not preview_img:
            return None
        else:
            return preview_img[0]['src']
    
    def get_address(self, preview:Element, selectors:list=None):
        """Searches address in the preview element.

        Parameters
        ----------
        preview : Element
            Page with apartment results.
        
        selectors : list, optional
            selectors to find address, by default takes `self.address_sel`

        Returns
        -------
        str
            address
        """
        if not selectors:
            selectors = self.address_sel
        element, address = self.parse_selectors(preview, self.address_sel)
        if not address:
            return None
        else:
            return address[0]

    def get_expose_src(self, preview:Element):
        """Searches expose url in the preview element.

        Parameters
        ----------
        preview : Element
            Page with apartment results.

        Returns
        -------
        str
            expose_url
        """
        expose, *_ = preview.absolute_links
        if not expose:
            return None
        else:
            return expose

    def get_expose_element(self, expose_src:str) -> HTML:
        """Requests expose of apartment.

        Parameters
        ----------
        expose_src : str
            Url of expose page, `self.session.get()` will be called.

        Returns
        -------
        HTML
            expose
        """
        expose = self.session.get(expose_src)
        _availablility = ['Die aufgerufene Immobilie ist bereits vergeben oder wurde zwischenzeitlich vom Anbieter entfernt',
                            'Objekt nicht mehr verfügbar.']
        if expose.status_code != 200:
            raise Exception(f'get("{expose_src}") didnt return a valid response')
        for av in _availablility:
            if expose.html.search(av):
                print(av)
                self.missing_info.append({'not_available':expose_src})
                return None
        return expose.html

    def get_apartment(self, apartment_id:int, image_start_id:int, preview:Element, expose:Element=None):
        """Loads all data from a single preview and its expose.

        Parameters
        ----------
        db_id : int,
            id for db entry
        
        preview : Element,
            preview element of an apartment    

        expose : Element, default None,
            if given, no session get request will be called

        Returns
        -------
        Apartment
            apartment_instance
        """
        title = self.get_title(preview)
        preview_img = self.get_preview_img(preview)
        address = self.get_address(preview)
        expose_src = self.get_expose_src(preview)
        if not expose:
            expose = self.get_expose_element(expose_src)
            if not expose:
                return None
        self.exposes.append(expose)
        categories = self.get_expose_categories(expose)
        if 'address' in categories:
            address = categories['address']
        if 'deposit' not in categories:
            categories['deposit'] = None
            print('missing deposit',expose_src)
        _images = self.get_images(expose)
        db_images = []
        for img in _images:
            if not img:
                print('no img',expose_src)
                self.missing_info.append({'image':expose,'src':expose_src})
                db_images.append(None)
                break
            # self.session.get(img['src'])
            img['id'] = image_start_id
            img['apartment_id'] = apartment_id
            img['img_bytes'] = 0
            image = Image(self.templates.image, **img)
            db_images.append(image)
            image_start_id += 1
        categories['images'] = db_images
        categories['id'] = apartment_id
        categories['title'] = title
        categories['preview_image'] = preview_img
        categories['address'] = address
        categories['expose'] = expose_src
        if not categories['address']:
            print('missing address',expose_src)
            self.missing_info.append({'address':expose})
        if 'parsed' not in categories:
            categories['parsed'] = None
        apartment = Apartment(self.templates.apartment, **categories)
        if len(apartment.images) < 1:
            print('no images',expose_src)
            self.missing_info.append({'image':expose,'src':expose_src})
            db_images.append(None)
            raise Exception('no images')
        return apartment

    def get_apartments(self, apartment_start_id:int, image_start_id:int):
        """Loads apartment data from `self.main_pages`.

        Parameters
        ----------
        start_id : int,
            id from where db entries start

        template : Template,
            template of this instance for making new Apartmant instances.

        Returns
        -------
        list
            [Apartment_instance, ...]
        """
        previews = []
        apartments = []
        for page in self.main_pages:
            previews += self.get_preview_elements(page)
        for preview in previews:
            apartment = self.get_apartment(apartment_start_id, image_start_id, 
                                        preview, self.templates.apartment, self.templates.image)
            if apartment is None:
                continue
            apartments.append(apartment)
            apartment_start_id += 1
            image_start_id = apartment.images[-1].id + 1
        self.apartments = apartments
        return apartments
        
    def get_images(self, expose:HTML, selector:str) -> list:
        """Parses expose for image sources and captions.

        Parameters
        ----------
        expose : HTML
            expose of apartment
        selector : str
            str selector for find

        Returns
        -------
        list
            `{'src':str, 'caption':str, 'is_floorplan':bool}`
        """  
        return 

    def get_total_rent(self, expose:HTML, selectors:list):
        element, criteria = self.parse_selectors(expose, self.total_rent_sel)
        if not criteria:
            return None
        else:
            return criteria[0]

    def get_expose_category(self, expose:HTML, selectors:list):
        element, category = self.parse_selectors(expose, selectors)
        if not category:
            return None
        else:
            return self._clean_text(category[0])

    def get_expose_categories(self, expose:HTML):
        categories = {}
        for k,v in self.expose_categories.items():
            sel = getattr(self, v)
            if not sel:
                continue
            cat = self.get_expose_category(expose, sel)
            categories[k] = cat
        return categories

    def get_data_table(self, expose_html, table_selector:str) -> Element:
        """An element which holds data in 2 columns(label,content)"""
        table = expose_html.find(table_selector)
        if table:
            return table[0]
        return None
            

    def parse_data_table(self, data_table:Element, label_selector:str, content_selector:str) -> dict:
        """Parses a data table with 2 columns(label, content).

        Parameters
        ----------
        data_table : Element
            table element which holds data
        label_selector : str
            string selector for label column
        content_selector : str
            string selector for content column

        Returns
        -------
        dict
            parsed_dict
        """
        label_els = data_table.find(label_selector)
        content_els = data_table.find(content_selector)
        data = {}
        for l,c in zip(label_els, content_els):
            data[self._clean_text(l.text)] = self._clean_text(c.text)
            # print(f'{l.text}:{c.text}')
        return data

    def update_apartments(self) -> None:
        pass


class Immobilienscout24(ApartmentSearcher):
    def __init__(self, HTMLSession, *args, **kwargs):
        super().__init__(HTMLSession, *args)
        # self.extras_el_sel:list = [Selector('ul[@class="result-list-entry__secondary-criteria"]')]
        self.page_param:str = '&pagenumber'
        self.url:str = 'https://www.immobilienscout24.de/Suche/de/sachsen/leipzig/wohnung-mieten?numberofrooms=3.0-&price=-450.0&geocodes=1276013012060,1276013012058,1276013012080,1276013012002,1276013012063,1276013012003,1276013012020,1276013012022,1276013012076,1276013012149,1276013012054,1276013012079,1276013012064&enteredFrom=result_list{}'
        self.page_el_sel:list = [Selector('select[@class="select"]'),Selector('option',first=False, return_type=ReturnType.element)]
        self.element_sel:list = [Selector('li[@class*="result-list__listing"]',first=False,return_type=ReturnType.element)]
        self.title_sel:list = [Selector('a[@class*="result-list-entry__brand-title"]',text=True, return_type=ReturnType.text)]
        self.preview_img_sel:list = [Selector('img[@class*="gallery__image"]', attributes={'src':'src'}, return_type=ReturnType.attribute)]
        self.address_sel:list = [Selector('div[@class="result-list-entry__address"]',text=True, return_type=ReturnType.text)]
        self.expose_sel:list = [Selector('a[@class="result-list-entry__brand-title-container"]')]
        
        self.img_elements_sel:str = 'img[@class="sp-image"]'
        self.total_rent_sel:list = [Selector('dd[@class*="is24qa-gesamtmiete"]', text=True, return_type='text')]
        self.cold_rent_sel:list = [Selector('dd[@class*="is24qa-kaltmiete"]', text=True, return_type='text')]
        self.add_costs_sel:list = [Selector('dd[@class*="is24qa-nebenkosten"]', text=True, return_type='text')]
        self.deposit_sel:list = [Selector('.is24qa-kaution-o-genossenschaftsanteile', text=True, return_type='text')]
        self.energy_usage_sel:list = [Selector('dd[@class*="is24qa-endenergieverbrauch"]', text=True, return_type='text')]

        self.available_sel:list = [Selector('dd[@class*="is24qa-bezugsfrei-ab"]', text=True, return_type='text')]
        self.rooms_sel:list = [Selector('div[@class*="is24qa-zi"]', text=True, return_type='text')]
        self.description_sel:list = [Selector('pre[@class*="is24qa-objektbeschreibung"]', text=True, return_type='text')]
        self.living_area_sel:list = [Selector('div[@class*="is24qa-flaeche"]', text=True, return_type='text')]
        # self.extras_el_sel:list = [Selector('div[@class*="criteriagroup boolean-listing"]', return_type='element', first=False)]
        
        self.expose_categories = {
            'total_rent':'total_rent_sel',
            'cold_rent':'cold_rent_sel',
            'add_costs':'add_costs_sel',
            'living_area':'living_area_sel',
            'rooms':'rooms_sel',
            'description':'description_sel',
            'energy_usage':'energy_usage_sel',
            'available':'available_sel',
            'deposit':'deposit_sel'
            }
        for k,v in kwargs.items():
            setattr(self, k, v)

    def get_preview_img(self, preview, selectors:list=None):
        if not selectors:
            selectors = self.preview_img_sel
        element, preview_img = self.parse_selectors(preview, self.preview_img_sel)
        if not preview_img[0]['src']:
            element, preview_img = self.parse_selectors(preview, [Selector('img[@class*="gallery__image"]', attributes={'data-lazy-src':'src'}, return_type=ReturnType.attribute)])
            return preview_img[0]['src']
        else:
            return preview_img[0]['src']

    def _parse_image(self, element:Element):
        """Parses an img element for source, 
        caption and if its a floorplan.

        Parameters
        ----------
        expose : HTML
            expose of apartment
        selector : str
            str selector for find

        Returns
        -------
        list
            `{'src':str, 'caption':str, 'is_floorplan':bool}`
        """  
        src = element.attrs.get('data-src')
        if src and 'legacy_thumbnail' not in src:
            is_floorplan = False
            caption = element.attrs.get('data-caption','')
            if 'Grundriss' in caption:
                is_floorplan = True
            clean_src = src.split('/ORIG')[0]
            img = {'src':clean_src, 'caption':caption, 'is_floorplan':is_floorplan}
            return img

    def get_images(self, expose:HTML) -> list:
        """Parses expose for image sources and captions.

        Parameters
        ----------
        expose : HTML
            expose of apartment
        selector : str
            str selector for find

        Returns
        -------
        list
            `{'src':str, 'caption':str, 'is_floorplan':bool}`
        """  
        images = expose.find(self.img_elements_sel)
        # print(images)
        # img_elements = images[0].find('img')
        parsed_images = []
        for e in images:
            img = self._parse_image(e)
            # print(img)
            if img:
                parsed_images.append(img)
        return parsed_images

    def get_expose_categories(self, expose:HTML):
        categories = {}
        for k,v in self.expose_categories.items():
            sel = getattr(self, v)
            if not sel:
                continue
            cat = self.get_expose_category(expose, sel)
            categories[k] = cat
        extras = self._get_extras(expose)
        categories['extras'] = extras
        return categories

    def _get_extras(self, expose:HTML):
        extra_els = expose.find('div[@class*="criteriagroup boolean-listing"] > span.palm-hide')
        extras = '\n'.join([self._clean_text(e.text) for e in extra_els])
        return extras


class Immowelt(ApartmentSearcher):
    def __init__(self, HTMLSession, *args, **kwargs):
        super().__init__(HTMLSession, *args)
        # self.extras_el_sel:list = [Selector('ul[@class="result-list-entry__secondary-criteria"]')]
        self.page_param:str = '&cp'
        self.url:str = 'https://www.immowelt.de/liste/leipzig-anger-crottendorf/wohnungen/mieten?geoid=10814365000034%2C10814365000075%2C10814365000037%2C10814365000038%2C10814365000041%2C10814365000045%2C10814365000047%2C10814365000048%2C10814365000049%2C10814365000050%2C10814365000051%2C10814365000052%2C10814365000053&roomi=3&prima=500&eqid=53&sort=createdate desc{}'
        self.page_el_sel:list = [Selector('div[@id="pnlPaging"]'),Selector('a[@class*="btn"]',first=False,return_type=ReturnType.element)]
        self.element_sel:list = [Selector('div[@class*="js-object listitem_wrap"]',first=False,return_type=ReturnType.element)]
        self.title_sel:list = [Selector('h2[@class]',text=True, return_type=ReturnType.text)]
        self.preview_img_sel:list = [Selector('img[@class*="js_listimage"]', attributes={'src':'src'}, return_type=ReturnType.attribute)]
        self.address_sel:list = [Selector('div[@class*="listlocation"]',text=True, return_type=ReturnType.text)]
        self.expose_sel:list = [Selector('a[@class="result-list-entry__brand-title-container"]')]
        
        self.etage_r:re.Pattern = re.compile('(erdgeschoss|dachgeschoss)|^\d\.', re.IGNORECASE)
        self.wtyp_r:re.Pattern = re.compile('apartment|Attikawohnung|Etagenwohnung|Loft|Maisonett|Penthous|Rohdach|Terrasse', re.IGNORECASE)
        self.available_r:re.Pattern = re.compile('bezug|frei', re.IGNORECASE)
        # self.total_rent_sel:list = [Selector('dd[@class*="is24qa-gesamtmiete"]', text=True, return_type='text')]
        # self.cold_rent_sel:list = [Selector('dd[@class*="is24qa-kaltmiete"]', text=True, return_type='text')]
        # self.add_costs_sel:list = [Selector('dd[@class*="is24qa-nebenkosten"]', text=True, return_type='text')]
        # self.living_area_sel:list = [Selector('div[@class="hardfacts clear"]', text=True, return_type='text')]
        # self.rooms_sel:list = [Selector('div[@class*="is24qa-zi"]', text=True, return_type='text')]
        # self.description_sel:list = [Selector('pre[@class*="is24qa-objektbeschreibung"]', text=True, return_type='text')]
        # self.energy_usage_sel:list = [Selector('dd[@class*="is24qa-endenergieverbrauch"]', text=True, return_type='text')]
        # self.available_sel:list = [Selector('dd[@class*="is24qa-bezugsfrei-ab"]', text=True, return_type='text')]

        # self.extras_el_sel:list = [Selector('div[@class*="criteriagroup boolean-listing"]', return_type='element', first=False)]
        # self.expose_category_el_sel = [Selector('div[@class="datatable clear"]', first=False, return_type='element')]
        # 'living_area':'living_area_sel',
        # 'rooms':'rooms_sel',
        # 'description':'description_sel',
        # 'energy_usage':'energy_usage_sel',
        # 'available':'available_sel',
        # }
        for k,v in kwargs.items():
            setattr(self, k, v)
    
    def preload(self, first_page:HTML=None, test=False) -> HTML:
        """Requests all pages with the previews. Stores found pages
        in `self.main_pages` and returns it.

        Parameters
        -------
        first_page : HTML, by default None
            Will not load first page with session if the first page is given.
    
        test : bool
            If True, no session.get will be called and `first_page` must be given.
            Stores url's in `result_list`
        
        Returns
        -------
        list
            `result_list`=[page_1.html, ...]
        """
        if test:
            print(f'{self.__class__.__name__}.preload(first_page={first_page}) in testmode.')
            if not first_page:
                raise AttributeError(f'first_page argument must be HTML if testing.')
        results = []
        page = 1
        first_page_url = self.url.format(f'{self.page_param}={page}')
        if not first_page:
            first_page_response = self.session.get(first_page_url)
            if first_page_response.status_code != 200:
                print(f'{first_page_url} didnt load properly.')
                return None
            first_page = first_page_response.html
        pages = self.get_pages(first_page, self.page_el_sel)
        if test:
            url = self.url.format(f'{self.page_param}=1')
            result = url
        else:
            add_result = self._load_more_previews(pages, first_page)
            result = HTML(session=self.session, html=first_page.html + add_result.html,url=first_page.url)
        # first_page.html += add_result.html
        results.append(result)
        self.main_pages = results[:]
        return results

    def _load_more_previews(self, pages:int, main_page:HTML):
        page_size = pages*20
        offset = 4
        payload = {
            'query':'geoid=10814365000002,10814365000034,10814365000075,10814365000037,10814365000038,10814365000041,   10814365000045,10814365000047,10814365000048,10814365000049,10814365000050,10814365000051,10814365000052,10814365000053&etype=1&esr=2&roomi=3&prima=500&eqid=53&sort=createdate+desc',
            'offset':offset,
            'pageSize':page_size
        }
        url_post = 'https://www.immowelt.de/liste/getlistitems'
        response = self.session.post(url_post, data=payload)
        if response.status_code != 200:
            print(f'session.post(url={self.url} data={payload}) didnt load properly.')
            return None
        return response.html

    def get_expose_category(self, expose:HTML, selector:str):
        # element = expose.find(selector)
        # if not element:
        #     return None
        # return element
        pass

    def get_expose_categories(self, expose:HTML):
        data = {}
        categories = {}
        facts = self._get_hardfacts(expose)
        costs = self._get_costs(expose)
        description = self._get_description(expose)
        energy = self._get_energy(expose)
        apartment = self._parse_wohnung(expose)
        
        data.update(facts['parsed'])
        data.update(costs)
        data.update(description)
        data.update(energy)
        data.update(apartment)
    
        categories.update(facts['categories'])
        categories['extras'] = apartment['extras']
        categories['parsed'] = data
        for k,v in data.items():
            key = k.lower()
            if 'warmmiete' in key:
                categories['total_rent'] = v
            if 'nebenkosten' in key:
                categories['add_costs'] = v
            if 'kaltmiete' in key:
                categories['cold_rent'] = v
            if 'objekt' in key:
                categories['description'] = v
            if 'energieverbrauch' in key:
                categories['energy_usage'] = v
            if 'kaution' in key:
                categories['deposit'] = v
            if 'bezugsfrei' in key:
                categories['available'] = v
        return categories
    
    def get_images(self, expose:HTML) -> list:
        """Parses expose for image sources and captions.

        Parameters
        ----------
        expose : HTML
            expose of apartment
        selector : str
            str selector for find

        Returns
        -------
        list
            `{'src':str, 'caption':str, 'is_floorplan':bool}`
        """  
        # images = expose.html.find(self.img_elements_sel)
        caps = expose.search_all('caption":"{}"')
        srcs = expose.search_all('srcImageStage":"{}"')
        # print(images)
        parsed_images = []
        for cap,src in zip(caps,srcs):
            is_floorplan = False
            if src and cap:
                if 'grundriss' in cap[0].lower():
                    is_floorplan = True
                img = {'src':src[0],'caption':cap[0],'is_floorplan':is_floorplan}
                parsed_images.append(img)
        return parsed_images

    def _get_costs(self, expose:HTML):
        dt = self.get_data_table(expose, 'div[@class="datatable clear"]')
        if dt:
            parsed = self.parse_data_table(dt, 'div[@class*="datalabel"]', 'div[@class*="datacontent"]')
            return parsed
        else:
            print('missing costs',expose)
            self.missing_info.append({'costs':expose,'src':expose.url})
            return
    
    def _get_hardfacts(self, expose:HTML):
        try:
            area, areal = expose.find('div[@class="hardfact"]')[1].text.split('\n')
        except:
            area, areal = '','Wohnfläche'
            self.missing_info.append({'living_area':expose,'src':expose.url})
        try:
            rooms, roomsl = expose.find('div[@class="hardfact rooms"]')[0].text.split('\n')
        except:
            rooms, roomsl= '','Zimmer'
            self.missing_info.append({'rooms':expose,'src':expose.url})
        parsed = {self._clean_text(areal):self._clean_text(area), 
                self._clean_text(roomsl):self._clean_text(rooms)}
        categories = {'living_area':area,'rooms':rooms}
        return {'categories':categories, 'parsed':parsed}

    def _get_description(self, expose:HTML):
        dt = self.get_data_table(expose, 'div[@class="read clear"]')
        if dt:
            parsed = self.parse_data_table(dt, '*[@class*="section_label"]', '*[@class*="section_content"]')
            return parsed
        else:
            print('missing description',expose)
            self.missing_info.append({'description':expose,'src':expose.url})
            return
        
    def _get_energy(self, expose:HTML):
        dt = self.get_data_table(expose, 'div[@class="datatable energytable clear"]')
        if dt:
            parsed = self.parse_data_table(dt, 'span[@class*="datalabel"]', 'span[@class*="datacontent"]')
            return parsed
        else:
            print('missing energy',expose)
            self.missing_info.append({'energy':expose,'src':expose.url})
            return {'energy_usage':''}

    def _print_s(self, label,content):
        """Prints
        -------
        
            label
            ------------
            content
        """
        print(label[0].text)
        print('-'*30)
        print(content[0].text)

    def _parse_wtype(self, element:Element) -> dict:
        """Parses upper part of Wohnung

        Parameters
        ----------
        element : Element
            Data element

        Returns
        -------
        dict
            contains:`Etage,Typ,Bezugsfrei,extras`
        """
        _data = element.find('p',first=True).text
        _data = self._clean_text(_data)
        _types = _data.split('\n')
        wdata = {'Bezugsfrei':'','Wohnungstyp':'','Etage':''}
        for t in _types:
            if self.available_r.search(t):
                wdata['Bezugsfrei'] = t
                continue
            # else:
            #     wdata = {'Bezugsfrei':''}
            if self.wtyp_r.search(t):
                wdata['Wohnungstyp'] = t
                continue
            # else:
            #     wdata = {'Wohnungstyp':''}
            if self.etage_r.search(t):
                wdata['Etage'] = t
                continue
            # else:
            #     wdata = {'Etage':''}
        _extras = element.find('li')
        if _extras:
            wdata['extras'] = '\n'.join([self._clean_text(e.text) for e in _extras])
        else:
            wdata['extras'] = {}
        return wdata

    def _parse_wohnung(self, expose:HTML) -> dict:
        """Parses Wohnung section

        Parameters
        ----------
        expose : HTML
            expose page

        Returns
        -------
        dict
            contains:`Etage,Typ,Bezugsfrei,Kaution,extras`
        """
        clear = expose.find('div[@class="clear"]')
        data = {}
        for c in clear:
            sec = c.find('div[@class*="section_label"]')
            if sec:
                if 'kaution' in sec[0].text.lower():
                    con = c.find('div[@class*="section_content"]')
                    # self._print_s(sec,con)
                    data['Kaution'] = self._clean_text(con[0].text)
                if 'wohnung' in sec[0].text.lower():
                    con = c.find('div[@class*="section_content"]')
                    # self._print_s(sec,con)
                    wtype = self._parse_wtype(con[0])
                    if 'Bezugsfrei' not in wtype:
                        print('no availability',expose)
                    data.update(wtype)
        return data
            

class Immonet(ApartmentSearcher):
    def __init__(self, HTMLSession, *args, **kwargs):
        super().__init__(HTMLSession, *args)
        # self.extras_el_sel:list = [Selector('span[@class="tag-element-50"]',first=False)]
        self.page_param:str = '&page'
        self.url:str = 'https://www.immonet.de/immobiliensuche/sel.do?suchart=1&city=116172&marketingtype=2&toprice=450.0&pageoffset=1&parentcat=1&listsize=26&sortby=19&objecttype=1&fromrooms=3.0&district=10391&district=10447&district=10428&district=10438&district=10431&district=10442&district=10441&district=10444&district=15868&district=10432&district=10443&district=10446&district=10434&district=10445{}'
        self.page_el_sel:list = [Selector('li[@class="pagination-item"]', first=False,return_type=ReturnType.element)]
        self.element_sel:list = [Selector('div[@id*="selObject_"]', first=False,return_type=ReturnType.element)]
        self.title_sel:list = [Selector('a[@id*="lnkToDetails_"]', text=True, return_type=ReturnType.text)]
        self.preview_img_sel:list = [Selector('img[@class*="image"]', attributes={'data-original':'src'}, return_type=ReturnType.attribute)]
        self.address_sel:list = None
        self.expose_sel:list= [Selector('a[@class="result-list-entry__brand-title-container"]')]
        self.img_elements_sel:str = 'div[@data-img]'
        for k,v in kwargs.items():
            setattr(self, k, v)

    def get_address(self, preview=None):
        """Immonet previews have no address.

        Returns
        -------
        None
        """
        return None

    def get_images(self, expose:HTML) -> list:
        """Parses expose for image sources and captions.

        Parameters
        ----------
        expose : HTML
            expose of apartment
        selector : str
            str selector for find

        Returns
        -------
        list
            `{'src':str, 'caption':str, 'is_floorplan':bool}`
        """  
        imgs = expose.find(self.img_elements_sel)
        # print(images)
        parsed_images = []
        for e in imgs:
            img = self._parse_image(e)
            # print(img)
            if img:
                parsed_images.append(img)
        return parsed_images

    def get_expose_categories(self, expose:HTML):
        data = {}
        categories = {}
        extras = self._get_extras(expose)
        address = self._get_address(expose)
        categories['extras'] = extras
        categories['address'] = address
        boxes = expose.xpath('//div[contains(@id,"panel")]/../..')
        for box in boxes:
            boxname = self._clean_text(box.find('h2')[0].text)
            # print(boxname)
            # print('-'*20)
            description_el = box.find('[id*="Description"]',first=True)
            if description_el:
                description = self._clean_text(description_el.text)
                data[boxname] = description
                if 'objekt' in boxname.lower():
                    categories['description'] = description
                # print(description)
            labels = box.find('[id^=panel] > div.row > div.row.list-100 > div:nth-child(1)')
            contents = box.find('[id^=panel] > div.row > div.row.list-100 > div:nth-child(2)')
            if labels and contents:
                for l,c in zip(labels, contents):
                    label = self._clean_text(l.text)
                    llow = label.lower()
                    content = self._clean_text(c.text)
                    data[label] = content
                    if 'inkl. nk' in llow:
                        categories['total_rent'] = content
                    if 'zzgl. nk' in llow:
                        categories['cold_rent'] = content
                    if 'kaution' in llow:
                        categories['deposit'] = content
                    if 'nebenkosten' in llow:
                        categories['add_costs'] = content
                    if 'wohnfläche' in llow:
                        categories['living_area'] = content
                    if 'verfügbar' in llow:
                        categories['available'] = content
                    if 'energieverbrauch' in llow:
                        categories['energy_usage'] = content
                    # print(l.text,c.text)
            # description = box.find('div[@id*="panelObjectdescription"]')
            # print(description[0].text)
            # print()
        categories['parsed'] = data
        return categories

    def _get_address(self, element:Element):
        p = element.xpath('//*[@id="tsr-int-map-anchor-xs-icon"]/../p')[0]
        if not p:
            return None
        street = p.text.split('\n')[0]
        plz, city = re.search('\n(\d+)(\W+)\s?(\w+)',p.text).group(1,3)
        return ','.join([street,plz,city])

    def _get_extras(self, element:Element):
        feature_elements = element.find('li[@id*="featureId"]')
        features = '\n'.join([self._clean_text(f.text) for f in feature_elements])
        if features:
            return  features
        else:
            return None
        
    def _parse_image(self, element:Element):
        """Parses an img element for source, 
        caption and if its a floorplan.

        Parameters
        ----------
        expose : HTML
            expose of apartment
        selector : str
            str selector for find

        Returns
        -------
        list
            `{'src':str, 'caption':str, 'is_floorplan':bool}`
        """  
        src = element.attrs.get('data-img')
        if src:
            is_floorplan = False
            caption = element.attrs.get('title','')
            if 'grundriss' in caption.lower():
                is_floorplan = True
            img = {'src':src, 'caption':caption, 'is_floorplan':is_floorplan}
            return img
        else:
            return None


class Address(NamedTuple):
    """Class for holding address object

    Parameters
    ----------
        street : str,
        street name

        nr : str,
        house number

        postal : str = None,
        postal code

        city : str = None,
        city name
    """
    street:str
    nr:str
    postal:str = None
    city:str = None
    


class DB:
    def __init__(self, templates:ApartmentTemplateCollection, path:Path=':memory:', fresh:bool=False, uri=False):
        """init db

        Parameters
        ----------
        templates : ApartmentTemplateCollection
        Collection of templates

        path : Path, optional, by default uses in-memory database.
        Database path `self.path`
        
        fresh : bool, optional
        Overwrites old database, by default False
        """
        self.path = path
        if fresh and ':memory:' not in str(path) and path.is_file():
            self._delete()
        if ':memory:' not in str(path):
            new_file = not path.is_file()
        else:
            new_file = False
        self.templates = templates
        self.conn = sqlite3.connect(path, uri=uri)
        self.c = self.conn.cursor()
        if fresh or ':memory:' in str(path) or new_file:
            self._create_tables()

    def __repr__(self):
        return f'DB(path="{self.path}", templates={self.templates})'

    def _create_tables(self):
        """Creates tables from self.templates."""
        for template in self.templates:
            sql = template.get_create_table_sql()
            self.c.execute(sql)

    def _delete(self):
        """Deletes DB."""
        self.path.unlink()
        print('removed: ',self.path)

    def _get_tables(self) -> list:
        """Fetches table names from sqlite_master.

        Returns
        -------
        list
            table_names
        """
        self.c.execute(f'select name from sqlite_master where type="table"')
        _tables = self.c.fetchall()
        table_names = [t[0] for t in _tables]
        return table_names

    def get_count(self, table:str):
        """Counts items in table.

        Parameters
        ----------
        table : str
            name

        Returns
        -------
        int
            count
        
        Raises
        ------
        AttributeError
            Table is not in database.
        """
        tables = self._get_tables()
        if table in tables:
            self.c.execute(f'select count(id) from {table}')
            count = self.c.fetchone()[0]
            return count
        else:
            raise AttributeError(f'{table} does not exist.')
    
    def get_last_id(self, table:str):
        """Gets the last id of a table.

        Parameters
        ----------
        table : str
            name

        Returns
        -------
        int
            last_id
        
        Raises
        ------
        AttributeError
            Table is not in database.
        """
        tables = self._get_tables()
        if table in tables:
            self.c.execute(f'select max(rowid) from {table}')
            rowid = self.c.fetchone()[0]
            if rowid is None:
                return 0
            else:
                return rowid
        else:
            raise AttributeError(f'{table} does not exist.')

    def insert(self, entry:DatabaseEntry):
        """Inserts data from entry to this database.

        Parameters
        ----------
        entry : DatabaseEntry
            entry_instance
        """
        name = entry._template.table.name
        if name not in self._get_tables():
            raise AttributeError(f'{name} table not in DB')
        sql = entry._template.get_insert_sql()
        db_entry = entry.get_insert_values()
        self.c.execute(sql, db_entry)
        self.conn.commit()

    def insert_many(self, entries:list):
        """Inserts all entries from list to this database.

        Parameters
        ----------
        entries : list,
            [template_instance, ...]
        """
        if not entries:
            return
        name = entries[0]._template.table.name
        if name not in self._get_tables():
            raise AttributeError(f'{name} table not in DB')
        sql = entries[0]._template.get_insert_sql()
        db_entries = []
        for table in entries:
            entry = table.get_insert_values()
            db_entries.append(entry)
        self.c.executemany(sql, db_entries)
        self.conn.commit()
    
    def get_data_entries(self, template:Template, data_entry_class:DatabaseEntry, sql_extra:str=None):
        """Creates database entry instances from this database

        Parameters
        ----------
        template : `Template`,
            database template
        
        data_entry_class : `DatabaseEntry`,
            entry class for data

        Returns
        -------
        list
            `data_entries`
        """
        keys = template.column_names()
        sql = template.get_select_sql(sql_extra=sql_extra)
        self.c.execute(sql)
        data = self.c.fetchall()
        if not data:
            return
        entries = []
        for values in data:
            entry_kwargs = {key:value for key,value in zip(keys,values)}
            data_entry = data_entry_class(template, **entry_kwargs)
            entries.append(data_entry)
        return entries