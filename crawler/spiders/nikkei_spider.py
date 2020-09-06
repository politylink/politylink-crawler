from urllib.parse import urljoin

import scrapy


class NikkeiSpider(scrapy.Spider):
    name = 'nikkei'
    limit = 4000

    def __init__(self, *args, **kwargs):
        super(NikkeiSpider, self).__init__(*args, **kwargs)
        self.next_bn = 1

    def build_next_url(self):
        return f'https://www.nikkei.com/politics/politics/?bn={self.next_bn}'

    def start_requests(self):
        yield scrapy.Request(self.build_next_url(), self.parse)

    def parse(self, response):
        divs = response.css('div.m-miM09')
        for div in divs:
            url = urljoin(response.url, div.xpath('.//a/@href').get())
            yield response.follow(url, callback=self.parse_news)
        self.next_bn += 20
        if self.next_bn < self.limit:
            yield response.follow(self.build_next_url(), self.parse)

    def parse_news(self, response):
        yield {
            'url': response.url,
            'time': response.css('dd.cmnc-publish::text').get(),
            'tag': response.css('dl.cmn-article_topics').xpath('.//a/text()').getall(),
            'paid': 'この記事は会員限定です' in response.body.decode('UTF-8'),
            'title': response.css('h1.cmn-article_title').xpath('.//span/text()').getall(),
            'text': response.css('div.cmn-article_text').xpath('.//p/text()').getall()
        }
