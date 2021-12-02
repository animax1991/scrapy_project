import json
import re
import os

import scrapy
import time
from scrapy_splash import SplashRequest
from scrapy.selector import Selector
from scrapy.http import HtmlResponse

from ..settings import Zyte_Splash_API_Key

from .myitems import RentalItem

#https://stackoverflow.com/questions/28852057/change-ip-address-dynamically
#https://stackoverflow.com/questions/40543892/how-to-set-cookies-in-scrapysplash-when-javascript-makes-multiple-requests

class KeizerSpider(scrapy.Spider):
    name = 'keizer'

    test = Zyte_Splash_API_Key
    #http_user = settings.Zyte_Splash_API_Key
    allowed_domains = ['keizerskroonmakelaars.nl']
    start_urls = ['https://www.keizerskroonmakelaars.nl/huurwoningen']

    def start_requests(self):
        # lua script for scroll to bottom while all objects appeared

        #optionally add to 'main' function below: splash.private_mode_enabled = false
        lua_script = """
        function main(splash, args)
          local url = splash.args.url
          splash:go(url)
          splash:wait(0.5)
          return splash:html()
        end
        """

        # yield first splash request with lua script and parse it from parse def
        yield SplashRequest(
            self.start_urls[0], self.parse,
            endpoint='execute',
            args={'lua_source': lua_script},
        )

    def parse(self, response):
        # get all properties from first page which was generated with lua script
        # get all adreslink from a tag
        object_links = response.css('a.adreslink::attr(href)').getall()
        for link in object_links:
            # send request with each link and parse it from parse_object def
            yield scrapy.Request(link, self.parse_object)

    def parse_object(self, response):
        # create new RentalItem which will saved to json file
        item = RentalItem()

        item['url'] = response.url # get url        
        item['street'] = response.css('span.adres::text').get().strip() # get adres        
        item['city'] = response.css('span.plaatsnaam::text').get().strip() # get plaatsaam

        # get price
        price_h2 = response.css('div.detail_prijs h2::text').get()
        #   filter only value from price h2 text
        if price_h2:
            price_re = re.search(r"(.*)€ (.*) per maand", price_h2)
            try:
                price = price_re.group(2).replace('.', '')
                item['price'] = float(price)
            except:
                item['price'] = 0
        else:
            item['price'] = 0

        # get status, deposit, construction type from object-features
        item['bathrooms'] = 0
        item['bedrooms'] = 0
        item['construction_type'] = ''
        item['deposit'] = 0
        item['energylabel'] = ''
        item['features'] = ''
        item['furnishedstate'] = ''
        item['livingsurface'] = 0
        item['propertytype'] = ''
        item['rooms'] = 0
        item['status'] = ''


        item['lat'] = ''
        item['lon'] = ''
        item['id'] = 0
        
        #find this element:
        #<input type="hidden" id="mgmMarker202012160946376923" name="mgmMarker202012160946376923" value="202012160946376923~1~52.37396877,4.90513487~1011AN~Amsterdam~Amsterdam~Prins Hendrikkade~127~A~WH~1~Beneden/bovenwoningen~Prins Hendrikkade 127 A Amsterdam ~<b>Huurprijs</b><br/>&euro; 1.675&nbsp;per maand~1675~per maand~huurprijs~1.675~https://www.keizerskroonmakelaars.nl/prins-hendrikkade-127a-amsterdam-202012160946376923~https://bb3.goesenroos.nl/Keizerskroon/WONEN/202012160946376923/DSCF0693.JPG~0~1~16/12/2020~1">
        
        hiddenField = response.css('[id^=mgmMarker]::attr(value)').get().strip().split('~')

        item['id'] = hiddenField[0]
        item['lat'] = hiddenField[2].split(',')[0]
        item['lon'] = hiddenField[2].split(',')[1]
        item['zipcode'] = hiddenField[3]

        object_features = response.css('div#object-features div.object-feature')
        for feature in object_features:
            try:
                feature_title = feature.css('div.features-title::text').get().strip()
                feature_info = feature.css('div.features-info::text').get().strip()
                
                if feature_title == 'Energielabel':
                    feature_info = feature.css('div.features-info span::text').get().strip()

                if feature_title and feature_info:
                    if feature_title == 'Status':
                        item['status'] = feature_info
                    elif feature_title == 'Bouwtype':
                        item['construction_type'] = feature_info
                    elif feature_title == 'Soort woning':
                        item['propertytype'] = feature_info
                    elif feature_title == 'Specifiek':
                        item['furnishedstate'] = feature_info
                    elif feature_title == 'Gebruiksoppervlak wonen':
                        item['livingsurface'] = int(feature_info.replace('m²','').strip())
                    elif feature_title == 'Totaal aantal kamers':
                        item['rooms'] = int(feature_info)
                    elif feature_title == 'Aantal slaapkamers':
                        item['bedrooms'] = int(feature_info)
                    elif feature_title == 'Aantal badkamers':
                        item['bathrooms'] = int(feature_info)
                    elif feature_title == 'Energielabel':
                        item['energylabel'] = feature_info
                    elif feature_title == 'Waarborgsom':
                        item['deposit'] = float(feature_info.replace('€ \xa0 ', ''))
                    elif (
                        feature_title == 'Voorzieningen badkamer' or feature_title == 'Voorzieningen' or feature_title == 'Isolatie' or feature_title == 'Soort verwarming' or 
                        feature_title == 'Warm water' or feature_title == 'Ligging' or feature_title == 'Soort garage' or feature_title == 'Soort parkeergelegenheid'
                    ):
                        item['features'] += feature_info + ' '

            except:
                continue

        #item['photothumbs'] = response.css("section#object-all-photos img::attr(src)").getall() # get photos from object-all-photos
        descriptions = response.css('div.object-detail-description::text').extract()# get description from object-detail-description extract all text in html text
        #   join all sub strings and insert to description
        item['description'] = '\n'.join([d_item.strip() for d_item in descriptions])

        item['thumbnails'] = response.css("section#object-all-photos img::attr(src)").getall() #e.g. https://bb3.goesenroos.nl/Keizerskroon/WONEN/202012091419390038/_thumbs/Bestanden/1.jpg

        photo_href = response.css("section#object-all-photos a::attr(data-src)").get() #e.g. https://www.keizerskroonmakelaars.nl/huizen/202012091419390038/allfoto.htm
        if photo_href:
            print('hello',photo_href)
            yield scrapy.Request(photo_href, self.parse_photos, meta={'item': item})
            # We use `item` to contain all info of one object.
            # In parse_object method, we scrapped all data except large photos, and stored one to object named `item`.
            # yield scrapy.Request(photo_href, self.parse_photos, meta={'item': item}) means we are going to scrape large photos in `parse_photos` method with `url photo_href`.
            # Here `meta={'item': item}` means pass item used in parse_objects to parse_photos.
            # So that we can store large photos to one same item which are storing other infos except large photos
        else:
            print("nophoto")

    def parse_photos(self, response):
        image_tags = response.css('img')
        item = response.meta['item'] 
        # In parse_photos method, we derived item from parse_object method and use same item to store large-photos. 
        # In `item = response.meta['item']` , response.meta['item'] equals item in parse_object\
        # all thumbnails and large photos are in same sequence, so no need to work with indices
        item['photos'] = []
        for img in image_tags:
            item['photos'].append(img.attrib['src'])
        yield item
