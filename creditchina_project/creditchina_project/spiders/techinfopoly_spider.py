# -*- coding: utf-8 -*-
import base64
import datetime
import logging
import re
import sys
import urllib
import requests
import scrapy
from inline_requests import inline_requests
from scrapy import Selector, Request

from creditchina_project.techinfopoly_items import TechInfoPolyLoaderItem, TechInfoPolyResultItem
from creditchina_project.utils.dbutils import execute

reload(sys)
sys.setdefaultencoding('utf-8')
class TechInfoPoly(scrapy.Spider):
    name = "techinfopoly"
    custom_settings = {
        'ITEM_PIPELINES': {
            'creditchina_project.pipelines.CreditchinaProjectDB2Pipeline': 100,
        }
    }
    #execute('TRUNCATE TABLE SPIDER.NEWS IMMEDIATE') # by qxs
    batch = datetime.datetime.now()
    allowed_domains = ['tech.sina.com.cn','36kr.com','iresearch.cn']
    default_data = {
    }
    default_headers = {
    }
    def start_requests(self):
        sites=['https://cre.mix.sina.com.cn/api/v3/get?callback=jQuery111207568558421793976_1538664874380&cateid=1z&cre=tianyi&mod=pctech&merge=3&statics=1&length=15&up=0&down=0&tm=1538664875&action=0&top_id=8oWdy%2C8oatR%2C8oBFT%2C8oY3T%2C8oYv6%2C8oYsw%2C%2C%2C8TdmN&offset=0&ad=%7B%22rotate_count%22%3A100%2C%22platform%22%3A%22pc%22%2C%22channel%22%3A%22tianyi_pctech%22%2C%22page_url%22%3A%22https%3A%2F%2Ftech.sina.com.cn%2F%22%2C%22timestamp%22%3A1538664875110%7D&_=1538664874381',
                'http://feed.mix.sina.com.cn/api/roll/get?pageid=372&lid=2431&k=&num=50&page=1&r=0.048739369442073244&callback=jQuery311013339969585292177_1538789898529&_=1538789898530',
               'http://center.iresearch.cn/ajax/process.ashx?work=login&uAccount=1514767024%40qq.com&uPassword=happy2018&days=15&t=0.5486955056946374',
               ]
        for site in sites:
            yield scrapy.Request(url=site, callback=self.parse_basic_info, dont_filter=True)

    def parse_basic_info(self, response):
        basic_info = response.text
        if response.url.startswith('https://cre.mix.sina.com.cn/api/v3/get'):
            news_list = eval(basic_info.replace('null', 'None').replace('false', 'None').replace('\n', '').replace('\r', '')[42:-2])['data']
            for news in news_list:
                url = news['url'].replace('\\', '')
                title = news['title']
                cover = base64.b64encode(requests.get(news['thumb'].replace('\\', '')).content)
                hot = '0'
                type = '金融科技'
                yield scrapy.Request(url=url, headers=self.default_headers, body=urllib.urlencode(self.default_data),
                                     meta={'title': title,'cover': cover,'hot': hot,'type': type}, callback=self.parse_detail_info, dont_filter=True)
        else:
            if response.url.startswith('http://feed.mix.sina.com.cn/api/roll/get'):
                news_list = eval(basic_info.replace('null', 'None').replace('false', 'None').replace('\n', '').replace('\r','')[46:-14])['result']['data']
                for news in news_list:
                    url = news['url'].replace('\\','')
                    title = news['title'].decode('unicode-escape')
                    cover = ''
                    hot = '1'
                    type = '快讯'
                    yield scrapy.Request(url=url, headers=self.default_headers,
                                         body=urllib.urlencode(self.default_data),
                                         meta={'title': title, 'cover': cover, 'hot': hot, 'type': type},
                                         callback=self.parse_detail_info, dont_filter=True)
            else:
                if response.url.startswith('http://center.iresearch.cn'):
                    yield scrapy.Request(url='http://report.iresearch.cn/common/page/rsprocess.ashx?work=csearch&vid=0&sid=2&yid='+str(datetime.datetime.now().year), headers=self.default_headers,
                                    callback=self.login_iresearch, dont_filter=True)

    @inline_requests
    def parse_detail_info(self, response):
        detail_info = response.text
        if ('http://tech.sina.com.cn' in response.url) or ('https://tech.sina.com.cn' in response.url):
            url = response.url.strip()
            title = response.meta['title']
            content = ''.join(Selector(text=detail_info).xpath('//div[@id="artibody"]/p').extract())
            pattern = re.compile('</?a[^>]*>')
            content = pattern.sub('', content)
            pattern = re.compile('</?img[^>]*>')
            content = pattern.sub('', content)
            cover = response.meta['cover']
            pdf = ''
            keywords = ''
            if len(Selector(text=detail_info).xpath('//div[@id="keywords"]/a/text()').extract())>0:
                keywords = ','.join(Selector(text=detail_info).xpath('//div[@id="keywords"]/a/text()').extract())
            else:
                keywords = ','.join(Selector(text=detail_info).xpath('//p[@class="art_keywords"]/a/text()').extract())
            hot = response.meta['hot']
            type = response.meta['type']
            if type != '快讯':
                type = self.get_type(content)
            update = ''
            if len(Selector(text=detail_info).xpath('//span[@class="date"]/text()').extract())>0:
                update = Selector(text=detail_info).xpath('//span[@class="date"]/text()').extract()[0].strip()
            else:
                update = Selector(text=detail_info).xpath('//span[@id="pub_date"]/text()').extract()[0].strip()
            batch = self.batch
            table_name = 'spider.news'
            yield self.save_result(batch, url, title, content, cover, pdf, keywords, hot, type, update, table_name, response).load_item()
        else:
            if ('http://report.iresearch.cn' in response.url):
                url = response.url
                title = response.meta['title']
                content = response.meta['content']
                pattern = re.compile('</?a[^>]*>')
                content = pattern.sub('', content)
                pattern = re.compile('</?img[^>]*>')
                content = pattern.sub('', content)
                cover = response.meta['cover']
                pdf = ''
                pdf_price = Selector(text=detail_info).xpath('//li[@class="price"]/text()').extract()[0]
                pdf_url = 'http://report.iresearch.cn/include/ajax/user_ajax.ashx?reportid=' + str(url[url.rfind('/') + 1:-6]) + '&work=rdown&url=' + url
                if '￥0' == pdf_price:
                    pdf_content = yield Request(pdf_url)
                    # self.save_pdf(pdf_content)
                    pdf = base64.b64encode(pdf_content.body)
                keywords = response.meta['keywords']
                hot = response.meta['hot']
                type = response.meta['type']
                update = response.meta['update']
                batch = self.batch
                table_name = 'spider.news'
                yield self.save_result(batch, url, title, content, cover, pdf, keywords, hot, type, update, table_name, response).load_item()

    def save_pdf(self, response):
        path = response.url.split('/')[-1][0:-5] + 'pdf'
        self.logger.info('Saving PDF %s', path)
        with open(path, 'wb') as f:
            f.write(response.body)

    def login_iresearch(self, response):
        basic_info = response.text
        items = Selector(text=basic_info).xpath('//li').extract()
        for item in items:
            url = Selector(text=item).xpath('//div[@class="u-img"]/a/@href').extract()[0]
            title = Selector(text=item).xpath('//div[@class="txt"]/h3/a/text()').extract()[0]
            content = Selector(text=item).xpath('//div[@class="txt"]/p/text()').extract()[0]
            cover = base64.b64encode(
                requests.get(Selector(text=item).xpath('//div[@class="u-img"]/a/img/@src').extract()[0]).content, )
            keywords = '行业报告'
            if len(Selector(text=item).xpath(
                    '//div[@class="txt"]/div[@class="foot f-cb"]/div[@class="link f-fl"]/a/text()').extract()) > 0:
                keywords = ','.join(Selector(text=item).xpath(
                    '//div[@class="txt"]/div[@class="foot f-cb"]/div[@class="link f-fl"]/a/text()').extract())
            hot = '2'
            type = '行业报告'
            update = Selector(text=item).xpath(
                '//div[@class="txt"]/div[@class="foot f-cb"]/div[@class="time f-fr"]/span/text()').extract()[0]
            yield scrapy.Request(url=url, headers=self.default_headers,
                                 meta={'title': title, 'content': content, 'cover': cover, 'keywords': keywords,
                                       'hot': hot, 'type': type, 'update': update},
                                 callback=self.parse_detail_info, dont_filter=True)

    def save_result(self, batch, url, title, content, cover, pdf, keywords, hot, type, update, table_name, response):
        item = TechInfoPolyLoaderItem(item=TechInfoPolyResultItem(), response=response)
        item.add_value('batch', batch)
        item.add_value('url', url)
        item.add_value('title', title)
        item.add_value('content', content)
        item.add_value('cover', cover)
        item.add_value('pdf', pdf)
        item.add_value('keywords', keywords)
        item.add_value('hot', hot)
        item.add_value('type', type)
        item.add_value('update', update)
        item.add_value('table_name', table_name)
        return item

    def get_type(self, content):
        if '金融' in content or '银行' in content or '证券' in content:
            return '金融科技'
        if '区块连' in content:
            return '区块连'
        if '消费' in content or '汽车' in content or '电子' in content:
            return '消费'
        if '新零售' in content or 'O2O' in content:
            return '新零售'
        if '大数据' in content:
            return '大数据'
        return '金融科技'

    def closed(self, reason):
        '''
        爬虫结束时退出登录状态
        :param reason:
        :return:
        '''
        if 'finished' == reason:
            logging.warning('%s', '爬虫程序执行结束，即将关闭')
        elif 'shutdown' == reason:
            logging.warning('%s', '爬虫进程被强制中断，即将关闭')
        elif 'cancelled' == reason:
            logging.warning('%s', '爬虫被引擎中断，即将关闭')
        else:
            logging.warning('%s', '爬虫被未知原因打断，即将关闭')