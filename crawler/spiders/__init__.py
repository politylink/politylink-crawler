import logging
from urllib.parse import urljoin

import scrapy

from crawler.utils import extract_text, build_url, UrlTitle
from politylink.elasticsearch.client import ElasticsearchClient
from politylink.graphql.client import GraphQLClient
from politylink.graphql.schema import Minutes
from politylink.helpers import BillFinder, MinutesFinder, CommitteeFinder

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

    def delete_old_urls(self, bill_id, url_title):
        bill = self.gql_client.get(bill_id)
        for url in bill.urls:
            if url.title == url_title:
                self.gql_client.delete(url.id)
                LOGGER.info(f'deleted {url.id}')

    def link_bills_by_topics(self, minutes: Minutes):
        if not hasattr(minutes, 'topics'):
            return

        from_ids, to_ids = [], []
        for topic in minutes.topics:
            bills = self.bill_finder.find(topic)
            if len(bills) == 1:
                bill = bills[0]
                from_ids.append(minutes.id)
                to_ids.append(bill.id)
                LOGGER.debug(f'linked {minutes.id} to {bill.id}')
            elif len(bills) > 1:
                LOGGER.warning(f'found multiple bills that match with "{topic}" in {minutes.id}: {bills}')
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
    def __init__(self, next_id, failure_in_row_limit, *args, **kwargs):
        super(TvSpiderTemplate, self).__init__(*args, **kwargs)
        self.next_id = next_id
        self.failure_in_row_limit = failure_in_row_limit
        self.failure_in_row = 0

    def build_next_url(self) -> str:
        NotImplemented

    def start_requests(self):
        yield scrapy.Request(self.build_next_url(), self.parse)

    def parse(self, response):
        """
        MinutesとURLをGraphQLに保存する
        """

        minutes = self.scrape_minutes(response)
        if minutes:
            url = build_url(response.url, UrlTitle.SHINGI_TYUKEI, self.domain)
            self.gql_client.bulk_merge([minutes, url])
            self.gql_client.link(url.id, minutes.id)
            LOGGER.info(f'merged {minutes.id} and {url.id}')
            try:
                committee = self.committee_finder.find_one(minutes.name)
                self.gql_client.link(minutes.id, committee.id)
            except ValueError as e:
                LOGGER.warning(e)
            self.link_bills_by_topics(minutes)
            self.failure_in_row = 0
        else:
            LOGGER.info(f'failed to parse minutes from {response.url}. skipping...')
            self.failure_in_row += 1

        if self.failure_in_row < self.failure_in_row_limit:
            yield response.follow(self.build_next_url(), callback=self.parse)

    def scrape_minutes(self, response) -> Minutes:
        NotImplemented
