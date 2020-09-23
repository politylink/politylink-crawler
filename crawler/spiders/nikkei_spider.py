import re
from datetime import datetime
from logging import getLogger
from urllib.parse import urljoin

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import build_news, to_neo4j_datetime
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
        if self.next_bn < self.limit:
            yield response.follow(self.build_next_url(), self.parse)

    def parse_news(self, response):
        datetime_str = response.css('dd.cmnc-publish::text').get()
        maybe_published_at, maybe_last_modified_at = self.extract_datetime_pair(datetime_str)
        is_paid = 'この記事は会員限定です' in response.body.decode('UTF-8')
        title = ' '.join(response.css('h1.cmn-article_title').xpath('.//span/text()').getall())
        body = ''.join(response.css('div.cmn-article_text').xpath('.//p/text()').getall())

        news = build_news(response.url, self.domain)
        news.title = title
        news.is_paid = is_paid
        if maybe_published_at:
            news.published_at = to_neo4j_datetime(maybe_published_at)
        if maybe_last_modified_at:
            news.last_modified_at = to_neo4j_datetime(maybe_last_modified_at)
        self.client.exec_merge_news(news)

        news_text = NewsText({'id': news.id})
        news_text.title = title
        news_text.body = body
        self.es_client.index(news_text)

    @staticmethod
    def extract_datetime_pair(text):
        def to_datetime(maybe_dt_str):
            return datetime.strptime(maybe_dt_str.strip(), '%Y/%m/%d %H:%M') if maybe_dt_str else None

        if not text:
            return None, None
        text = text.strip()
        pattern = r'([0-9/: ]*)(\(([0-9/: ]*)更新\))?'
        match = re.fullmatch(pattern, text)
        if not match:
            LOGGER.warning(f'failed to extract datetime from {text}')
            return None, None
        return to_datetime(match.group(1)), to_datetime(match.group(3))
