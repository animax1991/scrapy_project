import json
import re
import os

import scrapy
import time
from scrapy_splash import SplashRequest
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
from scrapy.crawler import CrawlerProcess

from ..myitems import RentalItem

class MyTest_Spider(scrapy.Spider):
    name = 'mytest'
    #http_user = settings.Zyte_Splash_API_Key
    start_urls = ['https://www.govaert.nl/verhuur/huis-huren/']

    def start_requests(self):
  
        # yield first splash request 
        yield SplashRequest(
            self.start_urls[0], self.parse
        )

    def parse(self, response):
        # get all properties from first page which was generated with lua script
        # get all adreslink from a tag
        object_links = response.css('div.wrapper div.inner33 > a::attr(href)').getall()

        #todo: only follow links that do NOT have label "onder optie"
        for link in object_links:
            # send request with each link and parse it from parse_object def
            yield scrapy.Request(link, self.parse_object)

        next_page = response.css('div.nav-links a.next.page-numbers::attr(href)').get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)


    def parse_object(self, response):
        # create new RentalItem which will saved to json file
        item = RentalItem()

        item['url'] = response.url # get url        

        object_features = response.css('table.info tr')
        for feature in object_features:
            try:
                feature_title = feature.css('th::text').get().strip()
                feature_info = feature.css('td::text').get().strip()
                
                if feature_title and feature_info:
                    if feature_title == 'Adres':
                        item['street'] = feature_info.split(',')[0]
                        #item.city = feature_info.split(',')[1].strip().capitalize()
                    # if feature_title == 'Prijs':
                    #     item.price = 0 
                    #     price_re = rice_re = re.search(r"€(\d[\d.,]*)\b", price, feature_info)
                    #     try:                            
                    #         price = str(price_re).strip().replace('€', '').replace(',00', '').replace('.', '')
                    #         item.price = int(price)
                    #     except:
                    #         item.price = 0                            


            except:
                continue

        item['photos'] = response.css('ul#objects li a::attr(href)').getall
        item['thumbnails'] = response.css("ul#objects li a img::attr(src)").getall()

        yield item


# process = CrawlerProcess()
# process.crawl(MyTest_Spider)
# process.start()
#
