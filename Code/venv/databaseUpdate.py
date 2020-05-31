# -*- coding: utf-8 -*-
import traceback

import re
from selenium import webdriver
import json
from bs4 import BeautifulSoup
from selenium.common.exceptions import InvalidArgumentException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox.options import Options
import pymongo
import datetime
from datetime import timedelta
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import requests
import re
from pymongo import GEOSPHERE
import time
import urllib.request
import json
import sys


myclient = pymongo.MongoClient("mongodb://localhost:27017/")

eventMapDB = myclient["eventMapDB"]
events = eventMapDB["events"]
places = eventMapDB["places"]
#places.ensure_index([("location", pymongo.GEOSPHERE)])



#x = events.insert_one(event)
for i in events.find():
    print(i)
for i in places.find():
    print(i)




url="http://www.biletix.com/search/TURKIYE/tr?category_sb=-1&date_sb=-1&city_sb=-1"
url_tff="http://www.tff.org/default.aspx?pageID=322"




def fetch_url(url,num_of):
    if(num_of==-2):
        return -1
    options = Options()
    options.add_argument("--headless")
    browser = webdriver.Firefox(firefox_options=options)#
    browser.get(url)
    filter = browser.find_element_by_xpath("//div[@id='search_results']/div[6]")
    browser.execute_script("arguments[0].click();", filter)



    date = str(datetime.datetime.now()).split(" ")[0]

    day_now = date.split("-")[2]
    month_now = date.split("-")[1]
    year_now = date.split("-")[0]




    counter=31

    driver = webdriver.Firefox(firefox_options=options)#
    #################################################################################################################
    while(counter==31 and num_of!=0):
        year = date.split("-")[0]
        month = date.split("-")[1]
        day = date.split("-")[2]



        start = browser.find_element_by_xpath("//input[@class='sDateInput hasDatepicker' and @id='start']")
        start.clear()
        #browser.execute_script("arguments[0].click();",start)
        #browser.execute_script("arguments[0].removeAttribute('readonly')", start)
        start.send_keys(day+"/"+month+"/"+year)
        start.send_keys(Keys.TAB)
    #javascript_click().send_keys("03/05/2013")


        #first_option = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.XPATH,"//div[@id='ui-datepicker-div']//td[@data-year="+"10"+"][@data-month="+"10"+"]/a[@class='ui-state-default'][text()="+"2018"+"]")))
        #first_option.click()

        #start.send_keys()
        #start.send_keys("10/10/2018")

        #wait.until(lambda browser: browser.find_element_by_xpath("//div[@id='ui-datepicker-div']"))
        #start.find_element_by_xpath("//div[@id='ui-datepicker-div']//td[@data-year="+year+"][@data-month="+month+"]/a[@class='ui-state-default'][text()="+day+"]")
        #start.send_keys(day+month+year) #bugunun tar

        #browser.execute_script("arguments[0].removeAttribute('readonly')", end)

        end = browser.find_element_by_xpath("//input[@class='sDateInput hasDatepicker' and @id='end']")
        end.clear()
        end.send_keys(day_now+"/"+month_now+"/"+str(int(year_now)+2)) # bugun+ 2 sene tar"""
        end.send_keys(Keys.ENTER)
        searchButton = browser.find_element_by_name('j_id131')
        browser.execute_script("arguments[0].click();", searchButton)

        time.sleep(20)
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Going through pagination
        pages_remaining = True
        counter = 1
        while pages_remaining:


            events = soup.findAll("div", {"class": "searchLinkDiv"})

            for x in range(1,len(events)):
                try:
                    event_url='http://www.biletix.com'+str(events[x]).split("'")[1]
                    #print(str(events[x]).split("'")[1])


                    if str(events[x]).split("/")[1].split("-")[-1] != "grup":
                        event_source_id = str(events[x]).split("/")[2]
                        #print("event source id:" + event_source_id)

                        event_html,isCancelled=getEventHtml(event_url,driver)
                        soup_evnt = BeautifulSoup(event_html, "html.parser")

                        truncated_description, description, irregular_cdata_list,place_url=getEventData(driver,soup_evnt)


                        #print(description)
                        #print(truncated_description)
                        #print(irregular_cdata_list)

                        price,currency=getPrices(soup_evnt)
                        category, subcategory, event_name, picture_html, place_name, place_city, place_country, latitude, longitude, start_date, start_time, end_date, end_time=irrToData(irregular_cdata_list)

                        addEventToDb(event_source_id,event_name,description,category,subcategory,picture_html,price,currency,place_name,place_country,place_city,latitude,longitude,start_date,end_date,start_time,end_time,place_url,driver,isCancelled)

                except WebDriverException:
                    print("WEB DRIVER Exception")
                except:
                    print("There is a problem!")
                    traceback.print_exc()





            try:
                counter+=1
                path='//*[@href="javascript:gotoPage('+str(counter)+')"]'
                next_link = browser.find_element_by_xpath(path)
                browser.execute_script("arguments[0].click();", next_link)
                html = browser.page_source
                soup = BeautifulSoup(html, "html.parser")
                #time.sleep(10)
            except NoSuchElementException:
                if(date!=start_date):
                    #print(date)
                    #print(start_date)
                    date=start_date
                else:
                    date=str(datetime.datetime.strptime(date, "%y-%m-%d")+timedelta(days=1))
                num_of-=1
                #print(counter)
                pages_remaining = False

def fetch_tff(url):

    options = Options()
    options.add_argument("--headless")

    browser = webdriver.Firefox()#firefox_options=options

    browser.get(url)
    time.sleep(15)
    filter = browser.find_element_by_xpath("//*[@id='ctl00_MPane_m_322_1480_ctnr_m_322_1480_RadTabStrip1_Tab3']")
    browser.execute_script("arguments[0].click();", filter)


    date = str(datetime.datetime.now()).split(" ")[0]

    day_now = date.split("-")[2]
    month_now = date.split("-")[1]
    year_now = date.split("-")[0]
    date_now=day_now+"."+month_now+"."+year_now

    time.sleep(5)
    date_in= browser.find_element_by_xpath("//*[@id='ctl00_MPane_m_322_1480_ctnr_m_322_1480_DonemSelector2_dateBaslangic_dateInput_TextBox']")
    browser.execute_script("arguments[0].click();", date_in)

    browser.execute_script("arguments[0].value = "+"'"+date_now+"'"+";", date_in)

    #date_in.send_keys(date_now)
    #date_in.send_keys(Keys.TAB)
    time.sleep(5)


    lig=browser.find_element_by_xpath("//*[@id='ctl00_MPane_m_322_1480_ctnr_m_322_1480_LigSelector1_combo_Input']")
    browser.execute_script("arguments[0].click();", lig)
    lig.send_keys(Keys.ENTER)

    browser.back()
    browser.forward()
    time.sleep(5)

    for x in range(3):
        ara=browser.find_element_by_xpath("//*[@id='ctl00_MPane_m_322_1480_ctnr_m_322_1480_btnSave3']")
        browser.execute_script("arguments[0].click();", ara)
        time.sleep(7)

        table=browser.find_element_by_xpath("/html/body/form/table/tbody/tr[2]/td[1]/table/tbody/tr/td[2]/table/tbody/tr[2]/td[2]/table/tbody/tr/td[1]/div[2]/table[2]/tbody/tr/td/fieldset/div/table/tbody")

        results=table.find_elements_by_tag_name("tr")
        for i in results:
            row=i.find_elements_by_tag_name("td")
            id=row[0].text
            t1= row[1].text
            t2=row[3].text
            tarih = row[4].text
            d=tarih.split(".")[0]
            m = tarih.split(".")[1]
            y=tarih.split(".")[2]
            tarih=y+"-"+m+"-"+d
            saat = row[5].text
            stad_name=row[6].text

            longitude=""
            latitude=""
            city=""

            r = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyD1FwJCRkIeTDeAsMHe0KCUBDHRrFG0u1w&address=" + stad_name)

            if (len(r.json()["results"]) != 0):
                # print(r.json())

                longitude = str(r.json()["results"][0]["geometry"]["location"]["lng"])
                latitude = str(r.json()["results"][0]["geometry"]["location"]["lat"])
                ad_comp=r.json()["results"][0]["address_components"]
                len_com=len(ad_comp)

                k=0
                while(k<len_com and ad_comp[k]["types"][0]!='administrative_area_level_1'):
                    k+=1

                if (k!=len_com):
                    city=ad_comp[k]["long_name"]


                print(longitude)
                print(latitude)
                print(city)


            addEventToDb(id, t1+"-"+t2, "", "SPORT", "Futbol", "", 0, "",
                         stad_name, "Türkiye", city, latitude, longitude, tarih, tarih, saat,
                         saat, "", browser, 0)

        lig = browser.find_element_by_xpath(
                "//*[@id='ctl00_MPane_m_322_1480_ctnr_m_322_1480_LigSelector1_combo_Input']")
        browser.execute_script("arguments[0].click();", lig)
        lig.send_keys(Keys.ARROW_DOWN)
        lig.send_keys(Keys.ENTER)

        #print("id:"+id+"t1:"+t1+"t2:"+t2+"tarih:"+tarih+"saat:"+saat+"stad_name:"+stad_name)



def getEventHtml(event_url,driver):


    driver.get(event_url)

    event_html = driver.find_element_by_tag_name('html').get_attribute('innerHTML')
    isCancelled=0
    isCancelledfind=len(driver.find_elements_by_css_selector(".eventNosMessage.eventNosMessage_s04_canceled"))

    if isCancelledfind!=0:
        isCancelled=1




    return event_html, isCancelled

def getEventData(driver,soup_evnt):
    truncated_description = driver.find_element_by_name('description').get_attribute('content')
    place_url=soup_evnt.find("a", {"itemprop":"url"})["href"]
    place_url="http://www.biletix.com"+place_url

    description = soup_evnt.find("div", {"id": "ei_header"}).find("meta", {"itemprop": "description"})['content']
    data = soup_evnt.findAll("script", {"type": "text/javascript"})
    js_obj = str(data[40]).split("var RondavuData = ")[1].replace("//]]>", "").replace("</script>", "").replace("};","}")
    irregular_cdata_list = [s.strip() for s in js_obj.splitlines()]

    return truncated_description, description, irregular_cdata_list,place_url

def getPrices(soup_evnt):
    price_list=[]
    prices = soup_evnt.findAll("span", {"itemprop": "price"})
    for i in prices:
        is_price=i.getText().split(" ")
        for j in range(0,len(is_price)):
            try:
                price_list.append(float(is_price[j]))
                currency=is_price[j+1]
            except ValueError:
                pass
    if (len(price_list)!=0):
        price_list.sort()
        price=(price_list[0])
    else:
        price=0
        currency=""

    #print(price)
    #print(currency)
    return price, currency

def irrToData(cdata_list):
    i=0
    while i<len(cdata_list) and (len(cdata_list[i])>16 and cdata_list[i][:16]=="ctgry_subctgry :")==False:
        i+=1

    cat_sub= cdata_list[i].split("\"")[3]
    category=cat_sub.split("$")[1]
    subcategory=cat_sub.split("$")[0]
    #print(category)
    #print(subcategory)

    while i<len(cdata_list) and (len(cdata_list[i])>14 and cdata_list[i][:14]=="name : [{name:")==False:
        i+=1

    event_name = cdata_list[i].split("\"")[1]
    #print(event_name)

    while i<len(cdata_list) and (cdata_list[i]!="picture: {"):
        i+=1
    i += 1
    picture_html=cdata_list[i].split("\"")[1]
    #print(picture_html)

    while i<len(cdata_list) and (cdata_list[i]!="location: {"):
        i+=1
    i+=1
    place_name = cdata_list[i].split("\"")[1]
    i += 1
    place_city=cdata_list[i].split("\"")[1]
    i+=2
    place_country=cdata_list[i].split("\"")[1]
    i += 2
    latitude = cdata_list[i].split("\"")[1]
    i += 1
    longitude = cdata_list[i].split("\"")[1]

    print("place name:"+place_name)
    print("place city:" + place_city)
    #print("place country:" + place_country)
    print("latitude:" + latitude)
    print("longitude:" + longitude)

    while i<len(cdata_list) and (cdata_list[i]!="product_date : [ {"):
        i+=1
    i+=2
    start_date=cdata_list[i].split("\"")[1]
    i+=1
    start_time=cdata_list[i].split("\"")[1]
    i+=4
    end_date = cdata_list[i].split("\"")[1]
    i += 1
    end_time = cdata_list[i].split("\"")[1]

    print("start date:" + start_date)
    """print("start time:" + start_time)
    print("end date:" + end_date)
    print("end time:" + end_time)"""

    return category,subcategory,event_name,picture_html,place_name,place_city,place_country,latitude,longitude,start_date,start_time,end_date,end_time

def getCapasity(placename,city,place_url,driver):
    name=placename.strip().split(" ")
    #print(placename)
    #print(name)
    result=-1
    placename=""
    for i in name:
        if(i!=""):
            placename+=i+"+"
    placename+=city.strip()
    #print(placename)

    try:
        driver.get(place_url)
        source_place = driver.find_element_by_class_name("e_info").get_attribute('innerHTML')
        source_text="".join(source_place.split())

        #print(source_text)


        # match = re.findall(r"apasite.*", txt)
        match = re.findall(r"apasite[^0-9]*" + "\d+" + "." + "\d\d\d+", source_text)
        match2 = re.findall(r"\d+" + "." + "\d+" + "kişi", source_text)
        match4 = re.findall(r"\d\d+" + "kişi", source_text)
        match3 = re.findall(r"\d+" + "." + "\d\d\d+" + "kapasite[^0-9]*", source_text)
        #print(match2)
        #print(match3)
        capasities = []
        for i in match + match2 + match3 + match4:
            digit = re.sub(r"\D", "", i)
            # digit=re.search(r"[^0-9]*",i).group()
            capasities.append(int(digit))
        if(len(capasities)!=0):
            result=max(capasities)
    except InvalidArgumentException:
        pass


    wikipedia=requests.get("https://www.wikizero.com/search.php?s="+placename+"&lang=tr").text
    soupWiki=BeautifulSoup(wikipedia,'lxml')

    divdata = soupWiki.findAll('div',attrs={'class':'mw-search-result-heading'})

    try:
        link = divdata[0].find('a')["href"]
        link="https://www.wikizero.com/"+link
        wikipage=requests.get(link).text
        soupPage=BeautifulSoup(wikipage,'lxml')
        txt=""
        divpage = soupPage.findAll('div',attrs={'class':'mw-parser-output'})
        for d in divpage:
            txt+="".join(d.text.split())
        #print("---------------------------------------------------------------------------------------------------------")
        #print(link)
        #print(txt)

        structured=re.search(r"Kapasite\d+"+"."+"\d+",txt)

        if (structured is not None):
            result=int(re.sub(r"\D","",structured.group()))


    except IndexError:
        print("sonuc yok!")


    return result


def addEventToDb(event_source_id,name,description,category,subcategory,picture_url,price,currency,place_name,place_country,place_city,latitude,longitude,start_date,end_date,start_time,end_time,place_url,driver,isCancelled):
    isThereEvent=events.find_one({"event_source_id":event_source_id})
    if(isThereEvent==None):
        if (isCancelled == 0):
            event_place_id=addEventPlaceToDb(place_name,place_country,place_city,latitude,longitude,place_url,driver)
            event = {"event_source_id":event_source_id, "name": name, "description":description,"category":category,"subcategory":subcategory,"picture_url":picture_url,"price":price,"currency":currency,"event_place_id":event_place_id,"start_date":start_date,"end_date":end_date,"start_time":start_time,"end_time":end_time}
            events.insert_one(event)
    else:
        if(isCancelled==0):
            print("update ediyor")
            events.update_one({
                "event_source_id": event_source_id
            }, {
                '$set': {
                    "name": name, "price": price, "currency": currency,
                    "start_date": start_date, "end_date": end_date, "start_time": start_time, "end_time": end_time,
                }
            }, upsert=False)
        else:
            print("siliniyor")
            events.delete_one({"event_source_id": event_source_id})



def addEventPlaceToDb(place_name,place_country,place_city,latitude,longitude,place_url,driver):
    isTherePlace = places.find_one({"place_name": place_name, "place_country": place_country, "place_city": place_city})

    if (isTherePlace != None):

        return isTherePlace.get("_id")

    district = ""
    latitude = re.sub('\s+', ' ', latitude)
    longitude = re.sub('\s+', ' ', longitude)
    capasity = getCapasity(place_name, place_city, place_url,driver)

    r = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyD1FwJCRkIeTDeAsMHe0KCUBDHRrFG0u1w&address=" + place_name + " " + place_city)


    if(longitude=="" and latitude==""):

        if (len(r.json()["results"]) != 0):
            longitude = str(r.json()["results"][0]["geometry"]["location"]["lng"])
            latitude = str(r.json()["results"][0]["geometry"]["location"]["lat"])



    if (longitude != "" and latitude != ""):

        if (len(r.json()["results"]) != 0):
            #print(r.json())

            ad_comp=r.json()["results"][0]["address_components"]
            len_com=len(ad_comp)
            k = 0
            while (k<len_com and ad_comp[k]["types"][0] != 'administrative_area_level_2'):
                k += 1
            if (k!=len_com):

                district = ad_comp[k]["long_name"].split(" ")[0]
            else:
                district=place_city


        latitude=float(latitude)
        longitude=float(longitude)
        loc = {"type": "Point", "coordinates": [longitude, latitude]}
        if(capasity!=-1):

            place = {"place_name": place_name, "place_country": place_country, "place_city": place_city,
                     "place_district": district, "location": loc, "capasity": capasity}

        else:
            place = {"place_name": place_name, "place_country": place_country, "place_city": place_city,
                     "place_district": district, "location": loc}

    else:
        if(capasity!=-1):

            place = {"place_name": place_name, "place_country": place_country, "place_city": place_city, "place_district":district, "capasity": capasity}
        else:
            place = {"place_name": place_name, "place_country": place_country, "place_city": place_city,
                     "place_district": district}



    places.insert_one(place)

    return places.find_one(place).get("_id")
#bu fonku silebilirsin
def loc():
    for place in places.find():

        place_name=place["place_name"]
        place_city=place["place_city"]
        r = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyD1FwJCRkIeTDeAsMHe0KCUBDHRrFG0u1w&address=" + place_name + " " + place_city)

        if("location" in place.keys()):

            if (len(r.json()["results"]) != 0):
                longitude = str(r.json()["results"][0]["geometry"]["location"]["lng"])
                latitude = str(r.json()["results"][0]["geometry"]["location"]["lat"])






                places.update_one({
                    "place_name":place_name, "place_city":place_city
                }, {
                    '$set': {
                        'location': {'type': 'Point', 'coordinates': [float(longitude), float(latitude)]

                    }
                }
                }, upsert=False)


def dbClean():
    for place in places.find():

        place_name=place["place_name"]
        place_city=place["place_city"]
        r = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyD1FwJCRkIeTDeAsMHe0KCUBDHRrFG0u1w&address=" + place_name + " " + place_city)

        district = place_city
        if (len(r.json()["results"]) != 0):
            ad_comp = r.json()["results"][0]["address_components"]
            len_com = len(ad_comp)
            k = 0
            while (k < len_com and ad_comp[k]["types"][0] != 'administrative_area_level_2'):
                k += 1
            if (k != len_com):
                district = ad_comp[k]["long_name"].split(" ")[0]
                print(district)
            else:
                k=0
                while (k < len_com and ad_comp[k]["types"][0] != 'administrative_area_level_3'):
                    k += 1
                if (k != len_com):
                    district = ad_comp[k]["long_name"].split(" ")[0]
                    print(district)
                else:
                    k = 0
                    while (k < len_com and ad_comp[k]["types"][0] != 'administrative_area_level_4'):
                        k += 1
                    if (k != len_com):
                        district = ad_comp[k]["long_name"].split(" ")[0]
                        print(district)


            print(district)





            longitude = str(r.json()["results"][0]["geometry"]["location"]["lng"])
            latitude = str(r.json()["results"][0]["geometry"]["location"]["lat"])





            places.update_one({
                "place_name":place_name, "place_city":place_city
            }, {
                '$set': {
                    'location': {'type': 'Point', 'coordinates': [float(longitude), float(latitude)],
                    "place_district": district
                }
            }
            }, upsert=False)



        print(place)

fetch_url(url,int(sys.argv[1]))
fetch_tff(url_tff)
############################################db temizleme###########################################################
#dbClean()
#####################################################################################################################
#loc()
#fetch_url(url,int(sys.argv[1]))
#fetch_tff(url_tff)

#dbClean()
#places.update({}, {"$unset": {"district": 1}},multi= True)
#places.delete_many({"place_name":""})
#places.delete_one({"place_name":"ÜMRANİYE BELEDİYESİ ŞEHİR STADI - İSTANBUL"})
#events.delete_many({"$and":[{"$or":[ {"category":"SPOR"}, {"category":"SPORT"}]},{"description": { "$exists": False }}]})
"""
for place in places.find():

    if (place["place_name"].isupper()):
        
        #places.delete_one({"place_name": place["place_name"]})
"""
"""
for i in f:
    print (i)"""
#places.delete_many({"place_name":" "})

"""else:
    #match = re.findall(r"apasite.*", txt)
    match = re.findall(r"apasite[^0-9]*"+"\d+"+"."+"\d+",txt)
    match2=re.findall(r"\d+"+"."+"\d+"+"kişi",txt)
    match3 = re.findall(r"\d+" + "." + "\d+" + "kapasite[^0-9]*" , txt)
    print(match2)
    print(match3)
    capasities=[]
    for i in match+match2+match3:
        digit=re.sub(r"\D","",i)
        #digit=re.search(r"[^0-9]*",i).group()
        capasities.append(int(digit))
    if (len(capasities)==0):

        result=-1
    else:
        result = max(capasities)"""

