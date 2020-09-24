from datetime import datetime
from logging import getLogger
from urllib.parse import urljoin

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import build_news, to_neo4j_datetime, extract_json_ld_or_none, strip_join
from politylink.elasticsearch.schema import NewsText

LOGGER = getLogger(__name__)


class NikkeiSpider(SpiderTemplate):
    name = 'nikkei'
    domain = 'nikkei.com'
    limit = 100

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
        if self.next_bn <= self.limit:
            yield response.follow(self.build_next_url(), self.parse)

    def parse_news(self, response):
        try:
            maybe_json_ld = extract_json_ld_or_none(response)
            title = strip_join(response.css('h1.cmn-article_title').xpath('.//span/text()').getall(), sep=' ')
            body = strip_join(response.css('div.cmn-article_text').xpath('.//p/text()').getall())

            news = build_news(response.url, self.domain)
            news.title = title
            news.is_paid = 'この記事は会員限定です' in response.body.decode('UTF-8')
            if maybe_json_ld:
                news.published_at = self.to_datetime(maybe_json_ld['datePublished'])
                news.last_modified_at = self.to_datetime(maybe_json_ld['dateModified'])
            self.client.exec_merge_news(news)

            news_text = NewsText({'id': news.id})
            news_text.title = title
            news_text.body = body
            self.es_client.index(news_text)
        except Exception:
            LOGGER.exception(f'failed to parse News from {response.url}')

    @staticmethod
    def to_datetime(dt_str):
        return to_neo4j_datetime(datetime.strptime(dt_str, '%Y%m%dT%H%M%S%z'))
