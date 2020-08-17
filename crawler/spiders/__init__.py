from logging import getLogger
from urllib.parse import urljoin

import scrapy

from crawler.utils import extract_text, build_url
from politylink.graphql.client import GraphQLClient
from politylink.helpers import BillFinder

LOGGER = getLogger(__name__)


class SpiderTemplate(scrapy.Spider):
    def __init__(self, *args, **kwargs):
        super(SpiderTemplate, self).__init__(*args, **kwargs)
        self.client = GraphQLClient()
        self.bill_finder = BillFinder()

    def parse(self, response):
        NotImplemented

    def store_urls(self, urls, bill_title):
        bills = self.bill_finder.find(bill_title)
        for url in urls:
            self.client.exec_merge_url(url)
            for bill in bills:
                self.client.exec_merge_url_referred_bills(url.id, bill.id)


class TableSpiderTemplate(SpiderTemplate):
    domain = NotImplemented
    table_idx = NotImplemented
    bill_col = NotImplemented
    url_col = NotImplemented

    def parse(self, response):
        table = response.xpath('//table')[self.table_idx]
        for row in table.xpath('.//tr'):
            cells = row.xpath('.//td')
            if len(cells) > max(self.bill_col, self.url_col):
                try:
                    bill_title = extract_text(cells[self.bill_col])
                    urls = self.extract_urls(cells[self.url_col])
                    self.store_urls(urls, bill_title)
                    LOGGER.info(f'scraped {len(urls)} urls for {bill_title}')
                except Exception as e:
                    LOGGER.warning(f'failed to parse {row}: {e}')
                    continue

    def extract_urls(self, cell):
        urls = []
        for a in cell.xpath('.//a'):
            text = extract_text(a)
            href = urljoin(self.start_urls[0], a.xpath('./@href').get())
            if '概要' in text:
                urls.append(build_url(href, '概要PDF', self.domain))
            elif '新旧' in text:
                urls.append(build_url(href, '新旧対照表PDF', self.domain))
        return urls
