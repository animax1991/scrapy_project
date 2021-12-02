# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy







class RentalItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    id = scrapy.Field()
    url = scrapy.Field()
    propertytype = scrapy.Field()
    description = scrapy.Field()
    rooms = scrapy.Field()
    bedrooms = scrapy.Field()
    bathrooms = scrapy.Field()
    street = scrapy.Field()
    streetnr = scrapy.Field()
    price = scrapy.Field()
    zipcode = scrapy.Field()
    city = scrapy.Field()
    province = scrapy.Field()
    lat = scrapy.Field()
    lon = scrapy.Field()
    photos = scrapy.Field()
    thumbnails = scrapy.Field()
    status = scrapy.Field()
    construction_type = scrapy.Field()
    construction_year = scrapy.Field()
    deposit = scrapy.Field()
    livingsurface = scrapy.Field()
    totalvolume = scrapy.Field()
    features = scrapy.Field()
    parking = scrapy.Field()
    furnishedstate = scrapy.Field()
    energylabel = scrapy.Field()
    servicecosts = scrapy.Field()
    

    pass
