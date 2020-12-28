import logging
from urllib.parse import urljoin

import scrapy

from crawler.utils import extract_text, build_url, UrlTitle, validate_news_or_raise, validate_news_text_or_raise
from politylink.elasticsearch.client import ElasticsearchClient
from politylink.elasticsearch.schema import NewsText
from politylink.graphql.client import GraphQLClient
from politylink.graphql.schema import Minutes, News
from politylink.helpers import BillFinder, MinutesFinder, CommitteeFinder, MemberFinder

LOGGER = logging.getLogger(__name__)


class SpiderTemplate(scrapy.Spider):
    domain = NotImplemented

    def __init__(self, *args, **kwargs):
        super(SpiderTemplate, self).__init__(*args, **kwargs)
        logging.getLogger('elasticsearch').setLevel(logging.WARNING)
        self.gql_client = GraphQLClient()
        self.es_client = ElasticsearchClient()
        self.bill_finder = BillFinder()
        self.minutes_finder = MinutesFinder()
        self.committee_finder = CommitteeFinder()
        self.member_finder = MemberFinder()

    def parse(self, response):
        NotImplemented

    def store_urls(self, urls, bill_query):
        bills = self.bill_finder.find(bill_query)
        if len(bills) == 0:
            LOGGER.warning(f'failed to find Bill for {bill_query}')
        elif len(bills) == 1:
            bill = bills[0]
            if urls:
                self.gql_client.bulk_merge(urls)
                self.gql_client.bulk_link(map(lambda x: x.id, urls), [bill.id] * len(urls))
        else:
            LOGGER.warning(f'found multiple Bills for {bill_query}')

    def delete_old_urls(self, src_id, url_title):
        obj = self.gql_client.get(src_id)
        for url in obj.urls:
            if url.title == url_title:
                self.gql_client.delete(url.id)
                LOGGER.info(f'deleted {url.id}')

    def link_bills_by_topics(self, minutes: Minutes):
        if not hasattr(minutes, 'topics'):
            return

        from_ids, to_ids = [], []
        for topic in minutes.topics:
            try:
                bill = self.bill_finder.find_one(topic)
            except ValueError as e:
                LOGGER.warning(e)
            else:
                from_ids.append(minutes.id)
                to_ids.append(bill.id)
                LOGGER.debug(f'link {minutes.id} to {bill.id}')
        self.gql_client.bulk_link(from_ids, to_ids)
        LOGGER.info(f'linked {len(from_ids)} bills to {minutes.id}')


class TableSpiderTemplate(SpiderTemplate):
    table_idx = NotImplemented
    bill_col = NotImplemented
    url_col = NotImplemented

    def parse(self, response):
        self.parse_table(response)

    def parse_table(self, response):
        table = response.xpath('//table')[self.table_idx]
        for row in table.xpath('.//tr'):
            cells = row.xpath('.//td')
            if len(cells) > max(self.bill_col, self.url_col):
                try:
                    bill_query = extract_text(cells[self.bill_col]).strip()
                    urls = self.extract_urls(cells[self.url_col])
                    self.store_urls(urls, bill_query)
                    LOGGER.info(f'scraped {len(urls)} urls for {bill_query}')
                except Exception as e:
                    LOGGER.warning(f'failed to parse {row}: {e}')
                    continue

    def extract_urls(self, cell):
        urls = []
        for a in cell.xpath('.//a'):
            text = extract_text(a)
            href = urljoin(self.start_urls[0], a.xpath('./@href').get())
            if '概要' in text:
                urls.append(build_url(href, UrlTitle.GAIYOU_PDF, self.domain))
            elif '新旧' in text:
                urls.append(build_url(href, UrlTitle.SINKYU_PDF, self.domain))
        return urls


class ManualSpiderTemplate(SpiderTemplate):
    items = []

    def parse(self, response):
        self.parse_items()

    def parse_items(self):
        for item in self.items:
            bill_query = item['bill']
            urls = [build_url(item['url'], item['title'], self.domain)]
            self.store_urls(urls, bill_query)
        LOGGER.info(f'merged {len(self.items)} urls')


class TvSpiderTemplate(SpiderTemplate):

    def store_minutes_and_url(self, minutes, url):
        """
        store minutes and url to GraphQL with links to Committee and Member
        """

        self.gql_client.bulk_merge([minutes, url])
        LOGGER.info(f'merged {minutes.id} and {url.id}')

        self.gql_client.link(url.id, minutes.id)
        self.link_bills_by_topics(minutes)

        try:
            committee = self.committee_finder.find_one(minutes.name)
            self.gql_client.link(minutes.id, committee.id)
        except ValueError as e:
            LOGGER.warning(e)

        if hasattr(minutes, 'speakers'):
            from_ids = []
            to_ids = []
            for speaker in minutes.speakers:
                try:
                    member = self.member_finder.find_one(speaker)
                except ValueError as e:
                    LOGGER.debug(e)  # this is expected when speaker is not member
                else:
                    from_ids.append(member.id)
                    to_ids.append(minutes.id)
            self.gql_client.bulk_link(from_ids, to_ids)
            LOGGER.info(f'linked {len(from_ids)} members')


class NewsSpiderTemplate(SpiderTemplate):
    def parse_news(self, response):
        """
        NewsとNewsTextをGraphQLとElasticSearchにそれぞれ保存する
        """

        try:
            news, news_text = self.scrape_news_and_text(response)
            validate_news_or_raise(news)
            validate_news_text_or_raise(news_text)
            self.gql_client.merge(news)
            self.es_client.index(news_text)
            LOGGER.info(f'saved {news.id}')
        except Exception:
            LOGGER.exception(f'failed to save News from {response.url}')

    def scrape_news_and_text(self, response) -> (News, NewsText):
        NotImplemented
