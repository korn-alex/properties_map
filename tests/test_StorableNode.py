# from properties_map.osm import StorableNode
# from shapely import geometry
# import geojson

# import unittest

# class TestStorableWay(unittest.TestCase):
#     def setUp(self):
#         tags = {'barrier': 'wall', 'leisure': 'park', 'name': 'Friedhof Lindenau', 'opening_hours': 'Apr-Sep 07:00-20:00; Oct-Mar 08:00-18:00', 'religion': 'christian'}
#         points = [(12.3184592, 51.3425832), (12.3180312, 51.34281), (12.3172063, 51.3424703), (12.3184592, 51.3425832)]
#         lon = 12.3184592
#         lat = 51.3425832
#         self.node = StorableNode('0',lon=lon,lat=lat,tags=tags)

#     def test_geo(self):
#         # geo = {"coordinates": [self.lon, self.lat], "type": "Point"}
#         geo = geojson.Point(self.node.location)
#         self.assertEqual(self.node.geo.point(), geo)

#     def test_shape(self):
#         shape = geometry.Point(self.node.location)
#         self.assertEqual(self.node.shape(), shape)
    
# if __name__ == "__main__":
#         unittest.main()