from datetime import datetime
from logging import getLogger

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import extract_json_ld_or_none, build_news, extract_thumbnail_or_none, \
    strip_join, to_neo4j_datetime, extract_full_href_list
from politylink.elasticsearch.schema import NewsText

LOGGER = getLogger(__name__)


class ReutersSpider(SpiderTemplate):
    name = 'reuters'
    publisher = 'ロイター'

    def __init__(self, limit, *args, **kwargs):
        super(ReutersSpider, self).__init__(*args, **kwargs)
        self.limit = int(limit)
        self.next_page = 1

    def build_next_url(self):
        return f'https://jp.reuters.com/news/archive/politicsNews?view=page&page={self.next_page}&pageSize=10'

    def start_requests(self):
        yield scrapy.Request(self.build_next_url(), self.parse)

    def parse(self, response):
        news_url_list = extract_full_href_list(
            response.xpath('//section[@id="moreSectionNews"]//article'), response.url)
        LOGGER.info(f'scraped {len(news_url_list)} news urls from {response.url}')
        for news_url in news_url_list:
            yield response.follow(news_url, callback=self.parse_news)
        self.next_page += 1
        if self.next_page <= self.limit:
            yield response.follow(self.build_next_url(), self.parse)

    def parse_news(self, response):
        try:
            maybe_json_ld = extract_json_ld_or_none(response)
            title = response.xpath('//h1/text()').get().strip()
            body = strip_join(response.xpath('//div[@class="ArticleBodyWrapper"]/p/text()').getall())

            news = build_news(response.url, self.publisher)
            news.title = title
            news.is_paid = False
            if maybe_json_ld:
                json_ld = maybe_json_ld
                maybe_thumbnail = extract_thumbnail_or_none(json_ld)
                if maybe_thumbnail:
                    news.thumbnail = maybe_thumbnail
                news.published_at = self.to_datetime(json_ld['datePublished'])
                news.last_modified_at = self.to_datetime(json_ld['dateModified'])
            self.client.exec_merge_news(news)

            news_text = NewsText({'id': news.id})
            news_text.title = title
            news_text.body = body
            self.es_client.index(news_text)
        except Exception:
            LOGGER.exception(f'failed to parse News from {response.url}')

    @staticmethod
    def to_datetime(dt_str):
        return to_neo4j_datetime(datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%SZ'))
