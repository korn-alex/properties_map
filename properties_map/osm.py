import osmium as o
import geojson, re
from shapely import geometry, wkb
from properties_map.handlers import NodeHandler, WayHandler, RelationHandler, AreaHandler, CombinedHandler
from properties_map.apartment import Address
# from geojson import geojson.Point, geojson.Feature, geojson.Polygon, geojson.MultiPolygon, LineString, loads as geoloads
from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from time import time
from dataclasses import dataclass, field
# osmium.geom.GeoJSONFactory()
# import osmium
# import sys

@dataclass
class Track:
    """Class to hold tracks.
    
    `tags`: dict
    
    `stops`: list of geojson.Point
    
    `way`: geojson.Feature"""
    tags: dict
    stops: list
    way: geojson.Feature

class OPV:
    """Finding Bus, Tram stops and ways."""
    def __init__(self, osm_file='data/data.osm.pbf', node_handler:NodeHandler=None, 
                way_handler:WayHandler=None, relation_handler:RelationHandler=None, 
                                                        area_handler:AreaHandler=None):
        self.osm_file = osm_file
        self.GEOJSON_DIR = Path().cwd() / 'data' / 'geojson' / 'lvb'
        self.nh = node_handler
        self.wh = way_handler
        self.rh = relation_handler
        self.ah = area_handler
        if relation_handler is None:
            raise Exception('needs relation_handler to get relation info for tracks')

    def get_tracks(self) -> list:
        """Returns a list with Track classes
        
            `tags: dict` 
            
            `stops: [point_features]`
            
            `way: Feature(MultiLineString)`."""
        self.gather_track_relations()
        tracks = []
        # TODO pack multiple relations into one, so the `get_track` handler can go through all ids at once
        for rel in self.rh.relations:
            point_features, multilinestrings_feature = self.get_track(rel)
            track = Track(rel['tags'],point_features,multilinestrings_feature)
            self.save_track(track)
            tracks.append(track)
        # for t in tracks:
        #     self.save_track(t)
        return tracks

    def gather_track_relations(self):
        """Applies `self.rh` to file"""
        h = o.make_simple_handler(relation=self.rh.callback)
        h.apply_file(self.osm_file, locations=True)


    def get_track(self, relation):
        """Returns `Point, Feature(MultiLineStrings)`."""
        tags = relation['tags']
        ids = self.rh.get_ids(relation)
        nh_callback = self.nh.callback if ids['n'] else None
        wh_callback = self.wh.callback if ids['w'] else None
        self.nh.tag_filters = [{'public_transport':'stop_position'}]
        self.nh.reg = self.nh._reg_filter()
        self.nh.id_filter = ids['n']
        self.wh.id_filter = ids['w']
        h2 = o.make_simple_handler(node=nh_callback, way=wh_callback)
        h2.apply_file(self.osm_file, locations=True)
        pf, mlf = self.get_features(tags)
        return pf, mlf

    def get_features(self, tags):
        ls = self.wh.geojson_linestrings(properties=tags, as_features=False)
        if ls:
            ml = geojson.MultiLineString(ls)
            mlf = geojson.Feature(geometry=ml, properties=tags)
            # mlf = self.wh.geojson_linestrings(properties=tags, as_features=True)
        else:
            mlf = []
        pf = self.nh.geojson_features
        print(tags.get('name',''))
        print('nh len features',len(self.nh.geojson_features))
        print('wh len features',len(self.wh.geojson_features))
        self.nh.geojson_features = list()
        self.wh.geojson_features = list()
        # print('nh len features',len(self.nh.geojson_features))
        # print('wh len features',len(self.wh.geojson_features))
        return pf, mlf

    def save_track(self, track:Track):
        name = track.tags.get('name','')
        if track.stops:
            # self.nh.save_geojson(track.stops, data_file=f'{name}_stops.json', data_dir=self.GEOJSON_DIR)
            self.nh.db_insert_stops(track)
        if track.way:
            self.nh.db_insert_line(track)
            # self.wh.save_geojson(track.way, data_file=f'{name}.json', data_dir=self.GEOJSON_DIR)

    # def make_feature_collection(self, multiline_properties):
    #     mlf = self.wh.multi_line_feature(properties=multiline_properties)
    #     pf = self.nh.geojson_features
    #     # area_points = ah.geojson_points(as_feature=True)
    #     fc = geojson.FeatureCollection([mlf]+pf)
    #     return fc


@dataclass
class ReverseCoder:
    apartments:list
    missing:list = field(default_factory=list)
    nodes:list = field(default_factory=list)
    areas:list = field(default_factory=list)
    re_street:re.Pattern=field(default=re.compile('[\-\w\s.]+\d\w?$', re.I))
    re_housenumber:re.Pattern=field(default=re.compile('\d{,3}\w?$', re.I))
    def prepare(self):
        self.apartment_dict = {a.id:a for a in self.apartments}
        self.addresses = [(a.id, a.address) for a in self.apartments]
        self.parsed = [(a[0], self._parse_address(a[1])) for a in self.addresses]
        self.unique_addresses = set(p[1] for p in self.parsed if p[1])
        if not self.unique_addresses:
            raise IndexError('no unique addresses')
        self.filters = [(a, self._make_tag_filter(a)) for a in self.unique_addresses if a]
        
        # maps unique address to apartment ids
        self.id_address_map = {}
        for ua in self.unique_addresses:
            ids = [ap_id for ap_id,p in self.parsed if p==ua]
            self.id_address_map[ua] = ids

    def _parse_address(self, address:str):
        if not address:
            return None
        # p = self._re_street_nr.findall(address)
        if address:
            parts = address.split(',')
            # if len(parts) != 3:
            #     print('address malformed: ',address)
            #     return
            for part in parts:
                p = self.re_street.search(part)
                if p:
                    housenumber = self.re_housenumber.search(part).group()
                    street = self.re_housenumber.sub('',part).strip()
                    parsed_address = Address(street=street, nr=housenumber)
                    return parsed_address
            # print(a)
            # print(f'{name}:{nr}')
            # return address
        else:
            print('    missing ',address)
            return None

    def _make_tag_filter(self, address:Address):
        if not address:
            return
        if address.nr is None or address.street is None:
            return
        else:
            tag = {'addr:city':'Leipzig'}
            tag['addr:street'] = f'{re.escape(address.street)}|{re.escape(address.street.replace(".",""))}|{re.escape(address.street.replace(".","").replace("ss","ß"))}'
            tag['addr:housenumber'] = '^'+address.nr+'$'
            return tag
    # def parse_addresses(self):
    #     # addresse_strings = [a.address for a in apartments]
    #     addresses = []
    #     for a in self.apartments:
    #         address = self._parse_address(a.address)
    #         if not address:
    #             print(f'{apartment} misses address')
    #             continue
    #         addresses.append(address)
    
    def search(self):
        start = time()
        for i, (address,tag) in enumerate(self.filters):
            nh = NodeHandler(tag_filters=[tag])
            ah = AreaHandler(tag_filters=[tag])
            # nh = NodeHandler(tag_filters=[filters[0]])
            # ah = AreaHandler(tag_filters=[filters[0]])
            handler = CombinedHandler(node=nh,area=ah)
            handler.apply()
            if not handler.nh.geojson_features and not handler.ah.geojson_features:
                # for ua in rc.unique_addresses:
                #     nl += [(i,a) for i,a in rc.parsed if a==ua]
                for ap_id in self.id_address_map[address]:
                    # ap = self.apartments[ap_id-1]
                    ap = self.apartment_dict.get(ap_id)
                    self.missing.append((ap, tag))
                    print('missing: ',(ap, tag))
            else:
                ap_ids = self.id_address_map[address]
                if handler.nh.geojson_features:
                    self.nodes.append((ap_ids, handler.nh.geojson_features))
                if handler.ah.geojson_features:
                    self.areas.append((ap_ids, handler.ah.geojson_features))
            print(f'address: {i+1:2d} / {len(self.filters)}')
        print('nodes: ',len(self.nodes))
        print('areas: ',len(self.areas))
        print('missing: ',len(self.missing))
        end = time()
        print(f'time taken: {end-start:.2f}s')

    def get_coordinate(self, feature:dict):
        """Parses feature for coordinates

        Parameters
        ----------
            feature : dict,
                geojson feature

        Returns
        -------
            tuple,
                (lon, lat)
        """
        geo = feature.get('geometry')
        if not geo:
            return
        geo_type = geo.get('type')
        if not geo_type:
            return
        elif geo_type == 'Point':
            point = geo.get('coordinates')
        elif geo_type == 'MultiPolygon':
            props = feature.get('properties')
            if not props:
                return
            point = props.get('point')
        if not point:
            return
        else:
            # coordinates = (point[1], point[0])
            return point


    
    

if __name__ == "__main__":
    pass
    # writer = osmium.SimpleWriter('data/data.osm.pbf')
    # wh = AreaWriterHandler(writer)
    # wh.apply_file('data/sachsen-latest.osm.pbf', locations=True)
    # out = NamesHandler()
    # out.apply_file('sachsen-latest.osm.pbf')