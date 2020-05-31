import flask
import requests
from bson import ObjectId
from flask import Flask, render_template, request, redirect
import os
import pymongo
import json
from flask_googlemaps import GoogleMaps
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length
from datetime import datetime as dt
import dash
import dash_core_components as dcc
import dash_html_components as html
from bson.son import SON
import re
from flask_googlemaps import Map
from pymongo import MongoClient
from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.serving import run_simple
from flask_admin import Admin
import bcrypt
import pymongo
from bson.objectid import ObjectId

from flask import Flask
from flask_admin import Admin

from wtforms import form, fields
from flask_admin import BaseView, AdminIndexView,expose
from flask_admin.form import Select2Widget
from flask_admin.contrib.pymongo import ModelView, filters
from flask_admin.model.fields import InlineFormField, InlineFieldList

import bcrypt
from flask import render_template, url_for, request, session, redirect
import operator
import locale


from flask_mongoengine import MongoEngine
from mongoengine import *

def connect():
    # Substitute the 5 pieces of information you got when creating
    # the Mongo DB Database (underlined in red in the screenshots)
    # Obviously, do not store your password as plaintext in practice
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")

    eventMapDB = myclient["eventMapDB"]
    return eventMapDB


app = Flask(__name__)
app.config['WTF_CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = 'my_love_dont_try'

eventMapDB = connect()
events = eventMapDB["events"]
places = eventMapDB["places"]

places.ensure_index([("location", pymongo.GEOSPHERE)])
evl = places.find({})

event = []
for i in evl:
    exc = i
    exc['_id'] = str(exc['_id'])
    event.append(exc)


with open("data_file2.json", "w") as write_file:
    json.dump(event, write_file)
app.config['GOOGLEMAPS_KEY'] = "AIzaSyD1FwJCRkIeTDeAsMHe0KCUBDHRrFG0u1w"
GoogleMaps(app)


# forma buradan veri ekleyebilirsin.

class UserForm(FlaskForm):
    filter_date = StringField('Tarih', validators=[DataRequired(), Length(max=40)], render_kw={"placeholder": "tarih"})
    filter_radius = StringField('Çap', validators=[DataRequired(), Length(max=40)], render_kw={"placeholder": "çap"})


# Bind our index page to both www.domain.com/and www.domain.com/index
@app.route("/main_page", methods=['GET'])
@app.route("/", methods=['GET'])
def index():
    form = UserForm()
    return render_template('main_page.html', form=form)


@app.route("/index", methods=['GET'])
def ex():
    form = UserForm()
    return render_template('index.html', form=form)


@app.route("/write", methods=['GET'])
def write():
    # tum filtreler ve enlem boylam değerleri burya geliyor burada db sorgusu atabiliriz.
    filter_start_date = request.args.get('filter_start_date')
    filter_end_date = request.args.get('filter_end_date')
    filter_category = request.args.get('filter_category')
    if filter_category == 'Müzik':
        category = 'MUSIC'
    elif filter_category == 'Sahne':
        category = 'ART'
    elif filter_category == 'Aile':
        category = 'FAMILY'
    elif filter_category == 'Spor':
        category = 'SPORT'
    elif filter_category == 'Diğerleri':
        category = 'OTHER'
    else:
        category = {"$exists": 1}  # Buna etkisiz eleman tarzı bir şey koymam lazım

    """ !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!11WRITE THE CODEEEEEEEEE!!!!!!!!!
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""
    # Alt kategori kontrol
    filter_sub_category = request.args.get('filter_sub_category')
    print(filter_sub_category)
    if "nu" in filter_sub_category:

        filter_sub_category = {"$exists": 1}

    # min and max price
    filter_min_price = request.args.get('min_price')
    filter_max_price = request.args.get('max_price')
    if filter_min_price == "":

        filter_min_price = 0
    else:
        filter_min_price = float(filter_min_price)
    if filter_max_price == "":
        filter_max_price = 10000
    else:
        filter_max_price = float(filter_max_price)
    # konum filtreleri
    filter_city = request.args.get('filter_city')
    print(filter_city)
    all_data = []
    markers = []
    # and is it checked
    checked = request.args.get('checked')

    if checked == "1":
        # haritadan konum seçilmiştir

        filter_radius = request.args.get('filter_radius')
        radius_unit = int(request.args.get('radius_unit'))
        lat = request.args.get('lat')
        lng = request.args.get('lng')
        print(lat)
        print(lng)
        try:
            filter_radius = int(filter_radius)
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            lat = float(0)
            lng = float(0)
            filter_radius = 100000

        places_find = places.find({'location': {'$near': SON(
            [('$geometry', SON([('type', 'Point'), ('coordinates', [lng, lat])])),
             ('$maxDistance', filter_radius * radius_unit)])}})
        district_l = []
        # burda foru places find ile çevircen, birden fazla olan eventlerle placeleri all datada birleştircen
        for i in range(places_find.count()):

            events_date = events.find({"$and": [{'event_place_id': places_find[i]['_id']},
                                                {"start_date": {"$gte": filter_start_date, "$lte": filter_end_date}},
                                                {"end_date": {"$gte": filter_start_date, "$lte": filter_end_date}},
                                                {"category": category},
                                                {"subcategory": filter_sub_category},
                                                {"price": {"$gte": filter_min_price, "$lte": filter_max_price}}]})

            for j in range(events_date.count()):

                val = dict(events_date[j], **(places_find[i]))
                if val:
                    exist = 0
                    k=0
                    while exist == 0 and k < len(district_l):
                        if val['place_district'] == district_l[k]['district']:
                            district_l[k]['total'] = district_l[k]['total'] + 1
                            exist = 1
                        k+=1
                    if exist == 0:
                        district_l.append({
                            'district': val['place_district'],
                            'total': 1
                        })

                    if val['category'] == 'MUSIC':
                        val['category'] = 'Müzik'
                        val.update({'color': "#4694ae"})
                    elif val['category'] == 'ART':
                        val['category'] = 'Sahne'
                        val.update({'color': "#7aca5e"})
                    elif val['category'] == 'FAMILY':
                        val['category'] = 'Aile'
                        val.update({'color': "#edbf5c"})
                    elif val['category'] == 'SPORT':
                        val['category'] = 'Spor'
                        val.update({'color': "#9f659d"})
                    elif val['category'] == 'OTHER':
                        val['category'] = 'Diğerleri'
                        val.update({'color': "#f3706b"})
                    del val['event_place_id']
                    del val['_id']
                    all_data.append(val)
                    if "location" in val:
                        lat = val["location"]["coordinates"][1]
                        lon = val["location"]["coordinates"][0]
                        capacity = 0
                        if "capasity" in val:
                            capacity = val['capasity']
                        # aynı lat lon ile marker eklenmiş mi?
                        exist2 = 0
                        for x in markers:

                            if x['lat'] == lat and x['lng'] == lon:
                                x['list'].append({
                                    'name': val['name'],
                                    'start_time': val['start_time'],
                                    'start_date': val['start_date']
                                })
                                exist2 = 1
                        if exist2 == 0:
                            markers.append({
                                'icon': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                                'lat': lat,
                                'lng': lon,
                                'capacity': capacity,
                                'place_name': val['place_name'],
                                'district':val['place_district'],
                                'list': [{
                                    'name': val['name'],
                                    'start_time': val['start_time'],
                                    'start_date': val['start_date']}]
                            })

    else:
        district = request.args.get('district')
        print("district change to " + district)

        events_date = events.find({"$and": [{"start_date": {"$gte": filter_start_date, "$lte": filter_end_date}},
                                            {"end_date": {"$gte": filter_start_date, "$lte": filter_end_date}},
                                            {"category": category},
                                            {"subcategory": filter_sub_category},
                                            {"price": {"$gte": filter_min_price, "$lte": filter_max_price}}]})
        district_l = []
        for i in range(events_date.count()):

            val = places.find_one({'_id': events_date[i]['event_place_id']})
            print("\nval")
            print(val)
            print(events_date[i])
            print(events_date[i]["category"])
            if val:
                if (val['place_city'] == filter_city or 'Hepsi' in filter_city) and (
                        val['place_district'] == district or 'Hepsi' in district):
                    val.update(events_date[i])
                    if val['category'] == 'MUSIC':
                        val['category'] = 'Müzik'
                        val.update({'color': "#4694ae"})
                    elif val['category'] == 'ART':
                        val['category'] = 'Sahne'
                        val.update({'color': "#7aca5e"})
                    elif val['category'] == 'FAMILY':
                        val['category'] = 'Aile'
                        val.update({'color': "#edbf5c"})
                    elif val['category'] == 'SPORT':
                        val['category'] = 'Spor'
                        val.update({'color': "#9f659d"})
                    elif val['category'] == 'OTHER':
                        val['category'] = 'Diğerleri'
                        val.update({'color': "#f3706b"})
                    del val['event_place_id']
                    del val['_id']
                    exist = 0
                    k=0
                    while exist == 0 and k < len(district_l):
                        if val['place_district'] == district_l[k]['district']:
                            district_l[k]['total'] = district_l[k]['total'] + 1
                            exist = 1
                        k+=1
                    if exist == 0:
                        district_l.append({
                            'district': val['place_district'],
                            'total': 1
                        })

                    all_data.append(val)
                    if "location" in val:
                        lat = val["location"]["coordinates"][1]
                        lon = val["location"]["coordinates"][0]
                        print(lat)
                        if lat != '':
                            lat = float(lat)
                            lon = float(lon)
                            capacity = 0
                            if "capasity" in val:
                                capacity = val['capasity']
                            # aynı lat lon ile marker eklenmiş mi?
                            exist2 = 0
                            for x in markers:

                                print(str(x['lat']) + " " + str(x['lng']))

                                print(str(lat) + " " + str(lon))
                                if x['lat'] == lat and x['lng'] == lon:
                                    x['list'].append({
                                        'name': val['name'],
                                        'start_time': val['start_time'],
                                        'start_date': val['start_date']
                                    })
                                    exist2 = 1
                            if exist2 == 0:
                                markers.append({
                                    'icon': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                                    'lat': lat,
                                    'lng': lon,
                                    'capacity': capacity,
                                    'place_name': val['place_name'],
                                    'district': val['place_district'],
                                    'list': [{
                                        'name': val['name'],
                                        'start_time': val['start_time'],
                                        'start_date': val['start_date']}]
                                })
    # İlçe etkinlik yoğunluklarını gösteren markerlar
    for x in markers:
        for y in district_l:
            if y['district'] == x['district']:
                if y['total'] > 20 and y['total'] <= 30:
                    x['icon'] = 'http://maps.google.com/mapfiles/ms/icons/green-dot.png'
                elif y['total'] > 30 and y['total'] <= 40:
                    x['icon'] = 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png'
                elif y['total'] > 40 and y['total'] <= 50:
                    x['icon'] = 'http://maps.google.com/mapfiles/ms/icons/orange-dot.png'
                elif y['total'] >= 50:
                    x['icon'] = 'http://maps.google.com/mapfiles/ms/icons/red-dot.png'
    art_l = []
    other_l = []
    music_l = []
    family_l = []
    spor_l = []
    all_data = sorted(all_data, key=operator.itemgetter('start_date', 'start_time'))
    for v in all_data:
        if v['category'] == 'Müzik':
            music_l.append(v)
        elif v['category'] == 'Sahne':
            art_l.append(v)
        elif v['category'] == 'Spor':
            spor_l.append(v)
        elif v['category'] == 'Aile':
            family_l.append(v)
        elif v['category'] == 'Diğerleri':
            other_l.append(v)

    all_data2 = family_l + other_l + music_l + art_l + spor_l
    # forma veri eklersen eklediklerini buradan return etmeyi ve ajax kısmına eklemeyi unutma :)))
    return flask.jsonify({'all_data': all_data2, 'markers': markers})



@app.route("/first", methods=['GET'])
def first():

    # tum filtreler ve enlem boylam değerleri burya geliyor burada db sorgusu atabiliriz.
    filter_start_date = request.args.get('filter_start_date')
    filter_end_date = request.args.get('filter_end_date')
    filter_city = request.args.get('filter_city')

    print(filter_city)
    filter_category = request.args.get('filter_category')
    if filter_category == 'Müzik':
        category = 'MUSIC'
    elif filter_category == 'Sahne':
        category = 'ART'
    elif filter_category == 'Aile':
        category = 'FAMILY'
    elif filter_category == 'Spor':
        category = 'SPORT'
    elif filter_category == 'Diğerleri':
        category = 'OTHER'
    else:
        category = {"$exists": 1}  # Buna etkisiz eleman tarzı bir şey koymam lazım

    # search = {"$exists": 1} bunu filtre seçilmediyse filtre değişkenine yaz
    events_date = events.find({"$and": [{"start_date": {"$gte": filter_start_date, "$lte": filter_end_date}},
                                        {"end_date": {"$gte": filter_start_date, "$lte": filter_end_date}},
                                        {"category": category}]})
    all_data = []
    markers = []
    district_l= []

    for i in range(events_date.count()):
        val = places.find_one({'_id': events_date[i]['event_place_id']})
        print(val)

        print(filter_city)
        if val:
            if val['place_city'] == filter_city or 'Hepsi' in filter_city:
                val.update(events_date[i])
                if val['category'] == 'MUSIC':
                    val['category'] = 'Müzik'
                    val.update({'color': "#4694ae"})
                elif val['category'] == 'ART':
                    val['category'] = 'Sahne'
                    val.update({'color': "#7aca5e"})
                elif val['category'] == 'FAMILY':
                    val['category'] = 'Aile'
                    val.update({'color': "#edbf5c"})
                elif val['category'] == 'SPORT':
                    val['category'] = 'Spor'
                    val.update({'color': "#9f659d"})
                elif val['category'] == 'OTHER':
                    val['category'] = 'Diğerleri'
                    val.update({'color': "#f3706b"})

                del val['event_place_id']
                del val['_id']
                exist = 0
                k=0
                while exist == 0 and k < len(district_l):
                    if val['place_district'] == district_l[k]['district']:
                        district_l[k]['total'] = district_l[k]['total'] + 1
                        exist = 1
                    k+=1

                if exist == 0:
                    district_l.append({
                        'district': val['place_district'],
                        'total': 1
                    })
                all_data.append(val)
                if "location" in val:
                    lat = val["location"]["coordinates"][1]
                    lon = val["location"]["coordinates"][0]
                    if lat != '':
                        lat = float(lat)
                        lon = float(lon)
                        capacity = 0
                        if "capasity" in val:
                            capacity = val['capasity']
                        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        # aynı lat lon ile marker eklenmiş mi?
                        exist2 = 0
                        for x in markers:

                            print(str(x['lat']) + " " + str(x['lng']))

                            print(str(lat) + " " + str(lon))
                            if x['lat'] == lat and x['lng'] == lon:
                                x['list'].append({
                                    'name': val['name'],
                                    'start_time': val['start_time'],
                                    'start_date': val['start_date']
                                })
                                exist2 = 1
                        if exist2 == 0:
                            markers.append({
                                'icon': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                                'lat': lat,
                                'lng': lon,
                                'capacity': capacity,
                                'place_name': val['place_name'],
                                'district':val['place_district'],
                                'list': [{
                                    'name': val['name'],
                                    'start_time': val['start_time'],
                                    'start_date': val['start_date']}]
                            })



    # İlçe etkinlik yoğunluklarını gösteren markerlar
    for x in markers:
        for y in district_l:
            if y['district'] == x['district']:
                if y['total'] > 20 and y['total'] <= 30:
                    x['icon'] = 'http://maps.google.com/mapfiles/ms/icons/green-dot.png'
                elif y['total'] > 30 and y['total'] <= 40:
                    x['icon'] = 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png'
                elif y['total'] > 40 and y['total'] <= 50:
                    x['icon'] = 'http://maps.google.com/mapfiles/ms/icons/orange-dot.png'
                elif y['total'] >= 50:
                    x['icon'] = 'http://maps.google.com/mapfiles/ms/icons/red-dot.png'

    art_l = []
    other_l = []
    music_l = []
    family_l = []
    spor_l = []
    all_data = sorted(all_data, key=operator.itemgetter('start_date', 'start_time'))
    for v in all_data:
        if v['category'] == 'Müzik':
            music_l.append(v)
        elif v['category'] == 'Sahne':
            art_l.append(v)
        elif v['category'] == 'Spor':
            spor_l.append(v)
        elif v['category'] == 'Aile':
            family_l.append(v)
        elif v['category'] == 'Diğerleri':
            other_l.append(v)

    all_data2 = family_l + other_l + music_l + art_l + spor_l
    """for i in range(0,15):
        print(all_data[i]['start_time'] + " " + all_data[i]['start_date'])"""



    return flask.jsonify({'all_data': all_data2, 'markers': markers})


all_data = []

subdata ={ "li" :[
  {
    "kategori": "Sahne",
    "val" : "tiyatro",
    "alt": "Tiyatro",
  },
  {
    "kategori": "Sahne",
    "val" : "opera",
    "alt": "Opera",
  },
  {
    "kategori": "Sahne",
    "val" : "stand_up",
    "alt": "Stand Up",
  },
  {
    "kategori": "Sahne",
    "val" : "gosteri",
    "alt": "Gösteri",
  },
  {
    "kategori": "Sahne",
    "val" : "bale_dans",
    "alt": "Bale Dans",
  },
  {
    "kategori": "Sahne",
    "val" : "sinema",
    "alt": "Sinema",
  },
    {
    "kategori": "Sahne",
    "val" : "musical",
    "alt": "Müzikal",
  },
  {
    "kategori": "Sahne",
    "val" : "muzikli_gosteri",
    "alt": "Müzikli Gösteri",
  },
  {
    "kategori": "Sahne",
    "val" : "sirk",
    "alt": "Sirk",
  },
{
    "kategori": "Sahne",
    "val" : "other",
    "alt": "Diğerleri",
  },
{
    "kategori": "Müzik",
    "val" : "alternatif",
    "alt": "Alternatif",
  },
{
    "kategori": "Müzik",
    "val" : "blues",
    "alt": "Blues",
  },
{
    "kategori": "Müzik",
    "val" : "dans_elektronik",
    "alt": "Dans Elektronik",
  },
{
    "kategori": "Müzik",
    "val" : "dunya_muzik",
    "alt": "Dünya Müzik",
  },
{
    "kategori": "Müzik",
    "val" : "heavy_metal",
    "alt": "Heavy Metal",
  },
{
    "kategori": "Müzik",
    "val" : "jazz",
    "alt": "Caz",
  },
{
    "kategori": "Müzik",
    "val" : "klasik",
    "alt": "Klasik",
  },
{
    "kategori": "Müzik",
    "val" : "latin_tango",
    "alt": "Latin Tango",
  },
{
    "kategori": "Müzik",
    "val" : "new_age",
    "alt": "New Age",
  },
{
    "kategori": "Müzik",
    "val" : "party",
    "alt": "Party",
  },
{
    "kategori": "Müzik",
    "val" : "pop",
    "alt": "Pop",
  },
{
    "kategori": "Müzik",
    "val" : "rap_hiphop",
    "alt": "Rap Hiphop",
  },
{
    "kategori": "Müzik",
    "val" : "rock",
    "alt": "Rock",
  },
{
    "kategori": "Müzik",
    "val" : "turksanat_halkmuzik",
    "alt": "Türk Sanat ve Halk Müziği",
  },
{
    "kategori": "Müzik",
    "val" : "other",
    "alt": "Diğerleri",
  },
{
    "kategori": "Aile",
    "val" : "gosteri",
    "alt": "Gösteri",
  },
{
    "kategori": "Aile",
    "val" : "sirk",
    "alt": "Sirk",
  },
{
    "kategori": "Aile",
    "val" : "tiyatro",
    "alt": "Tiyatro",
  },
{
    "kategori": "Aile",
    "val" : "muzikli_gosteri",
    "alt": "Müzikli Gösteri",
  },
{
    "kategori": "Aile",
    "val" : "other",
    "alt": "Diğerleri",
  },
{
    "kategori": "Spor",
    "val" : "basketbol",
    "alt": "Basketbol",
  },
    {
    "kategori": "Spor",
    "val" : "motorspor",
    "alt": "Motorspor",
  },
{
    "kategori": "Spor",
    "val" : "dovus_sporlari",
    "alt": "Dövüş Sporları",
  },
{
    "kategori": "Spor",
    "val" : "Futbol",
    "alt": "Futbol",
  },
{
    "kategori": "Spor",
    "val" : "esport",
    "alt": "E-sport",
  },
{
    "kategori": "Spor",
    "val" : "motor_sporlari",
    "alt": "Motor Sporları",
  },
{
    "kategori": "Spor",
    "val" : "e_sport",
    "alt": "E-sport",
  },
{
    "kategori": "Spor",
    "val" : "voleybol",
    "alt": "Voleybol",
  },
{
    "kategori": "Spor",
    "val" : "tenis",
    "alt": "Tenis",
  },
{
    "kategori": "Spor",
    "val" : "other",
    "alt": "Diğerleri",
  },
{
    "kategori": "Diğerleri",
    "val" : "egitim",
    "alt": "Eğitim",
  },
{
    "kategori": "Diğerleri",
    "val" : "atolye",
    "alt": "Atölye",
  },
{
    "kategori": "Diğerleri",
    "val" : "mebonayliegitim",
    "alt": "Mebonayli Eğitim",
  },
{
    "kategori": "Diğerleri",
    "val" : "muze",
    "alt": "Müze",
  },
{
    "kategori": "Diğerleri",
    "val" : "fuar",
    "alt": "Fuar",
  },
{
    "kategori": "Diğerleri",
    "val" : "konferans",
    "alt": "Konferans",
  },
{
    "kategori": "Diğerleri",
    "val" : "sergi",
    "alt": "Sergi",
  },
{
    "kategori": "Diğerleri",
    "val" : "sergi",
    "alt": "Sergi",
  },
{
    "kategori": "Diğerleri",
    "val" : "urunsatisi",
    "alt": "Ürün Satışı",
  },
{
    "kategori": "Diğerleri",
    "val" : "minimaster",
    "alt": "Mini master",
  },
{
    "kategori": "Diğerleri",
    "val" : "seyretix",
    "alt": "Seyretix",
  },
    {
    "kategori": "Diğerleri",
    "val" : "@night",
    "alt": "@night",
  },
    {
    "kategori": "Diğerleri",
    "val" : "msaworkshop",
    "alt": "Msa work shop",
  }
]
}

def show_data(collect, groupBy, title):
    agr = [{'$group': {'_id': groupBy, 'all': {'$sum': 1}}}
        , {"$sort": SON([("_id", 1)])}]
    val = list(collect.aggregate(agr))
    # print(val)
    x = []
    y = []
    for i in val:
        if groupBy == "$category" :
            if i['_id'] == 'MUSIC':
                x.append('Müzik')
            elif i['_id'] == 'ART':
                x.append('Sahne')
            elif i['_id'] == 'FAMILY':
                x.append('Aile')
            elif i['_id'] == 'SPORT':
                x.append('Spor')
            elif i['_id'] == 'OTHER':
                x.append('Diğerleri')
        else:
            x.append(i['_id'])
        y.append(i['all'])
    ex_l = {'title': title, 'x': x, 'y': y}

    all_data.append(ex_l)


def show_data_of_megacity(city, title):
    # { "$and": [ {"start_date": { "$gte":start , "$lte" :end}},{'place_city': city}]}
    agr = [{'$match': {'place_city': city}},
           {'$group': {'_id': '$place_district', 'all': {'$sum': 1}}}
        , {"$sort": SON([("_id", 1)])}]
    val = list(places.aggregate(agr))
    # print(val)
    x = []
    y = []
    for i in val:
        x.append(i['_id'])
        y.append(i['all'])
    ex_l = {'title': title, 'x': x, 'y': y}

    all_data.append(ex_l)


def show_data_of_megacity_by_date(city, start, end):
    # { "$and": [ {"start_date": { "$gte":start , "$lte" :end}},{'place_city': city}]}
    agr = [{'$match': {'place_city': city}},
           {'$group': {'_id': '$place_district', 'all': {'$sum': 1}, 'array': {'$push': "$_id"}}}
        , {"$sort": SON([("_id", 1)])}]
    val = list(places.aggregate(agr))
    # print("megacity ")
    # print(val)
    x = []
    y = []
    for i in val:
        count = 0
        for j in i['array']:
            event_find = events.find_one({"$and": [{'event_place_id': j},
                                                   {"start_date": {"$gte": start, "$lte": end}},
                                                   {"end_date": {"$gte": start, "$lte": end}}
                                                   ]})
            # print(event_find)
            if event_find:
                count += 1
        x.append(i['_id'])
        y.append(count)
    ex_l = {'x': x, 'y': y}

    return ex_l


def show_statistic():
    show_data(events, '$start_date', "Tüm Türkiye gün/etkinlik sayısı")
    show_data(places, '$place_city', "İl/Etkinlik Sayısı")
    show_data(events, '$category', "Kategori/Etkinlik sayısı")
    show_data_of_megacity('İstanbul', "İstanbul")
    show_data_of_megacity('Ankara', "Ankara")
    show_data_of_megacity('İzmir', "İzmir")



    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    appDash = dash.Dash(__name__, server=app,
                        external_stylesheets=external_stylesheets,
                        url_base_pathname='/statistic/')
    appDash.config['suppress_callback_exceptions'] = True
    appDash.scripts.config.serve_locally = False
    appDash.scripts.append_script({"external_url": "https://cdn.plot.ly/plotly-locale-tr-latest.js"})
    config_plots = {
        'modeBarButtonsToRemove': ["sendDataToCloud", "lasso2d", "pan2d", "autoScale2d", "select2d", "zoom2d",
                                   "zoomIn2d", "zoomOut2d"],
        "locale": "tr"}

    #style ={'fontSize': 20} ,  month_format='Y-M-D',
    appDash.layout = html.Div( children=[
        html.H1(children='İstatistiki Veriler'),
        dcc.DatePickerRange(
            id='my-date-picker-range',
            min_date_allowed=dt(2015, 8, 5),
            display_format='DD.MM.YYYY',
            start_date=dt.now().replace(hour=0,minute=0,second=0,microsecond=0),
            end_date_placeholder_text="Bitiş Tarihi",
        ),
        html.Div(id='output-date', style={'fontSize': 20} ),
        dcc.Tabs(id="tabs", value='tab-1-example', children=[
            dcc.Tab(label='Tarih / Etkinlik Sayısı', value='tab-1-example'),
            dcc.Tab(label='İl / Etkinlik Sayısı', value='tab-2-example'),
            dcc.Tab(label='Kategori / Etkinlik Sayısı', value='tab-3-example'),
            dcc.Tab(label='İlçe / Etkinlik Sayısı', value='tab-4-example', children=[
                dcc.Tabs(id="sub_tabs", value='tab-5-example', children=[
                    dcc.Tab(label='İstanbul', value='tab-5-example'),
                    dcc.Tab(label='İzmir', value='tab-6-example'),
                    dcc.Tab(label='Ankara', value='tab-7-example')
                ], colors={
                    "border": "white",
                    "primary": "gold",
                    "background": "cornsilk"
                })
            ]),
            dcc.Tab(label='Alt Kategori / Etkinlik Sayısı', value='tab-8-example',children=[
                dcc.Tabs(id="subTab", value='tab-9-example', children=[
                    dcc.Tab(label='Sahne', value='tab-9-example'),
                    dcc.Tab(label='Müzik', value='tab-10-example'),
                    dcc.Tab(label='Spor', value='tab-11-example'),
                    dcc.Tab(label='Aile', value='tab-12-example'),
                    dcc.Tab(label='Diğerleri', value='tab-13-example')
                ], colors={
                "border": "white",
                "primary": "gold",
                "background": "cornsilk"
                })
            ])
        ]),
        html.Div(id='tabs-content-example')
    ])




    @appDash.callback(dash.dependencies.Output('tabs-content-example', 'children'),
                  [dash.dependencies.Input('tabs', 'value'),
                   dash.dependencies.Input('sub_tabs', 'value'),
                   dash.dependencies.Input('subTab', 'value')])
    def render_content(tab, sub_tab, sub_tab2):
        print(tab)
        if tab == 'tab-1-example':
            return dcc.Graph(
                id='turkey',
                config=config_plots,
                figure={
                    'data': [
                        {'x': all_data[0]['x'], 'y': all_data[0]['y'], 'type': 'bar', 'name': 'SF'},

                    ],
                    'layout': {
                        'title': all_data[0]['title'],
                        'titlefont': dict(size=30),
                        'xaxis': dict(
                            title='<b>Tarih </b>',
                            titlefont=dict(
                                family='Courier New, monospace',
                                size=20,
                                color='#7f7f7f'
                            )),
                        'yaxis': dict(
                            title='<b>Etkinlik Sayısı</b>',
                            titlefont=dict(
                                family='Helvetica, monospace',
                                size=20,
                                color='#7f7f7f'
                            ))
                    }
                }
            )
        elif tab == 'tab-2-example':
            return dcc.Graph(
                id='city',
                figure={
                    'data': [
                        {'x': all_data[1]['x'], 'y': all_data[1]['y'], 'type': 'bar', 'name': 'SF'},
                    ],
                    'layout': {
                        'title': all_data[1]['title'],
                        'titlefont': dict(size=30),
                        'bargap': 0.5,
                        'xaxis': dict(
                            title='<b>İl</b>',
                            titlefont=dict(
                                family='Courier New, monospace',
                                size=20,
                                color='#7f7f7f'
                            )),
                        'yaxis': dict(
                            title='<b>Etkinlik Sayısı</b>',
                            titlefont=dict(
                                family='Helvetica, monospace',
                                size=20,
                                color='#7f7f7f'
                            ))
                    }
                }
            )
        elif tab == 'tab-3-example':
            return dcc.Graph(
                id='category',
                figure={
                    'data': [
                        {'x': all_data[2]['x'], 'y': all_data[2]['y'], 'type': 'bar', 'name': 'X'},
                    ],
                    'layout': {
                        'title': all_data[2]['title'],
                        'titlefont': dict(size=30),
                        'bargap': 0.8,
                        'xaxis': dict(
                            title='<b>Kategori</b>',
                            titlefont=dict(
                                family='Courier New, monospace',
                                size=20,
                                color='#7f7f7f'
                            )),
                        'yaxis': dict(
                            title='<b>Etkinlik Sayısı</b>',
                            titlefont=dict(
                                family='Helvetica, monospace',
                                size=20,
                                color='#7f7f7f'
                            ))
                    }
                }
            )
        elif tab == 'tab-4-example':
            if sub_tab == 'tab-5-example':
                return dcc.Graph(
                    id='istanbul',
                    figure={
                        'data': [
                            {'x': all_data[3]['x'], 'y': all_data[3]['y'], 'type': 'bar', 'name': 'SF'},
                        ],
                        'layout': {
                            'title': all_data[3]['title'],
                            'titlefont': dict(size=30),
                            'bargap': 0.4,
                            'xaxis': dict(
                                title='<b>İlçe</b>',
                                titlefont=dict(
                                    family='Courier New, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                )),
                            'yaxis': dict(
                                title='<b>Etkinlik Sayısı</b>',
                                titlefont=dict(
                                    family='Helvetica, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                ))
                        }
                    }
                )
            if sub_tab == 'tab-6-example':
                return dcc.Graph(
                    id='izmir',
                    figure={
                        'data': [
                            {'x': all_data[5]['x'], 'y': all_data[5]['y'], 'type': 'bar', 'name': 'SF'},
                        ],
                        'layout': {
                            'title': all_data[5]['title'],
                            'titlefont': dict(size=30),
                            'bargap': 0.6,
                            'xaxis': dict(
                                title='<b>İlçe</b>',
                                titlefont=dict(
                                    family='Courier New, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                )),
                            'yaxis': dict(
                                title='<b>Etkinlik Sayısı</b>',
                                titlefont=dict(
                                    family='Helvetica, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                ))
                        }
                    }
                )
            if sub_tab == 'tab-7-example':
                return dcc.Graph(
                    id='ankara',
                    figure={

                        'data': [
                            {'x': all_data[4]['x'], 'y': all_data[4]['y'], 'type': 'bar', 'name': 'SF'},
                        ],
                        'layout': {
                            'title': all_data[4]['title'],
                            'titlefont': dict(size=30),
                            'bargap': 0.6,
                            'xaxis': dict(
                                title='<b>İlçe</b>',
                                titlefont=dict(
                                    family='Courier New, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                )),
                            'yaxis': dict(
                                title='<b>Etkinlik Sayısı</b>',
                                titlefont=dict(
                                    family='Helvetica, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                ))
                        }
                    }
                )
        elif tab == 'tab-8-example':
            if sub_tab2 == 'tab-9-example':
                agr = [{'$match': {'category': 'ART'}},
                       {'$group': {'_id': '$subcategory', 'all': {'$sum': 1}}}
                    , {"$sort": SON([("_id", 1)])}]
                val = list(events.aggregate(agr))
                x = []
                y = []
                for i in val:
                    y.append(i['all'])
                    j=0
                    find=0
                    while j < len(subdata["li"]) and find == 0:
                        if i['_id'] == subdata["li"][j]["val"]:
                            find = 1
                            x.append(subdata["li"][j]["alt"])
                        j+=1

                return dcc.Graph(
                    id='sahne',
                    figure={

                        'data': [
                            {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},
                        ],
                        'layout': {
                            'title': "Sahne",
                            'titlefont': dict(size=30),
                            'bargap': 0.6,
                            'xaxis': dict(
                                title='<b>Alt Kategori</b>',
                                titlefont=dict(
                                    family='Courier New, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                )),
                            'yaxis': dict(
                                title='<b>Etkinlik Sayısı</b>',
                                titlefont=dict(
                                    family='Helvetica, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                ))
                        }
                    }
                )
            if sub_tab2 == 'tab-10-example':
                agr = [{'$match': {'category': 'MUSIC'}},
                       {'$group': {'_id': '$subcategory', 'all': {'$sum': 1}}}
                    , {"$sort": SON([("_id", 1)])}]
                val = list(events.aggregate(agr))
                print(val)
                x = []
                y = []
                for i in val:
                    y.append(i['all'])
                    j=0
                    find=0
                    while j < len(subdata["li"]) and find == 0:
                        if i['_id'] == subdata["li"][j]["val"]:
                            find = 1
                            x.append(subdata["li"][j]["alt"])
                        j+=1

                return dcc.Graph(
                    id='muzik',
                    figure={

                        'data': [
                            {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},
                        ],
                        'layout': {
                            'title': "Müzik",
                            'titlefont': dict(size=30),
                            'bargap': 0.6,
                            'xaxis': dict(
                                title='<b>Alt Kategori</b>',
                                titlefont=dict(
                                    family='Courier New, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                )),
                            'yaxis': dict(
                                title='<b>Etkinlik Sayısı</b>',
                                titlefont=dict(
                                    family='Helvetica, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                ))
                        }
                    }
                )
            if sub_tab2 == 'tab-11-example':
                agr = [{'$match': {'category': 'SPORT'}},
                       {'$group': {'_id': '$subcategory', 'all': {'$sum': 1}}}
                    , {"$sort": SON([("_id", 1)])}]
                val = list(events.aggregate(agr))
                print(val)
                x = []
                y = []
                for i in val:
                    y.append(i['all'])
                    j=0
                    find=0
                    while j < len(subdata["li"]) and find == 0:
                        if i['_id'] == subdata["li"][j]["val"]:
                            find = 1
                            x.append(subdata["li"][j]["alt"])
                        j+=1

                return dcc.Graph(
                    id='spor',
                    figure={

                        'data': [
                            {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},
                        ],
                        'layout': {
                            'title': "Spor",
                            'titlefont': dict(size=30),
                            'bargap': 0.9,
                            'xaxis': dict(
                                title='<b>Alt Kategori</b>',
                                titlefont=dict(
                                    family='Courier New, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                )),
                            'yaxis': dict(
                                title='<b>Etkinlik Sayısı</b>',
                                titlefont=dict(
                                    family='Helvetica, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                ))
                        }
                    }
                )
            if sub_tab2 == 'tab-12-example':
                agr = [{'$match': {'category': 'FAMILY'}},
                       {'$group': {'_id': '$subcategory', 'all': {'$sum': 1}}}
                    , {"$sort": SON([("_id", 1)])}]
                val = list(events.aggregate(agr))
                print(val)
                x = []
                y = []
                for i in val:
                    y.append(i['all'])
                    j=0
                    find=0
                    while j < len(subdata["li"]) and find == 0:
                        if i['_id'] == subdata["li"][j]["val"]:
                            find = 1
                            x.append(subdata["li"][j]["alt"])
                        j+=1

                return dcc.Graph(
                    id='aile',
                    figure={

                        'data': [
                            {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},
                        ],
                        'layout': {
                            'title': "Aile",
                            'titlefont': dict(size=30),
                            'bargap': 0.6,
                            'xaxis': dict(
                                title='<b>Alt Kategori</b>',
                                titlefont=dict(
                                    family='Courier New, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                )),
                            'yaxis': dict(
                                title='<b>Etkinlik Sayısı</b>',
                                titlefont=dict(
                                    family='Helvetica, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                ))
                        }
                    }
                )
            if sub_tab2 == 'tab-13-example':
                agr = [{'$match': {'category': 'OTHER'}},
                       {'$group': {'_id': '$subcategory', 'all': {'$sum': 1}}}
                    , {"$sort": SON([("_id", 1)])}]
                val = list(events.aggregate(agr))
                print(val)
                x = []
                y = []
                for i in val:
                    y.append(i['all'])
                    j=0
                    find=0
                    while j < len(subdata["li"]) and find == 0:
                        if i['_id'] == subdata["li"][j]["val"]:
                            find = 1
                            x.append(subdata["li"][j]["alt"])
                        j+=1

                return dcc.Graph(
                    id='diger',
                    figure={

                        'data': [
                            {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},
                        ],
                        'layout': {
                            'title': "Diğerleri",
                            'titlefont': dict(size=30),
                            'bargap': 0.6,
                            'xaxis': dict(
                                title='<b>Alt Kategori</b>',
                                titlefont=dict(
                                    family='Courier New, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                )),
                            'yaxis': dict(
                                title='<b>Etkinlik Sayısı</b>',
                                titlefont=dict(
                                    family='Helvetica, monospace',
                                    size=20,
                                    color='#7f7f7f'
                                ))
                        }
                    }
                )


    @appDash.callback(
        dash.dependencies.Output('turkey', 'figure'),
        [dash.dependencies.Input('my-date-picker-range', 'start_date'),
         dash.dependencies.Input('my-date-picker-range', 'end_date')])
    def update_output(start_date, end_date):
        print("----turkey")
        print("start date ")
        print(start_date)
        print("end date")
        print(end_date)
        if start_date is not None and end_date is not None:
            print("start_date")
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            print(start_date)
            start = start_date.strftime('%Y-%m-%d')
            print(start)
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            print(end_date)
            end = end_date.strftime('%Y-%m-%d')

            agr = [{'$match': {
                "$and": [{"start_date": {"$gte": start, "$lte": end}}, {"end_date": {"$gte": start, "$lte": end}}]}},
                {'$group': {'_id': '$start_date', 'all': {'$sum': 1}}}
                , {"$sort": SON([("_id", 1)])}]
            val = list(events.aggregate(agr))
            print(val)
            x = []
            y = []
            for i in val:
                x.append(i['_id'])
                y.append(i['all'])

            return {
                'data': [
                    {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},

                ],
                'layout': {
                    'title': "Tüm türkiye gün/etkinlik sayısı",
                    'titlefont': dict(size=30),
                    'xaxis': dict(
                        title='<b>Tarih</b>',
                        titlefont=dict(
                            family='Courier New, monospace',
                            size=20,
                            color='#7f7f7f'
                        )),
                    'yaxis': dict(
                        title='<b>Etkinlik Sayısı</b>',
                        titlefont=dict(
                            family='Helvetica, monospace',
                            size=20,
                            color='#7f7f7f'
                        ))
                }
            }

    @appDash.callback(
        dash.dependencies.Output('city', 'figure'),
        [dash.dependencies.Input('my-date-picker-range', 'start_date'),
         dash.dependencies.Input('my-date-picker-range', 'end_date')])
    def update_output_city(start_date, end_date):
        print("---city")
        if start_date is not None and end_date is not None:
            print(start_date)
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            print(start_date)
            start = start_date.strftime('%Y-%m-%d')
            print(type(start))
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            end = end_date.strftime('%Y-%m-%d')
            #end=end_date
            agr = [{'$group': {'_id': '$place_city', 'all': {'$sum': 1}, 'array': {'$push': "$_id"}}}
                , {"$sort": SON([("_id", 1)])}]
            val = list(places.aggregate(agr))
            print(val)
            x = []
            y = []
            for i in val:
                count = 0
                for j in i['array']:
                    event_find = events.find_one({"$and": [{'event_place_id': j},
                                                           {"start_date": {"$gte": start, "$lte": end}},
                                                           {"end_date": {"$gte": start, "$lte": end}}
                                                           ]})
                    if event_find:
                        count += 1
                x.append(i['_id'])
                y.append(count)

            return {
                'data': [
                    {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},

                ],
                'layout': {
                    'title': "İl/Etkinlik Sayısı",
                    'titlefont': dict(size=30),
                    'bargap': 0.5,
                    'xaxis': dict(
                        title='<b>İl</b>',
                        titlefont=dict(
                            family='Courier New, monospace',
                            size=20,
                            color='#7f7f7f'
                        )),
                    'yaxis': dict(
                        title='<b>Etkinlik Sayısı</b>',
                        titlefont=dict(
                            family='Helvetica, monospace',
                            size=20,
                            color='#7f7f7f'
                        ))
                }
            }

    @appDash.callback(
        dash.dependencies.Output('category', 'figure'),
        [dash.dependencies.Input('my-date-picker-range', 'start_date'),
         dash.dependencies.Input('my-date-picker-range', 'end_date')])
    def update_output_category(start_date, end_date):
        if start_date is not None and end_date is not None:
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            start = start_date.strftime('%Y-%m-%d')
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            end = end_date.strftime('%Y-%m-%d')
            #end=end_date
            agr = [{'$match': {
                "$and": [{"start_date": {"$gte": start, "$lte": end}}, {"end_date": {"$gte": start, "$lte": end}}]}},
                {'$group': {'_id': '$category', 'all': {'$sum': 1}}}
                , {"$sort": SON([("_id", 1)])}]
            val = list(events.aggregate(agr))
            print(val)
            x = []
            y = []
            for i in val:
                if i['_id'] == 'MUSIC':
                    x.append('Müzik')
                elif i['_id'] == 'ART':
                    x.append('Sahne')
                elif i['_id'] == 'FAMILY':
                    x.append('Aile')
                elif i['_id'] == 'SPORT':
                    x.append('Spor')
                elif i['_id'] == 'OTHER':
                    x.append('Diğerleri')
                y.append(i['all'])

            return {
                'data': [
                    {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},

                ],
                'layout': {
                    'title': "Kategori/Etkinlik sayısı",
                    'titlefont': dict(size=30),
                    'bargap': 0.8,
                    'xaxis': dict(
                        title='<b>Kategori</b>',
                        titlefont=dict(
                            family='Courier New, monospace',
                            size=20,
                            color='#7f7f7f'
                        )),
                    'yaxis': dict(
                        title='<b>Etkinlik Sayısı</b>',
                        titlefont=dict(
                            family='Helvetica, monospace',
                            size=20,
                            color='#7f7f7f'
                        ))
                }
            }

    @appDash.callback(
        dash.dependencies.Output('istanbul', 'figure'),
        [dash.dependencies.Input('my-date-picker-range', 'start_date'),
         dash.dependencies.Input('my-date-picker-range', 'end_date')])
    def update_output_istanbul(start_date, end_date):
        if start_date is not None and end_date is not None:
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            start = start_date.strftime('%Y-%m-%d')
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            end = end_date.strftime('%Y-%m-%d')
            # veri çekiliyor
            #end=end_date
            new_list = show_data_of_megacity_by_date('İstanbul', start, end)

            return {
                'data': [
                    {'x': new_list['x'], 'y': new_list['y'], 'type': 'bar', 'name': 'SF'},

                ],
                'layout': {
                    'title': "İstanbul",
                    'titlefont': dict(size=30),
                    'bargap': 0.4,
                    'xaxis': dict(
                        title='<b>İlçe</b>',
                        titlefont=dict(
                            family='Courier New, monospace',
                            size=20,
                            color='#7f7f7f'
                        )),
                    'yaxis': dict(
                        title='<b>Etkinlik Sayısı</b>',
                        titlefont=dict(
                            family='Helvetica, monospace',
                            size=20,
                            color='#7f7f7f'
                        ))
                }
            }

    @appDash.callback(
        dash.dependencies.Output('izmir', 'figure'),
        [dash.dependencies.Input('my-date-picker-range', 'start_date'),
         dash.dependencies.Input('my-date-picker-range', 'end_date')])
    def update_output_izmir(start_date, end_date):
        if start_date is not None and end_date is not None:
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            start = start_date.strftime('%Y-%m-%d')
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            end = end_date.strftime('%Y-%m-%d')
            #end=end_date
            # Veri çekiliyor
            new_list = show_data_of_megacity_by_date('İzmir', start, end)

            return {
                'data': [
                    {'x': new_list['x'], 'y': new_list['y'], 'type': 'bar', 'name': 'SF'},

                ],
                'layout': {
                    'title': "İlçe/Etkinlik Sayısı",
                    'titlefont': dict(size=30),
                    'bargap': 0.6,
                    'xaxis': dict(
                        title='<b>İlçe</b>',
                        titlefont=dict(
                            family='Courier New, monospace',
                            size=20,
                            color='#7f7f7f'
                        )),
                    'yaxis': dict(
                        title='<b>Etkinlik Sayısı</b>',
                        titlefont=dict(
                            family='Helvetica, monospace',
                            size=20,
                            color='#7f7f7f'
                        ))
                }
            }

    @appDash.callback(
        dash.dependencies.Output('ankara', 'figure'),
        [dash.dependencies.Input('my-date-picker-range', 'start_date'),
         dash.dependencies.Input('my-date-picker-range', 'end_date')])
    def update_output_ankara(start_date, end_date):
        if start_date is not None and end_date is not None:
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            start = start_date.strftime('%Y-%m-%d')
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            end = end_date.strftime('%Y-%m-%d')
            end = end_date
            # veri çekiliyor
            new_list = show_data_of_megacity_by_date('Ankara', start, end)

            return {
                'data': [
                    {'x': new_list['x'], 'y': new_list['y'], 'type': 'bar', 'name': 'SF'},

                ],
                'layout': {
                    'title': "İlçe/Etkinlik Sayısı",
                    'titlefont': dict(size=30),
                    'bargap': 0.6,
                    'xaxis': dict(
                        title='<b>İlçe</b>',
                        titlefont=dict(
                            family='Courier New, monospace',
                            size=20,
                            color='#7f7f7f'
                        )),
                    'yaxis': dict(
                        title='<b>Etkinlik Sayısı</b>',
                        titlefont=dict(
                            family='Helvetica, monospace',
                            size=20,
                            color='#7f7f7f'
                        ))
                }
            }

    @appDash.callback(
        dash.dependencies.Output('sahne', 'figure'),
        [dash.dependencies.Input('my-date-picker-range', 'start_date'),
         dash.dependencies.Input('my-date-picker-range', 'end_date')])
    def update_output_s(start_date, end_date):
        if start_date is not None and end_date is not None:
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            start = start_date.strftime('%Y-%m-%d')
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            end = end_date.strftime('%Y-%m-%d')

            agr = [{'$match': {"$and": [{"start_date": {"$gte": start, "$lte": end}},
                                        {"end_date": {"$gte": start, "$lte": end}},
                                        {"category": "ART"}]}},
                   {'$group': {'_id': '$subcategory', 'all': {'$sum': 1}}}
                    , {"$sort": SON([("_id", 1)])}]
            val = list(events.aggregate(agr))
            print(val)
            print()
            x = []
            y = []
            for i in val:
                y.append(i['all'])
                j = 0
                find = 0
                while j < len(subdata["li"]) and find == 0:
                    if i['_id'] == subdata["li"][j]["val"]:
                        find = 1
                        x.append(subdata["li"][j]["alt"])
                    j += 1
            print("sahne içerik")
            print(x)
            print(y)
            return {
                'data': [
                    {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},

                ],
                'layout': {
                    'title': "<b>Sahne</b>",
                    'titlefont': dict(size=30),
                    'bargap': 0.5,
                    'xaxis': dict(
                        title='<b>Alt Kategori</b>',
                        titlefont=dict(
                            family='Courier New, monospace',
                            size=20,
                            color='#7f7f7f'
                        )),
                    'yaxis': dict(
                        title='<b>Etkinlik Sayısı</b>',
                        titlefont=dict(
                            family='Helvetica, monospace',
                            size=20,
                            color='#7f7f7f'
                        ))
                }
            }

    @appDash.callback(
        dash.dependencies.Output('muzik', 'figure'),
        [dash.dependencies.Input('my-date-picker-range', 'start_date'),
         dash.dependencies.Input('my-date-picker-range', 'end_date')])
    def update_output_m(start_date, end_date):
        if start_date is not None and end_date is not None:
            print(start_date)
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            print(start_date)
            start = start_date.strftime('%Y-%m-%d')
            print(type(start))
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            end = end_date.strftime('%Y-%m-%d')

            agr = [{'$match': {
                "$and": [{"start_date": {"$gte": start, "$lte": end}}, {"end_date": {"$gte": start, "$lte": end}},
                         {'category': 'MUSIC'}]}},
                {'$group': {'_id': '$subcategory', 'all': {'$sum': 1}}}
                , {"$sort": SON([("_id", 1)])}]
            val = list(events.aggregate(agr))
            print(val)
            x = []
            y = []
            for i in val:
                y.append(i['all'])
                j = 0
                find = 0
                while j < len(subdata["li"]) and find == 0:
                    if i['_id'] == subdata["li"][j]["val"]:
                        find = 1
                        x.append(subdata["li"][j]["alt"])
                    j += 1

            print("müzik içerik")
            print(x)
            print(y)

            return {
                'data': [
                    {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},

                ],
                'layout': {
                    'title': "<b>Müzik</b>",
                    'titlefont': dict(size=30),
                    'bargap': 0.5,
                    'xaxis': dict(
                        title='<b>Alt Kategori</b>',
                        titlefont=dict(
                            family='Courier New, monospace',
                            size=20,
                            color='#7f7f7f'
                        )),
                    'yaxis': dict(
                        title='<b>Etkinlik Sayısı</b>',
                        titlefont=dict(
                            family='Helvetica, monospace',
                            size=20,
                            color='#7f7f7f'
                        ))
                }
            }

    @appDash.callback(
        dash.dependencies.Output('spor', 'figure'),
        [dash.dependencies.Input('my-date-picker-range', 'start_date'),
         dash.dependencies.Input('my-date-picker-range', 'end_date')])
    def update_output_p(start_date, end_date):
        if start_date is not None and end_date is not None:
            print(start_date)
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            print(start_date)
            start = start_date.strftime('%Y-%m-%d')
            print(type(start))
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            end = end_date.strftime('%Y-%m-%d')

            agr = [{'$match': {
                "$and": [{"start_date": {"$gte": start, "$lte": end}}, {"end_date": {"$gte": start, "$lte": end}},
                         {'category': 'SPORT'}]}},
                {'$group': {'_id': '$subcategory', 'all': {'$sum': 1}}}
                , {"$sort": SON([("_id", 1)])}]
            val = list(events.aggregate(agr))
            print(val)
            x = []
            y = []
            for i in val:
                y.append(i['all'])
                j = 0
                find = 0
                while j < len(subdata["li"]) and find == 0:
                    if i['_id'] == subdata["li"][j]["val"]:
                        find = 1
                        x.append(subdata["li"][j]["alt"])
                    j += 1

            print("spor içerik")
            print(x)
            print(y)

            return {
                'data': [
                    {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},

                ],
                'layout': {
                    'title': "<b>Spor</b>",
                    'titlefont': dict(size=30),
                    'bargap': 0.9,
                    'xaxis': dict(
                        title='<b>Alt Kategori</b>',
                        titlefont=dict(
                            family='Courier New, monospace',
                            size=20,
                            color='#7f7f7f'
                        )),
                    'yaxis': dict(
                        title='<b>Etkinlik Sayısı</b>',
                        titlefont=dict(
                            family='Helvetica, monospace',
                            size=20,
                            color='#7f7f7f'
                        ))
                }
            }

    @appDash.callback(
        dash.dependencies.Output('diger', 'figure'),
        [dash.dependencies.Input('my-date-picker-range', 'start_date'),
         dash.dependencies.Input('my-date-picker-range', 'end_date')])
    def update_output_d(start_date, end_date):
        if start_date is not None and end_date is not None:
            print(start_date)
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            print(start_date)
            start = start_date.strftime('%Y-%m-%d')
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            end = end_date.strftime('%Y-%m-%d')
            print(end)

            agr = [{'$match': {
                "$and": [{"start_date": {"$gte": start, "$lte": end}}, {"end_date": {"$gte": start, "$lte": end}},
                         {'category': 'OTHER'}]}},
                {'$group': {'_id': '$subcategory', 'all': {'$sum': 1}}}
                , {"$sort": SON([("_id", 1)])}]
            val = list(events.aggregate(agr))
            print(val)
            x = []
            y = []
            for i in val:
                y.append(i['all'])
                j = 0
                find = 0
                while j < len(subdata["li"]) and find == 0:
                    if i['_id'] == subdata["li"][j]["val"]:
                        find = 1
                        x.append(subdata["li"][j]["alt"])
                    j += 1

            print("diger içerik")
            print(x)
            print(y)

            return {
                'data': [
                    {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},

                ],
                'layout': {
                    'title': "<b>Diğerleri</b>",
                    'titlefont': dict(size=30),
                    'bargap': 0.5,
                    'xaxis': dict(
                        title='<b>Alt Kategori</b>',
                        titlefont=dict(
                            family='Courier New, monospace',
                            size=20,
                            color='#7f7f7f'
                        )),
                    'yaxis': dict(
                        title='<b>Etkinlik Sayısı</b>',
                        titlefont=dict(
                            family='Helvetica, monospace',
                            size=20,
                            color='#7f7f7f'
                        ))
                }
            }

    @appDash.callback(
        dash.dependencies.Output('aile', 'figure'),
        [dash.dependencies.Input('my-date-picker-range', 'start_date'),
         dash.dependencies.Input('my-date-picker-range', 'end_date')])
    def update_output_a(start_date, end_date):
        if start_date is not None and end_date is not None:
            print(start_date)
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            print(start_date)
            start = start_date.strftime('%Y-%m-%d')
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            end = end_date.strftime('%Y-%m-%d')
            print(end)

            agr = [{'$match': {
                "$and": [{"start_date": {"$gte": start, "$lte": end}}, {"end_date": {"$gte": start, "$lte": end}},
                         {'category': 'FAMILY'}]}},
                {'$group': {'_id': '$subcategory', 'all': {'$sum': 1}}}
                , {"$sort": SON([("_id", 1)])}]
            val = list(events.aggregate(agr))
            print(val)
            x = []
            y = []
            for i in val:
                y.append(i['all'])
                j = 0
                find = 0
                while j < len(subdata["li"]) and find == 0:
                    if i['_id'] == subdata["li"][j]["val"]:
                        find = 1
                        x.append(subdata["li"][j]["alt"])
                    j += 1

            print("aile içerik")
            print(x)
            print(y)

            return {
                'data': [
                    {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},

                ],
                'layout': {
                    'title': "<b>Aile</b>",
                    'titlefont': dict(size=30),
                    'bargap': 0.9,
                    'xaxis': dict(
                        title='<b>Alt Kategori</b>',
                        titlefont=dict(
                            family='Courier New, monospace',
                            size=20,
                            color='#7f7f7f'
                        )),
                    'yaxis': dict(
                        title='<b>Etkinlik Sayısı</b>',
                        titlefont=dict(
                            family='Helvetica, monospace',
                            size=20,
                            color='#7f7f7f'
                        ))
                }
            }


    @appDash.callback(
        dash.dependencies.Output('output-date', 'children'),
        [dash.dependencies.Input('my-date-picker-range', 'start_date'),
         dash.dependencies.Input('my-date-picker-range', 'end_date')])
    def update_output_text(start_date, end_date):
        if start_date is not None and end_date is not None:
            locale.setlocale(locale.LC_ALL, "tr_TR")
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            print(start_date)
            start = start_date.strftime('%B %d, %Y')
            print(start)
            print(end_date)
            print(end_date)
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            print(end_date)
            end = end_date.strftime('%B %d, %Y')
            return "Şu tarihler arasındaki veriler gösteriliyor: " + start + " / " +end
        else:
            return 'Veri tabanındaki tüm veriler listeleniyor. Görmek istediğiniz tarih aralığını yukarıdan seçebillirsiniz.'

    return appDash




appDash = show_statistic()
event_app = DispatcherMiddleware(app, {
    '/dash1': appDash.server
})



def findPolygonCoordinates():
    with open('il-ilce.json') as f:
        data = json.load(f)
    print("data")
    print(data[0])


    city = data[0]["il"]
    jsList = [ { city : [] }]


    tur = 0;
    for i in data:
        tur+=1
        print("----------" + str(tur) +"---------")
        if  city == i["il"]:
            r = requests.get("https://nominatim.openstreetmap.org/search.php?q="+i["ilce"]+"+"+i["il"]+"+Turkey&polygon_geojson=1&format=json", headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0' })
            r_d = r.json()
            print("---r_d-----")
            print(r_d)
            dist = { i["ilce"] : []}
            for k in r_d:
                print("----k---")
                print(k)
                if k["class"] == "boundary":
                    for j in k["geojson"]["coordinates"][0]:
                        print("j------")
                        print(j)
                        loc = { "lat": j[0], "lng": j[1]}
                        dist[i["ilce"]].append(loc)
            print("----dist-----")
            print(dist)
            jsList[0][city].append(dist)
        elif jsList[0].get(i["il"]):
            city = i["il"]
            r = requests.get("https://nominatim.openstreetmap.org/search.php?q=" + i["ilce"] + "+" + i[
                "il"] + "+Turkey&polygon_geojson=1&format=json", headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'})
            r_d = r.json()
            print("---r_d-----")
            print(r_d)
            dist = {i["ilce"]: []}
            for k in r_d:
                print("----k---")
                print(k)
                if k["class"] == "boundary":
                    for j in k["geojson"]["coordinates"][0]:
                        print("j------")
                        print(j)
                        loc = {"lat": j[0], "lng": j[1]}
                        dist[i["ilce"]].append(loc)
            print("----dist-----")
            print(dist)
            jsList[0][city].append(dist)
        else:
            city = i["il"]
            jsList[0].update({ city : []})
            r = requests.get("https://nominatim.openstreetmap.org/search.php?q=" + i["ilce"] + "+" + i[
                "il"] + "+Turkey&polygon_geojson=1&format=json" , headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0' })
            r_d = r.json()
            print("---r_d-----")
            print(r_d)
            dist = {i["ilce"]: []}
            for k in r_d:
                print("----k---")
                print(k)
                if k["class"] == "boundary":
                    for j in k["geojson"]["coordinates"][0]:
                        print("j------")
                        print(j)
                        loc = {"lat": j[0], "lng": j[1]}
                        dist[i["ilce"]].append(loc)
            print("----dist-----")
            print(dist)
            jsList[0][city].append(dist)


    with open("districts.js", 'a') as file:
        file.write("var jsonObj = {\n \"l\": \n"+ json.dumps(jsList, ensure_ascii=False)+"\n}")



@app.route('/statistic/')
def render_statistic():
    return flask.redirect('/dash1')

###########################################################################
#----------------------------auth-------------------------------------------
###############################################################################
users=eventMapDB["users"]

@app.route('/giris')
def admin():
    if 'username' in session:

        return render_template("main_page.html")
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    login_user = users.find_one({'u_name' : request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            session['type']=login_user["type"]
            return redirect(url_for('admin'))

    return "Kullanıcı adı veya şifre yanlış!"

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()

    """  
    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            return redirect(url_for('admin'))"""

    return render_template('main_page.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        existing_user = users.find_one({'u_name': request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'u_name': request.form['username'], 'password': hashpass, "type":"normal"})
            session['username'] = request.form['username']
            session['type']='normal'
            return redirect(url_for('admin'))

        return 'That username already exists!'


    return render_template('register.html')

#######################################################################################



def eventDateRange():
    min_date=str(events.find().sort("start_date", 1)[0]["start_date"])
    max_date=str(events.find().sort("start_date", -1)[0]["start_date"])

    min_day=min_date.split("-")[2]
    min_mon=min_date.split("-")[1]
    min_year=min_date.split("-")[0]

    maxd=max_date.split("-")

    max_day=maxd[2]
    max_mon=maxd[1]
    max_year=maxd[0]

    min_date=min_day+"/"+min_mon+"/"+min_year
    max_date=max_day+"/"+max_mon+"/"+max_year
    return min_date, max_date

"""
for i in users.find():
    print(i)
"""

# User admin


class UserForm(form.Form):
    type=fields.StringField("Kullanıcı Tipi")

class PlaceForm(form.Form):
    place_name = fields.StringField('Etkinlik Yeri Adı')
    place_district = fields.StringField('İlçe')
    place_city = fields.StringField('İl')
    place_country=fields.StringField('Ülke')
    capasity=fields.IntegerField("Kişi Kapasitesi")


class PlacesView(ModelView):
    def is_accessible(self):
        if session and session['type']=='admin':
            return True
        else:
            return False

    column_list = ("_id","place_name", "place_district", "place_city")
    column_sortable_list = ("place_name", "place_district", "place_city")

    form = PlaceForm

class UserView(ModelView):
    def is_accessible(self):
        if session and session['type']=='admin':
            return True
        else:
            return False
    column_list = ("u_name","type", "password")
    column_sortable_list = ("name", "type")
    form=UserForm




class EventsForm(form.Form):

    name=fields.StringField("Etkinlik Adı")
    start_date=fields.StringField("Başlama tarihi")
    start_time=fields.StringField("Başlama Saati")
    end_date = fields.StringField("Bitiş tarihi")
    end_time = fields.StringField("Bitiş Saati")
    description=fields.StringField("Açıklama")
    category=fields.StringField("Kategori")
    subcategory=fields.StringField("Alt Kategori")
    price=fields.FloatField("Ücret")
    currency=fields.StringField("Ücret Birimi")
    event_place_id=fields.StringField("Etkinlik Yeri id")



class EventsView(ModelView):

    def is_accessible(self):
        if session and session['type']=='admin':
            return True
        else:
            return False
    column_list = ('_id','name', 'start_date', 'start_time','category','subcategory','price','currency','event_place_id')
    column_sortable_list = ('name', 'start_date', 'start_time','category','subcategory','price','currency','event_place_id')

    form = EventsForm


class MyHomeView(AdminIndexView):
    def is_accessible(self):
        if session and session['type']=='admin':
            return True
        else:
            return False
    @expose('/')
    def index(self):
        arg1, arg2= eventDateRange()
        arg3=session['username']
        arg4=events.find().count()
        arg5=places.find().count()
        return self.render('home.html', arg1=arg1, arg2=arg2, arg3=arg3, arg4=arg4, arg5=arg5)

class StatisticView(BaseView):
    def is_accessible(self):
        if session and session['type']=='admin':
            return True
        else:
            return False
    @expose('/')
    def index(self):

        return self.redirect(url_for('render_statistic'))


###################################################################################
#######################################################################################

if __name__ == '__main__':

    admin = Admin(app,index_view=MyHomeView(),name='Admin')

    # Add views
    admin.add_view(PlacesView(places, 'Etkinlik Yerleri', endpoint="etkinlik yerleri"))
    admin.add_view(EventsView(events, 'Etkinlikler', endpoint="etkinlikler"))
    admin.add_view(UserView(users, 'Kullanıcılar', endpoint="kullanıcılar"))
    admin.add_view(StatisticView('İstatistikler', url='/statistic'))
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))

    run_simple('127.0.0.1', 5000, event_app, use_reloader=True, use_debugger=True)


