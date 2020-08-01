from logging import getLogger
from urllib.parse import urljoin

import scrapy

from politylink.graphql.client import GraphQLClient
from politylink.graphql.schema import Bill, Url
from politylink.idgen import idgen

LOGGER = getLogger(__name__)


class ShugiinSpider(scrapy.Spider):
    name = "shugiin"
    start_urls = ['http://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/menu.htm']

    def __init__(self, *args, **kwargs):
        super(ShugiinSpider, self).__init__(*args, **kwargs)
        self.client = GraphQLClient()

    def parse(self, response):
        """
        議案一覧ページからBillとURLを取得し、GraphQLに保存する
        """

        bills, urls = self.scrape_bills_and_urls(response)
        LOGGER.info(f'scraped {len(bills)} bills')
        LOGGER.info(f'scraped {len(urls)} urls')

        for bill in bills:
            assert isinstance(bill, Bill)
            self.client.exec_merge_bill(bill)
            LOGGER.debug(f'merged {bill.id}')
        LOGGER.info(f'merged {len(bills)} bills')

        for url in urls:
            assert isinstance(url, Url)
            self.client.exec_merge_url(url)
            self.client.exec_merge_url_referred_bills(url.id, url.meta['bill_id'])
            LOGGER.debug(f'merged {url.id}')
        LOGGER.info(f'merged {len(urls)} urls')

        for url in urls:
            assert isinstance(url, Url)
            if url.title == '本文':
                yield response.follow(url.url, callback=self.parse_honbun, meta=url.meta)
        LOGGER.info(f'finished successfully')

    def parse_honbun(self, response):
        """
        本文ページから法案原文ページへジャンプする
        """

        houan_link = None
        for a in response.xpath('//a'):
            text = a.xpath('./text()').get()
            if isinstance(text, str) and '提出時法律案' in text:
                houan_link = a.xpath('./@href').get()
                break
        if houan_link:
            yield response.follow(houan_link, callback=self.parse_houan, meta=response.meta)

    def parse_houan(self, response):
        """
        法案ページから議案の理由を取得し、GraphQLに保存する
        """

        paragraphs = response.xpath('//div[@id="mainlayout"]/p')
        if not paragraphs:
            paragraphs = response.xpath('//div[@id="mainlayout"]/div[@class="WordSection1"]/p[position()>3]')
        content = [''.join(p.xpath('.//text()').getall()).strip() for p in paragraphs]

        if '理　由' in content:
            bill = Bill(None)
            bill.id = response.meta['bill_id']
            bill.reason = '\n'.join(content[content.index('理　由') + 1:])
            self.client.exec_merge_bill(bill)
            LOGGER.debug(f'merged reason for {bill.id}')

    @staticmethod
    def scrape_bills_and_urls(response):
        bills, urls = [], []
        tables = response.xpath('//table')
        for table, category in zip(tables[:3], ('衆法', '参法', '閣法')):
            res = ShugiinSpider.scrape_bills_and_urls_from_table(table, category, response.url)
            bills.extend(res[0])
            urls.extend(res[1])
        return bills, urls

    @staticmethod
    def scrape_bills_and_urls_from_table(table, bill_category, response_url):
        def extract_text(cell):
            return cell.xpath('.//text()').get()

        def extract_full_href_or_none(cell):
            selector = cell.xpath('.//a/@href')
            if len(selector) == 1:
                return urljoin(response_url, selector[0].get())
            return None

        bills, urls = [], []
        for row in table.xpath('./tr')[1:]:  # skip header
            cells = row.xpath('./td')
            assert len(cells) == 6

            # build Bill instance with necessary info
            try:
                diet_number = int(extract_text(cells[0]))
                submission_number = int(extract_text(cells[1]))
                bill_name = extract_text(cells[2])
            except Exception as e:
                LOGGER.warning(f'failed to parse row:\n{row.get()}\n{e}')
                continue
            bill = ShugiinSpider.build_bill(bill_category, diet_number, submission_number, bill_name)
            bills.append(bill)

            # build keika URL if exists
            maybe_keika_href = extract_full_href_or_none(cells[4])
            if maybe_keika_href:
                url = ShugiinSpider.build_url(maybe_keika_href, '経過')
                url.meta = {'bill_id': bill.id}
                urls.append(url)

            # build honbun URL if exists
            maybe_honbun_href = extract_full_href_or_none(cells[5])
            if maybe_honbun_href:
                url = ShugiinSpider.build_url(maybe_honbun_href, '本文')
                url.meta = {'bill_id': bill.id}
                urls.append(url)

        return bills, urls

    @staticmethod
    def build_bill(bill_category, diet_number, submission_number, bill_name):
        bill = Bill(None)
        bill.name = bill_name
        bill.bill_number = f'第{diet_number}回国会{bill_category}第{submission_number}号'
        bill.id = idgen(bill)
        return bill

    @staticmethod
    def build_url(href, title):
        url = Url(None)
        url.url = href
        url.domain = 'shugiin.go.jp'
        url.title = title
        url.id = idgen(url)
        return url
