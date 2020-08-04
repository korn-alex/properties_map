# from properties_map.osm import StorableNode, StorableWay

# import unittest

# class TestStorableWay(unittest.TestCase):
#     def setUp(self):
#         tags = {'barrier': 'wall', 'leisure': 'park', 'name': 'Friedhof Lindenau', 'opening_hours': 'Apr-Sep 07:00-20:00; Oct-Mar 08:00-18:00', 'religion': 'christian'}
#         points = [(12.3184592, 51.3425832), (12.3180312, 51.34281), (12.3172063, 51.3424703), (12.3184592, 51.3425832)]
#         nodes = []
#         for i,p in enumerate(points):
#             node = StorableNode(str(i),lon=p[0], lat=p[1],tags=tags)
#             nodes.append(node)
#         self.nodes = nodes
#         self.way = StorableWay('4',nodes,tags=tags)

#     def test_reverse(self):
#         nodes = self.way.storable_nodes
#         p1 = self.way.points[1]
#         p2 = self.way.points[2]
#         self.way.reverse()
#         nodesr = self.way.storable_nodes
#         p1r = self.way.points[2]
#         p2r = self.way.points[1]

#         self.assertEqual(p1,p1r)
#         self.assertEqual(p2,p2r)
#         self.assertEqual(nodes[1],nodesr[-2])


#     if __name__ == "__main__":
#         unittest.main()