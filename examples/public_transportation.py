if __name__ == "__main__":
    # For starting from 'examples' directory.
    from pathlib import Path
    from sys import path
    path.append(str(Path.cwd()))
from properties_map.osm import OPV
from properties_map.handlers import NodeHandler, WayHandler, RelationHandler

def main():
    """Example for populating the database from osm.pbf files.
    
    Creates tables for public stops and lines in database, 
    searches all nodes / ways / relations with tag {operator:lvb}
    and inserts found results.

    It will take several minutes to complete.
    """
    bus_tram_tags = [{'operator':'lvb'}]
    nh = NodeHandler()
    wh = WayHandler()
    rh = RelationHandler(tag_filters=bus_tram_tags)
    opv = OPV(node_handler=nh,way_handler=wh,relation_handler=rh)
    tracks = opv.get_tracks()

if __name__ == "__main__":
    main()