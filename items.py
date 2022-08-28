# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class TIDWordItem(scrapy.Item):
    # define the fields for your item here like:
    id = scrapy.Field()
    tr_word = scrapy.Field()
    desc_eng = scrapy.Field()
    # video = scrapy.Field()
    source_url = scrapy.Field()
    examples = scrapy.Field()
        # types = scrapy.Field()
        # description = scrapy.Field()
        # sign_movement = scrapy.Field()
        # desc_vid = scrapy.Field()
        # sample_transcipts = scrapy.Field()
        # sample_vid = scrapy.Field()
    pass