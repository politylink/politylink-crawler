from datetime import datetime
from logging import getLogger

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import extract_full_href_or_none, build_news, to_neo4j_datetime, extract_json_ld_or_none, strip_join
from politylink.elasticsearch.schema import NewsText

LOGGER = getLogger(__name__)


class MainichiSpider(SpiderTemplate):
    name = 'mainichi'
    publisher = '毎日新聞'
    limit = 50

    def __init__(self, *args, **kwargs):
        super(MainichiSpider, self).__init__(*args, **kwargs)
        self.next_page = 1

    def build_next_url(self):
        return f'https://mainichi.jp/seiji/{self.next_page}'

    def start_requests(self):
        yield scrapy.Request(self.build_next_url(), self.parse)

    def parse(self, response):
        news_list = response.xpath('//section[@class="newslist"]').css('ul.list-typeA')
        url_list = []
        for li in news_list.xpath('li'):
            maybe_url = extract_full_href_or_none(li, response.url)
            if maybe_url:
                url_list.append(maybe_url)
        LOGGER.info(f'scraped {len(url_list)} News urls from {response.url}')
        for url in url_list:
            if 'premier' not in url:  # ToDo: process premier article
                yield response.follow(url, callback=self.parse_news)
        self.next_page += 1
        if self.next_page <= self.limit:
            yield response.follow(self.build_next_url(), self.parse)

    def parse_news(self, response):
        try:
            maybe_json_ld = extract_json_ld_or_none(response)
            article = response.xpath('//div[@class="article"]')
            title = article.xpath('.//h1/text()').get().strip()
            body = strip_join(article.xpath('.//p[@class="txt"]/text()').getall())

            news = build_news(response.url, self.publisher)
            news.title = title
            news.is_paid = 'この記事は有料記事です' in response.body.decode('UTF-8')
            if maybe_json_ld:
                json_ld = maybe_json_ld
                if 'image' in json_ld and 'url' in json_ld['image']:
                    news.thumbnail = json_ld['image']['url']
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
        return to_neo4j_datetime(datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S%z'))
