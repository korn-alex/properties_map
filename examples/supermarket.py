if __name__ == "__main__":
    # For starting from 'examples' directory.
    from pathlib import Path
    from sys import path
    path.append(str(Path.cwd()))
from properties_map.handlers import NodeHandler, WayHandler, AreaHandler, CombinedHandler

def main():
    """Example for populating the database from osm.pbf files.
    
    Creates a table for supermarkets in database, 
    searches all nodes / ways / areas with tag {shop:supermarket}
    and inserts found results.
    """
    tags = [
        {'shop':'supermarket'},
        ]
    nh = NodeHandler(tag_filters=tags)
    wh = WayHandler(tag_filters=tags)
    ah = AreaHandler(tag_filters=tags)
    combined = CombinedHandler(node=nh,way=wh,area=ah)
    combined.apply()
    supermarket_geojsons = nh.geojson_features + ah.geojson_points(as_features=True)
    with combined.nh.conn as conn:
        conn.execute("""create table Amenity(id INT PRIMARY KEY, name Text, geojson Text);""")
        conn.execute("""insert into Amenity(id,name,geojson) values(?,?,?)""", (0,'supermarket',str(supermarket_geojsons)))
if __name__ == "__main__":
    main()