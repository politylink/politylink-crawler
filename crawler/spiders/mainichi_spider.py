from datetime import datetime
from logging import getLogger

from crawler.spiders import NewsSpiderTemplate
from crawler.utils import build_news, to_neo4j_datetime, extract_json_ld_or_none, strip_join, \
    extract_thumbnail_or_none, extract_full_href_list
from politylink.elasticsearch.schema import NewsText

LOGGER = getLogger(__name__)


class MainichiSpider(NewsSpiderTemplate):
    name = 'mainichi'
    publisher = '毎日新聞'
    start_urls = ['https://mainichi.jp/seiji/']

    def __init__(self, *args, **kwargs):
        super(MainichiSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        news_url_list = extract_full_href_list(response.xpath('//section[@id="article-list"]//li'), response.url)
        LOGGER.info(f'scraped {len(news_url_list)} news urls from {response.url}')
        for news_url in news_url_list:
            if 'premier' not in news_url:  # ToDo: process premier article
                yield response.follow(news_url, callback=self.parse_news)

    def scrape_news_and_text(self, response):
        maybe_json_ld = extract_json_ld_or_none(response)
        title = response.xpath('//h1[@class="title-page"]/text()').get().strip()
        article = response.css('section#articledetail-body')
        body = strip_join(article.xpath('.//p/text()').getall())

        news = build_news(response.url, self.publisher)
        news.title = title
        news.is_paid = 'この記事は有料記事です' in response.body.decode('UTF-8')
        if maybe_json_ld:
            json_ld = maybe_json_ld
            maybe_thumbnail = extract_thumbnail_or_none(json_ld)
            if maybe_thumbnail:
                news.thumbnail = maybe_thumbnail
            news.published_at = self.to_datetime(json_ld['datePublished'])
            news.last_modified_at = self.to_datetime(json_ld['dateModified'])

        news_text = NewsText({'id': news.id})
        news_text.title = title
        news_text.body = body

        return news, news_text

    @staticmethod
    def to_datetime(dt_str):
        return to_neo4j_datetime(datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S%z'))
