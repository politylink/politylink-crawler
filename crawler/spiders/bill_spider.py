from logging import getLogger
from urllib.parse import urljoin

import scrapy
from politylink.graphql.client import GraphQLClient
from politylink.graphql.schema import BillCategory, Bill, Url

LOGGER = getLogger(__name__)


class BillSpider(scrapy.Spider):
    name = "bill"
    start_urls = ['http://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/menu.htm']

    progress_url_field = '_progress_url'
    text_url_field = '_text_url'
    all_url_fields = [progress_url_field, text_url_field]

    def __init__(self, *args, **kwargs):
        super(BillSpider, self).__init__(*args, **kwargs)
        self.client = GraphQLClient()

    def parse(self, response):
        bills = self.scrape_bills(response)
        LOGGER.info(f'scraped {len(bills)} bills')

        for bill in bills:
            self.client.exec_merge_bill(bill)
            LOGGER.debug(f'added {bill.id}')
            for url_field in self.all_url_fields:
                if hasattr(bill, url_field):
                    url = getattr(bill, url_field)
                    self.merge_url_for_bill(url, bill)
                    LOGGER.debug(f'added {url_field} for {bill.id}')

        LOGGER.info(f'saved {len(bills)} bills successfully')

    def merge_url_for_bill(self, url, bill):
        self.client.exec_merge_url(url)
        self.client.exec_merge_url_referred_bills(url.id, bill.id)

    @staticmethod
    def scrape_bills(response):
        tables = response.xpath('//table')
        bills = BillSpider.parse_bill_table(tables[0], BillCategory.SYUHOU, response.url) + \
                BillSpider.parse_bill_table(tables[1], BillCategory.SANHOU, response.url) + \
                BillSpider.parse_bill_table(tables[1], BillCategory.KAKUHOU, response.url)
        return bills

    @staticmethod
    def parse_bill_table(table, bill_category, response_url):
        def extract_text(cell):
            return cell.xpath('.//text()').get()

        def extract_full_href_or_none(cell):
            selector = cell.xpath('.//a/@href')
            if len(selector) == 1:
                return urljoin(response_url, selector[0].get())
            return None

        bills = []
        for row in table.xpath('./tr')[1:]:  # skip header
            cells = row.xpath('./td')
            assert len(cells) == 6

            # build bill instance with necessary info
            try:
                diet_number = int(extract_text(cells[0]))
                bill_number = int(extract_text(cells[1]))
                bill_title = extract_text(cells[2])
            except Exception as e:
                LOGGER.warning(f'failed to parse row:\n{row.get()}\n{e}')
                continue
            bill = BillSpider.build_bill(diet_number, bill_category, bill_number, bill_title)

            # add URLs if exist
            maybe_progress_href = extract_full_href_or_none(cells[4])
            maybe_text_href = extract_full_href_or_none(cells[5])
            if maybe_progress_href:
                progress_url = BillSpider.build_url(maybe_progress_href, '経過')
                bill.__setattr__(BillSpider.progress_url_field, progress_url)
            if maybe_text_href:
                text_url = BillSpider.build_url(maybe_text_href, '本文')
                bill.__setattr__(BillSpider.text_url_field, text_url)

            bills.append(bill)
        return bills

    @staticmethod
    def build_bill(diet_number, bill_category, bill_number, bill_title):
        bill = Bill(None)
        bill.id = f'bill:{diet_number}-{bill_category}-{bill_number}'
        bill.bill_category = bill_category
        bill.bill_number = bill_number
        bill.bill_title = bill_title
        return bill

    @staticmethod
    def build_url(href, title):
        url = Url(None)
        url.id = f'url:{href}'
        url.url = href
        url.domain = 'shugiin.go.jp'
        url.title = title
        return url
