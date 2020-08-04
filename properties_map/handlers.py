import osmium, geojson, re, sqlite3
from shapely import geometry, wkb
from pathlib import Path
from secrets import token_hex
from properties_map.apartment import DB

GEOJSON_PATH = Path().cwd() / 'data' / 'geojson'
GEOJSON_DB = GEOJSON_PATH / 'geojson.db'

class AreaWriterHandler(osmium.SimpleHandler):
    """Writes data for specific area to reduce size
    
    east: `float`,
        longitude of bounding box to the east.
    
    north: `float`,
        latitude of bounding box to the north.
    
    west: `float`,
        longitude of bounding box to the westt.
    
    east: `float`,
        latitude of bounding box to the south.
    """
    def __init__(self, writer, east=12.1423, north=51.4230, west=12.6813, south=51.2275):
        # default area is of city leipzig
        super(AreaWriterHandler, self).__init__()
        self.writer = writer
        self.east = east
        self.west = west
        self.north = north
        self.south = south

    def node(self, n):
        if (self.east <= n.location.lon <= self.west and 
             self.north >= n.location.lat >= self.south):
            self.writer.add_node(n)

    def way(self, w):
        node = w.nodes[0]
        if (self.east <= node.location.lon <= self.west and 
            self.north >= node.location.lat >= self.south):
            self.writer.add_way(w)

    # TODO remove relations out of bound
    def relation(self, r):
        self.writer.add_relation(r)

class Handler:
    """Base handler."""
    def __init__(self, tag_filters:list=None, id_filter:list=None, 
                relations_filter:list=None, db_path:str=GEOJSON_DB, 
                overwrite_db:bool=False, apartment_db:DB=None):
        """Base handler for osm.

        Parameters
        ----------
        tag_filters : list, optional,
            Tags to filter relevant data, see OSM documentation for more info, by default None

        id_filter : list, optional
            matches only id's, by default None

        relations_filter : list, optional
            [description], by default None

        db_path : str, optional
            path of geojson.db, by default GEOJSON_DB

        overwrite_db : bool, optional
            creates new database if set to True, by default False
        """
        self._connect_db(db_path, overwrite=overwrite_db)
        self.geofab = osmium.geom.GeoJSONFactory()
        self.wkbfab = osmium.geom.WKBFactory()
        self.default_radius = 1
        self.default_intensity = 1
        self.tag_filters = tag_filters
        if tag_filters:
            # self._update_reg()
            self.reg = self._reg_filter()
        self.id_filter = id_filter
        self.geojson_features = []
        self.relations_filter = relations_filter

    def _connect_db(self, db_path, overwrite=False):
        dbp = Path(db_path)
        if overwrite:
            self.conn = sqlite3.connect(dbp)
            self.c = self.conn.cursor()
            self.c.execute("""drop table Line;""")
            self.c.execute("""drop table Stops;""")
            self.conn.commit()
            self._create_db()
            return
        if dbp.is_file():
            self.conn = sqlite3.connect(dbp)
            self.c = self.conn.cursor()
        else:
            self.conn = sqlite3.connect(dbp)
            self.c = self.conn.cursor()
            self._create_db()

    def _create_db(self):
        self.c.execute("""create table Line(id INT PRIMARY KEY, name Text, geojson Text);""")
        self.c.execute("""create table Stops(id INT PRIMARY KEY, name Text, geojson Text);""")
        
        self.conn.commit()

    # def _update_reg(self):
    #     """Sets `self.regs` according to `self.tag_filters`."""
    #     self.reg = self._reg_filter()
    #     # self.reg = self.regs[0]

    def _reg_filter(self):
        # regs = []
        regd = {}
        for tags in self.tag_filters:
            # for tag in tags:
            for t,v in tags.items():
                # reg = re.compile(re.escape(v), re.IGNORECASE)
                reg = re.compile(v, re.IGNORECASE)
                regd[t] = reg
            
            # regs.append(regd)
        return regd

    def filter(self, osm_obj):
        """Filters osm_obj for given self.tag_filters.
        
        Saves node."""
        if self.id_filter:
            if not self.filter_id(osm_obj):
                return False
        if self.tag_filters:
            if not self.filter_tags(osm_obj):
                return False
        return True
        # self._save_node(osm_obj)

    def filter_tags(self, osm_obj):
        for tag in self.tag_filters:
            if self.filter_tag(tag, osm_obj):
                return True
        return False

    # def filter_tag(self, tag, osm_obj):
    #     keys = set(tag)
    #     n_keys = set(dict(osm_obj.tags))
    #     if keys.issubset(n_keys):
    #         for ftag,fvalue in tag.items():
    #             if type(fvalue)==list:
    #                 for fv in fvalue:
    #                     if self._value_in_obj(ftag, fv, osm_obj):
    #                         return True
    #             else:
    #                 if self._value_in_obj(ftag, fvalue, osm_obj):
    #                 # if self.regs[ftag].search(osm_obj.tags.get(ftag)):
    #                     return True
    #     return False

    def filter_tag(self, tag, osm_obj):
        # keys = set(tag)
        # n_keys = set(dict(osm_obj.tags))
        # if keys.issubset(n_keys):
        # for reg in self.regs:
        has_values = True
        for ftag,fvalue in tag.items():
            # if type(fvalue)==list:
            #     for fv in fvalue:
            #         if self._value_in_obj(reg, fv, osm_obj):
            #             return True
            #     continue
            # else:
            # if not self._value_in_obj(reg, ftag, osm_obj):
            if not self.reg[ftag].search(osm_obj.tags.get(ftag,'')):
                has_values = False
                break
            # return True
        if has_values:
            return True
        else:
            return False
            # continue
        # return False
                

        # else:
        #     return False

    def filter_id(self, osm_obj):
        if osm_obj.id in self.id_filter:
            return True
        else:
            return False

    def _value_in_obj(self, reg, ftag, osm_obj):
        # for reg in self.regs:
            # for key in reg:
        if reg[ftag].search(osm_obj.tags.get(ftag,'')):
            # if osm_obj.tags.get(ftag) == fvalue:
            return True
        # return False

    def feature_collection(self, features:list):
        """Returns FeatureCollection of features."""
        return geojson.FeatureCollection(features)

    def save_geojson(self, features, data_file='test.json', data_dir:Path=None, append=False):
        """Saves geojson object to datapath."""
        mode = 'a' if append else 'w'
        if not data_dir:
            data_dir = GEOJSON_PATH
        else:
            if not data_dir.is_dir():
                try:
                    data_dir.mkdir()
                except:
                    pass
        filepath = data_dir / data_file
        try:
            with open(filepath, mode) as f:
                geojson.dump(features, f)
            print('saved: ',filepath)
        except:
            print('saving didnt work, attempting to save with a safe name')
            clean_n = "".join([c for c in filepath.stem if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            # random 8 letters
            rngl = token_hex(8)
            clean_n = clean_n+filepath.suffix if clean_n else rngl+filepath.suffix
            filepath = GEOJSON_PATH / clean_n
            with open(filepath, mode) as f:
                geojson.dump(features, f)
    
    def _db_count_id(self, table):
        self.c.execute(f'select count(id) from {table}')
        _id = self.c.fetchone()[0]
        return _id

    def db_insert_line(self, track):
        line_id = self._db_count_id('Line')
        name = track.tags.get('name','')
        self.c.execute('insert into Line(id, name, geojson) values (?,?,?) ', (line_id, name, str(track.way)))
        self.conn.commit()
        
    def db_insert_stops(self, track):
        stop_id = self._db_count_id('Stops')
        name = track.tags.get('name','')
        self.c.execute('insert into Stops(id, name, geojson) values (?,?,?) ', (stop_id, name, str(track.stops)))
        self.conn.commit()

    def load_geojson(self, filename):
        """Returns geojson file."""
        filepath = GEOJSON_PATH / filename
        with open(filepath, 'r') as f:
            data = geojson.load(f)
        print('loaded: ',filepath)
        return data


class NodeHandler(Handler):
    # """Handles node callbacks from `SimpleHandler`."""
    def __init__(self, **kwargs):
        """`node_filter`: list of node id's to save or return."""
        super(NodeHandler, self).__init__(**kwargs)
        # self.id_filter = node_filter
        # self.geojson_points = []
        # self.geojson_features = []
        self.ignored_nodes = []
        self.invalid_node_locations = 0

    def _save_node(self, node):
        """Creates geojson object."""
        geo_wkb = self.geofab.create_point(node)
        geo_point = geojson.loads(geo_wkb)
        if type(geo_point)=='str':
            print(geo_point)
        props = dict(node.tags)
        props['id'] = node.id
        # props['point'] = (node.lon, node.lat)
        props['intensity'] = self.default_intensity
        props['radius'] = self.default_radius
        geo_feature = geojson.Feature(geometry=geo_point, properties=props)
        # self.geojson_points.append(geo_point)
        self.geojson_features.append(geo_feature)

    def geojson_points(self, as_features=False) -> list:
        if not self.geojson_features:
            return None
        points = []
        for feat in self.geojson_features:
            props = feat['properties']
            point = props['geometry']
            if as_features:
                points.append(geojson.Feature(geometry=point,properties=props))
            else:
                points.append(point)
        return points

    def filter_relation(self, relation):
        if self.relations_filter:
            for r in self.relations_filter:
                nodes = self.filter_relation(r)

    def callback(self, n):
        if self.filter(n):
            print('node ',n.tags)
            self._save_node(n)


class WayHandler(Handler):
    """Handles way callbacks from `SimpleHandler`."""
    def __init__(self, **kwargs):
        super(WayHandler, self).__init__(**kwargs)
        # self.geojson_linestrings = []
        # self.geojson_features = []
        self.invalid_locations = []

    def _save_way(self, way):
        """Creates geojson object."""
        try:
            geo_wkb = self.geofab.create_linestring(way)
            geo_line = geojson.loads(geo_wkb)
            props = dict(way.tags)
            props['id'] = way.id
            props['radius'] = self.default_radius
            props['intensity'] = self.default_intensity
            feature = geojson.Feature(geometry=geo_line, properties=props)
            # self.geojson_linestrings.append(geo_line)
            self.geojson_features.append(feature)
        except Exception as e:
            # print(way, e)
            props = dict(way.tags)
            props['id'] = way.id
            self.invalid_locations.append(props)
    
    def callback(self, w):
        if self.filter(w):
            
        # if w.tags.get('amenity','') == 'cinema':
            self._save_way(w)
    
    def geojson_linestrings(self, properties=None, as_features=False) -> list:
        """Returns list of geojson.LineString or geojson.Feature."""
        if not self.geojson_features:
            return None
        collection = []
        for feat in self.geojson_features:
            if properties:
                props = properties
            else:
                props = feat['properties']            
            linestrings = feat['geometry']
            if as_features:
                collection.append(geojson.Feature(geometry=linestrings,properties=props))
            else:
                collection.append(linestrings)
        return collection


class RelationHandler(Handler):
    """Handles relation callbacks from `SimpleHandler`."""
    def __init__(self, **kwargs):
        super(RelationHandler, self).__init__(**kwargs)
        self.relations = []
        self.ignored_relations = []

    def callback(self, r):
        if self.filter(r):
            self._save_relation(r)
    
    def _save_relation(self, r):
        rela = {'tags':dict(r.tags)}
        rela['id'] = r.id
        rela['refs'] = {}
        # rela['radius'] = self.default_radius
        # rela['intensity'] = self.default_intensity
        # rela['type'] = []
        for rel in r.members:
            rela['refs'][str(rel.ref)] = ''
            rela['refs'][str(rel.ref)] = rel.type
            # if rel.type == 'n':
            #     rela['type'].append('n')
            #     # self.ignored_nodes.append(rela)
            # if rel.type == 'w':
            #     rela['type'].append('w')
            # if rel.type == 'r':
            #     rela['type'].append('r')
            #     # self.ignored_relations.append(rela)   
        self.relations.append(rela)
    
    def get_ids(self, relation, n=True, w=True, r=True) -> dict:
        """Returns dict with requested ids.
        
        `{'n':[node_ids],'w':[way_ids],'r':[relation_ids]}`."""
        node_ids = []
        way_ids = []
        relation_ids = []
        for n_id,n_type in relation['refs'].items():
            if n_type=='n' and n:
                node_ids.append(int(n_id))
            elif n_type=='w' and w:
                way_ids.append(int(n_id))
            elif n_type=='r' and r:
                relation_ids.append(int(n_id))
        ids = {'n':node_ids,'w':way_ids,'r':relation_ids}
        return ids

    def has_nodes(self, relation):
        for ref,n_type in relation['refs'].items():
            if n_type == 'n':
                return True
        return False
            
    def has_ways(self, relation):
        for ref,n_type in relation['refs'].items():
            if n_type == 'w':
                return True
        return False


class AreaHandler(Handler):
    """Handles relation callbacks from `SimpleHandler`."""
    def __init__(self, **kwargs):
        super(AreaHandler, self).__init__(**kwargs)
        # self.geojson_multipolygons = []
        # self.geojson_features = []
        # self.geojson_point = []
    
    def _save_area(self, area):
        mp_wkb = self.geofab.create_multipolygon(area)
        shape_wkb = self.wkbfab.create_multipolygon(area)
        mp = geojson.loads(mp_wkb)
        shape_area = wkb.loads(shape_wkb, hex=True)
        props = dict(area.tags)
        props['id'] = area.id
        props['radius'] = self.default_radius
        props['intensity'] = self.default_intensity
        point = shape_area.representative_point()
        props['point'] = (point.x, point.y)
        props['area'] = shape_area.area
        # p = geojson.Point(props['point'])
        # mp = geojson.MultiPolygon(geo_wkb)
        mp_feature = geojson.Feature(geometry=mp, properties=props)
        # self.geojson_point.append(p)
        # self.geojson_multipolygons.append(mp)
        self.geojson_features.append(mp_feature)

    def geojson_points(self, as_features=False):
        """Returns list of geojson.Point or geojson.Feature(MultiPolygon)."""
        if not self.geojson_features:
            return None
        points = []
        for area_feat in self.geojson_features:
            props = area_feat['properties']
            p = props['point']
            point = geojson.Point(p)
            if as_features:
                points.append(geojson.Feature(geometry=point,properties=props))
            else:
                points.append(point)
        return points
    
    def callback(self, a):
        if self.filter(a):
            print('area ',a.tags)
            self._save_area(a)


class CombinedHandler:
    def __init__(self, node:NodeHandler=None,way:WayHandler=None,relation:RelationHandler=None,area:AreaHandler=None):
        self.nh = node
        self.wh = way
        self.rh = relation
        self.ah = area

    def apply(self):
        n_callback = self.nh.callback if self.nh else None
        w_callback = self.wh.callback if self.wh else None
        r_callback = self.rh.callback if self.rh else None
        a_callback = self.ah.callback if self.ah else None
        h = osmium.make_simple_handler(node=n_callback, way=w_callback, relation=r_callback, area=a_callback)
        h.apply_file('data/data.osm.pbf', locations=True)
        if self.wh and self.ah:
            self.remove_duplicate_areas()

    def remove_duplicate_areas(self):
        # for i in range(len(self.wh.geojson_features)):
        to_remove = []
        for wh_f in self.wh.geojson_features:
            unique = True
            # wh_f = self.wh.geojson_features[i]
            _wh_prop = dict(wh_f['properties'])
            del _wh_prop['id']
            for ah_f in self.ah.geojson_features:
                _ah_prop = dict(ah_f['properties'])
                del _ah_prop['id']
                del _ah_prop['area']
                del _ah_prop['point']
                if _wh_prop == _ah_prop:
                    to_remove.append(wh_f)
                    # self.wh.geojson_features.remove(wh_f)
        for feature in to_remove:
            self.wh.geojson_features.remove(feature)
            

    def save_points(self, data_dir=GEOJSON_PATH, data_file='test.json', append=False):
        ah_features = self.ah.geojson_points(as_features=True)
        nh_features = self.nh.geojson_features
        self.nh.save_geojson(ah_features+nh_features,data_dir=data_dir, data_file=data_file, append=append)