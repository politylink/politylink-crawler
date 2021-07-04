from datetime import datetime, timedelta
from logging import getLogger

import scrapy

from crawler.spiders import NewsSpiderTemplate
from crawler.utils import build_news, to_neo4j_datetime, extract_full_href_list
from politylink.elasticsearch.schema import NewsText
from politylink.utils import strip_join, to_date_str

LOGGER = getLogger(__name__)


class NikkeiSpider(NewsSpiderTemplate):
    name = 'nikkei'
    publisher = '日経新聞'

    def __init__(self, limit, *args, **kwargs):
        super(NikkeiSpider, self).__init__(*args, **kwargs)
        self.limit = int(limit)
        self.news_count = 0
        self.next_bn = -19

    def build_next_url(self):
        self.next_bn += 20
        return f'https://www.nikkei.com/politics/politics/?bn={self.next_bn}'

    def start_requests(self):
        yield scrapy.Request(self.build_next_url(), self.parse)

    def parse(self, response):
        news_url_list = extract_full_href_list(response.css('div.m-miM09'), response.url)
        LOGGER.info(f'scraped {len(news_url_list)} news urls from {response.url}')
        for news_url in news_url_list:
            yield response.follow(news_url, callback=self.parse_news)
        self.news_count += len(news_url_list)
        if self.news_count < self.limit:
            yield response.follow(self.build_next_url(), self.parse)

    def scrape_news_and_text(self, response):
        title = strip_join(response.css('h1.title_tyodebu').xpath('.//text()').getall(), sep=' ')
        body = strip_join(response.css('section.container_cz8tiun').xpath('.//p/text()').getall())

        news = build_news(response.url, self.publisher)
        news.title = title
        news.is_paid = 'この記事は会員限定です' in response.body.decode('UTF-8')

        news_text = NewsText({'id': news.id})
        news_text.title = title
        news_text.body = body

        maybe_published_at_str = response.css('div.TimeStamp_t165nkxq').xpath('.//time/@datetime').get()
        if maybe_published_at_str:
            news.published_at = self.to_datetime2(maybe_published_at_str)
            news_text.date = to_date_str(news.published_at)

        return news, news_text

    @staticmethod
    def to_datetime(dt_str):
        return to_neo4j_datetime(datetime.strptime(dt_str, '%Y%m%dT%H%M%S%z'))

    @staticmethod
    def to_datetime2(dt_str):
        dt_str = dt_str.split('.')[0]  # drop timezone
        return to_neo4j_datetime(datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S') + timedelta(hours=9))
