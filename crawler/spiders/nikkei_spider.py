from datetime import datetime
from logging import getLogger

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import build_news, to_neo4j_datetime, extract_json_ld_or_none, strip_join, extract_thumbnail_or_none, \
    extract_full_href_list
from politylink.elasticsearch.schema import NewsText

LOGGER = getLogger(__name__)


class NikkeiSpider(SpiderTemplate):
    name = 'nikkei'
    publisher = '日経新聞'

    def __init__(self, limit, *args, **kwargs):
        super(NikkeiSpider, self).__init__(*args, **kwargs)
        self.limit = int(limit)
        self.next_bn = 1

    def build_next_url(self):
        return f'https://www.nikkei.com/politics/politics/?bn={self.next_bn}'

    def start_requests(self):
        yield scrapy.Request(self.build_next_url(), self.parse)

    def parse(self, response):
        news_url_list = extract_full_href_list(response.css('div.m-miM09'), response.url)
        LOGGER.info(f'scraped {len(news_url_list)} news urls from {response.url}')
        for news_url in news_url_list:
            yield response.follow(news_url, callback=self.parse_news)
        self.next_bn += 20
        if self.next_bn <= self.limit:
            yield response.follow(self.build_next_url(), self.parse)

    def parse_news(self, response):
        try:
            maybe_json_ld = extract_json_ld_or_none(response)
            title = strip_join(response.css('h1.cmn-article_title').xpath('.//span/text()').getall(), sep=' ')
            body = strip_join(response.css('div.cmn-article_text').xpath('.//p/text()').getall())

            news = build_news(response.url, self.publisher)
            news.title = title
            news.is_paid = 'この記事は会員限定です' in response.body.decode('UTF-8')
            if maybe_json_ld:
                json_ld = maybe_json_ld
                maybe_thumbnail = extract_thumbnail_or_none(json_ld)
                if maybe_thumbnail:
                    news.thumbnail = maybe_thumbnail
                news.published_at = self.to_datetime(json_ld['datePublished'])
                news.last_modified_at = self.to_datetime(json_ld['dateModified'])
            self.gql_client.merge(news)

            news_text = NewsText({'id': news.id})
            news_text.title = title
            news_text.body = body
            self.es_client.index(news_text)
        except Exception:
            LOGGER.exception(f'failed to parse News from {response.url}')

    @staticmethod
    def to_datetime(dt_str):
        return to_neo4j_datetime(datetime.strptime(dt_str, '%Y%m%dT%H%M%S%z'))
