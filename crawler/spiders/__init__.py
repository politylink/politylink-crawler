from logging import getLogger
from urllib.parse import urljoin

import scrapy

from crawler.utils import extract_text, build_url, UrlTitle
from politylink.graphql.client import GraphQLClient
from politylink.helpers import BillFinder

LOGGER = getLogger(__name__)


class SpiderTemplate(scrapy.Spider):
    domain = NotImplemented

    def __init__(self, *args, **kwargs):
        super(SpiderTemplate, self).__init__(*args, **kwargs)
        self.client = GraphQLClient()
        self.bill_finder = BillFinder()

    def parse(self, response):
        NotImplemented

    def store_urls(self, urls, bill_text):
        bills = self.bill_finder.find(bill_text)
        if len(bills) == 0:
            LOGGER.warning(f'failed to find Bill for {bill_text}')
        elif len(bills) == 1:
            bill = bills[0]
            for url in urls:
                self.client.exec_merge_url(url)
                self.client.exec_merge_url_referred_bills(url.id, bill.id)
        else:
            LOGGER.warning(f'found multiple Bills for {bill_text}')


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
                    bill_text = extract_text(cells[self.bill_col]).strip()
                    urls = self.extract_urls(cells[self.url_col])
                    self.store_urls(urls, bill_text)
                    LOGGER.info(f'scraped {len(urls)} urls for {bill_text}')
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
            bill_text = item['bill_text']
            urls = [build_url(item['href'], item['title'], self.domain)]
            self.store_urls(urls, bill_text)
