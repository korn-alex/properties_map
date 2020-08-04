from flask import Flask, render_template, request, jsonify, Response
app = Flask(__name__, template_folder='client/templates',static_folder='client/static')
from pathlib import Path
import json, geojson, re, sqlite3

from collections import namedtuple
from requests_html import HTMLSession, HTMLResponse, HtmlElement, HTML, Element
from dataclasses import dataclass, field
from pathlib import Path
import datetime
import time
from properties_map import apartment
from properties_map.template import site_db_templates, apartment_db_templates
from properties_map.apartment import DB, Selector, SelectorDict,\
        Immobilienscout24, Immonet, Immowelt, ApartmentSearcher, \
        WebEntry, ExposeEntry, PreviewEntry, Apartment, Image
from properties_map.site import SiteData, SiteManager
from properties_map.handlers import NodeHandler

from properties_map.handlers import GEOJSON_DB
from properties_map.apartment import DB
from properties_map.osm import ReverseCoder

dp = Path().cwd() / 'data' / 'geojson'
site_db_p = Path().cwd() / 'apartments' / 'database' / 'site_data.db'
apartments_db_p = Path().cwd() / 'apartments' / 'database' / 'apartments.db'

@app.route('/')
def main():
    return render_template('map.html')

def db_tables():
    conn = sqlite3.connect(GEOJSON_DB)
    c = conn.cursor()
    c.execute('select name from sqlite_master where type="table"')
    tables = [n[0] for n in c.fetchall()]
    return tables

@app.route('/api/data/<table>', methods=['GET'])
@app.route('/api/data/<table>/<int:id>', methods=['GET'])
def get_table_contents(table, id=None):
    conn = sqlite3.connect(GEOJSON_DB)
    c = conn.cursor()
    if table in db_tables():
        if id is not None:
            c.execute(f'select geojson from {table} where id=?', (id,))
            data = geojson.loads(c.fetchone()[0])
            if type(data) != list:
                contents = geojson.FeatureCollection([data])
            else:
                contents = geojson.FeatureCollection(data)
        else:
            c.execute(f'select id,name from {table}')
            contents = c.fetchall()
        return jsonify(contents)
    else:
        return jsonify('no such table')

@app.route('/api/data', methods=['GET'])
def get_tables():
    tables = db_tables()
    return jsonify(tables)


@app.route('/api/data', methods=['GET'])
def get_geojson():
    tables = db_tables()
    return jsonify(tables)


@app.route('/api/settings/<settings_name>', methods=['GET','POST'])
def settings(settings_name):
    sf = dp.parent / 'settings.json'
    if sf.is_file():
        with open(sf,'r') as f:
            settings = json.load(f)
    else:
        settings = {'controlOverlay':{}, 'apartment':{}}
        with open(sf, 'w') as f:
            json.dump(settings, f)
    if request.method == 'POST':
        settings[settings_name] = request.json
        with open(sf,'w') as f:
            json.dump(settings, f)
        return jsonify('ok')
    if request.method == 'GET':
        new_settings = settings.get(settings_name)
        if new_settings is not None:
            return jsonify(new_settings)
        else:
            return jsonify(f'"{settings_name}" not in settings.'), 404
    
@app.route('/api/apartments/database', methods=['GET'])
def get_apartments():
    ap_db = DB(apartment_db_templates,path=apartments_db_p)
    apartments = ap_db.get_data_entries(ap_db.templates.apartment,Apartment)
    if not apartments:
        return jsonify('no apartments')
    features = [a.get_feature() for a in apartments if a.get_feature()]
    collection = geojson.FeatureCollection(features)
    return jsonify(collection)

@app.route('/api/apartments/database/update_site', methods=['GET'])
def update_site_db():
    site_db = DB(site_db_templates, path=site_db_p)
    ap_db = DB(apartment_db_templates, path=apartments_db_p)
    start = time.time()
    site_manager = SiteManager(site_db, ap_db, immobilienscout24=Immobilienscout24, immowelt=Immowelt, immonet=Immonet)
    msg = site_manager.update_site_db()
    end = time.time()
    return jsonify(msg)

@app.route('/api/apartments/database/update_apartments', methods=['GET'])
def update_ap_db():
    site_db = DB(site_db_templates, path=site_db_p)
    ap_db = DB(apartment_db_templates, path=apartments_db_p)
    start = time.time()
    site_manager = SiteManager(site_db, ap_db, immobilienscout24=Immobilienscout24, immowelt=Immowelt, immonet=Immonet)
    msg = site_manager.update_apartment_db()
    end = time.time()
    return jsonify(msg)


@app.route('/api/apartments/missing_coordinates', methods=['GET','POST'])
def get_addresses_missing_coordinates():
    ap_db = DB(apartment_db_templates,path=apartments_db_p)
    if request.method == 'POST':
        ids = request.json.get('ids')
        latlng = request.json.get('coordinates')
        coordinates = json.dumps( (latlng["lng"], latlng["lat"]) )
        print(ids, coordinates)
        sql = f'update Apartment set coordinates=(?) where id=?'
        entries = [(coordinates, i) for i in ids]
        with ap_db.conn as conn:
            conn.executemany(sql, entries)
        return jsonify('ok')

    if request.method == 'GET':
        apartments = ap_db.get_data_entries(ap_db.templates.apartment,Apartment,sql_extra="where coordinates is null")
        if not apartments:
            return jsonify('no apartments')
        rc = ReverseCoder(apartments)
        rc.prepare()
        data = [{'address':ua,'ids':ids} for ua,ids in rc.id_address_map.items()]
        if not data:
            return 'no missing addresses', 404
        return jsonify(data)
    

@app.route('/api/apartments/images/<apid>', methods=['GET'])
def get_images(apid):
    ap_db = DB(apartment_db_templates,path=apartments_db_p)
    images = ap_db.get_data_entries(ap_db.templates.image,Image,sql_extra=f'where apartment_id={apid}')
    if not images:
        return jsonify('no images')
    img_dicts = [img.get_dict() for img in images]
    return jsonify(img_dicts)