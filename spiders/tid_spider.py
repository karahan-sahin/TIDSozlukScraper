from doctest import Example
from gc import callbacks
import scrapy
import math
import re 

from tid_sozluk.items import TIDWordItem

class SignSpider(scrapy.Spider):
    name = "tid_spider"

    def start_requests(self):
        urls = [
            f'http://tidsozluk.net/tr/Alfabetik/Arama/{char.capitalize()}?p=1'
                for char in 'A'#'ABCÇDEFGHIİJKLMNOÖPRSŞTUÜVWYZ'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        
        # Count total words
        total_pages = math.ceil(int(response.xpath("//div[@id='rezults_summ']//b/text()").get()) / 10)
        current_page = int(response.url.split("?")[-1].split("=")[1])
        
        words = response.xpath("//div[contains(@class,'rezult_item')]//h3/text()")
        desc_eng = response.xpath("//div[contains(@class,'rezult_item')]//span/text()")
        
        # Initially group them by their code -> multiple signs
        # /vidz_proc/1299/degiske/1299-01_cr_0.1.mp4 ->  /vidz_proc/1299/degiske/1299-01_cr_0.1.mp4 
        videos = ["http://tidsozluk.net/"+url.get() for url in response.xpath("//div[contains(@class,'rezult_item')]//source/@src")] 
        ids, videos = self.stack_url(videos)
        word_url = response.xpath("//div[contains(@class,'rezult_item')]/a/@href")
        
        print(len(ids), len(words), len(desc_eng), len(videos), len(word_url))
        for id, word, desc, url in zip(ids, words, desc_eng, word_url):
            url = "http://tidsozluk.net/"+url.get()
            yield scrapy.Request(url, 
                                 callback= self.parse_results,
                                 meta={
                                    "id": id,
                                    "word":word.get(), 
                                    "desc":desc.get(), 
                                    # "vid":vid, 
                                    "url":url
                                })
        
        if current_page < total_pages:
            next_page = response.url.split("?")[0] + f"?p={current_page+1}"
            yield scrapy.Request(url=next_page, 
                                 callback=self.parse)

    
    def parse_results(self, response):
        
        item = TIDWordItem()
        item["id"] = response.meta["id"]
        item["tr_word"] = response.meta["word"]
        item["desc_eng"] = response.meta["desc"]
        # item["video"] = response.meta["vid"]
        item["source_url"] = response.meta["url"]
        # word type
        types = [i.get() for i in response.xpath("//div[contains(@class,'container-fluid')]//span[contains(@class,'badge_tur')]/text()")] #word_type
        # word description (Turkish)
        description = [i.get() for i in response.xpath("//div[contains(@class,'container-fluid')]//span[contains(@class,'badge_tur')]/following-sibling::span[1]/text()")] # Meaning
        # Description video
        desc_vid = response.xpath("//source[contains(@src, 'ornek')]/@src") # meaning sign

        # Meaning form in handshape        
        sign_movement = []
        for div in range(2,len(response.xpath(f"/html/body/div[2]/div"))+1):
            shapes = []
            for s in range(1,len(response.xpath(f"/html/body/div[2]/div[{div}]/div[2]/div[2]/div"))+1):
                points = response.xpath(f"/html/body/div[2]/div[{div}]/div[2]/div[2]/div[{s}]//img/@src").get()
                print(points)
                motion = {}
                for sh in points:
                    print(sh[len("/imgz/degiske_el-konum/"):-4].split("/"))
                    place, shape = sh[len("/imgz/degiske_el-konum/"):-4].split("/")
                    motion[place] = shape
                shapes.append(motion)

            sign_movement.append(shapes)


        # Direct Translation (Turkish)
        sample_translations = response.xpath(f"//div[contains(text(), 'Çeviri: ')]/following-sibling::div[1]/text()")
        # Intermediate Translation (TID-Tr)
        sample_transcipts = response.xpath(f"//div[contains(text(), 'TRANSKRİPSİYON: ')]/following-sibling::div[1]/text()")
        # Video link 
        sample_vid = response.xpath("//source[contains(@src, 'ornek')]/@src")

        examples = []
        for i in zip(types,description,desc_vid,sample_translations,sample_transcipts,sample_vid,sign_movement):
            examples.append({
                "type" : i[0],
                "description" : i[1],
                "desc_vid" : i[2].get(),
                "sample_tranlation" : i[3].get(),
                "sample_transcipt" : i[4].get(),
                "sample_vid" : i[5].get(),
                "sign_movement" : i[6]
            })
        
        item["examples"] = examples

        yield item



    def stack_url(self, urls):
        stacked = []
        url_prev = ""
        ids = []
        url_stack = []
        for url in urls:
            if url_prev:
                if re.findall("/vidz_proc/(.+?)/", url) == re.findall("/vidz_proc/(.+?)/", url_prev):
                    url_stack.append(url)
                else:
                    if url_stack:
                        stacked.append(url_stack)
                        url_stack = []
                    else:
                        stacked.append(url)
                        ids.append(re.findall("/vidz_proc/(.+?)/", url)[0])
            else:
                stacked.append(url)
                ids.append(re.findall("/vidz_proc/(.+?)/", url)[0])
        
        _ids = []
        [_ids.append(x) for x in ids if x not in _ids]
        print(_ids)
        return _ids, stacked