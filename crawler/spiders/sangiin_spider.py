from logging import getLogger

from crawler.spiders import SpiderTemplate
from crawler.utils import extract_text, extract_full_href_or_none, build_bill, build_url, to_neo4j_datetime
from politylink.graphql.schema import Url, Bill
from politylink.utils import DateConverter

LOGGER = getLogger(__name__)


class SangiinSpider(SpiderTemplate):
    name = 'sangiin'
    domain = 'sangiin.go.jp'
    start_urls = ['https://www.sangiin.go.jp/japanese/joho1/kousei/gian/201/gian.htm']

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
            if url.title == '議案情報':
                yield response.follow(url.url, callback=self.parse_meisai, meta=url.meta)
        LOGGER.info(f'finished successfully')

    def parse_meisai(self, response):
        """
        議案情報ページから各種日付を取得し、GraphQLに保存する
        """

        def extract_datetime_or_none(data, key):
            try:
                if key in data:
                    val = data[key].strip()
                    if val:
                        return DateConverter.convert(val)
            except ValueError as e:
                LOGGER.warning(f'failed to parse datetime from {data[key]}: {e}')
            return None

        def set_datetime_if_exists(key, maybe_datetime):
            if maybe_datetime:
                setattr(bill, key, to_neo4j_datetime(maybe_datetime))

        tables = response.xpath('//table')
        bill = Bill(None)
        bill.id = response.meta['bill_id']

        submission_data = self.parse_meisai_table(tables[1])
        set_datetime_if_exists(
            'submitted_date',
            extract_datetime_or_none(submission_data, '提出日')
        )
        sangiin_committee_data = self.parse_meisai_table(tables[2])
        if sangiin_committee_data.get('議決・継続結果') == '可決':
            set_datetime_if_exists(
                'passed_councilors_committee_date',
                extract_datetime_or_none(sangiin_committee_data, '議決日')
            )
        sangiin_data = self.parse_meisai_table(tables[3])
        if sangiin_data.get('議決') == '可決':
            set_datetime_if_exists(
                'passed_councilors_date',
                extract_datetime_or_none(sangiin_data, '議決日')
            )
        shugiin_committee_data = self.parse_meisai_table(tables[4])
        if shugiin_committee_data.get('議決・継続結果') == '可決':
            set_datetime_if_exists(
                'passed_representatives_committee_date',
                extract_datetime_or_none(shugiin_committee_data, '議決日')
            )
        shugiin_data = self.parse_meisai_table(tables[5])
        if shugiin_data.get('議決') == '可決':
            set_datetime_if_exists(
                'passed_representatives_date',
                extract_datetime_or_none(shugiin_data, '議決日')
            )
        proclaim_data = self.parse_meisai_table(tables[6])
        set_datetime_if_exists(
            'proclaimed_date',
            extract_datetime_or_none(proclaim_data, '公布年月日')
        )

        self.client.exec_merge_bill(bill)
        LOGGER.debug(f'merged date for {bill.id}')

    @staticmethod
    def scrape_bills_and_urls(response):
        bills, urls = [], []
        tables = response.xpath('//table')
        for table, category in zip(tables[1:4], ('閣法', '衆法', '参法')):
            res = SangiinSpider.scrape_bills_and_urls_from_table(table, category, response.url)
            bills.extend(res[0])
            urls.extend(res[1])
        return bills, urls

    @staticmethod
    def scrape_bills_and_urls_from_table(table, bill_category, response_url):
        bills, urls = [], []
        for row in table.xpath('./tr')[1:]:  # skip header
            cells = row.xpath('./td')
            assert len(cells) == 5

            # build Bill instance with necessary info
            try:
                diet_number = int(extract_text(cells[0]))
                submission_number = int(extract_text(cells[1]))
                bill_name = extract_text(cells[2])
            except Exception as e:
                LOGGER.warning(f'failed to parse row:\n{row.get()}\n{e}')
                continue
            bill = build_bill(bill_category, diet_number, submission_number, bill_name)
            bills.append(bill)

            # build  URL if exists
            maybe_meisai_href = extract_full_href_or_none(cells[2], response_url)
            if maybe_meisai_href:
                url = build_url(maybe_meisai_href, title='議案情報', domain=SangiinSpider.domain)
                url.meta = {'bill_id': bill.id}
                urls.append(url)

        return bills, urls

    @staticmethod
    def parse_meisai_table(table):
        data = dict()
        for row in table.xpath('./tr'):
            key = extract_text(row.xpath('./th'))
            val = extract_text(row.xpath('./td'))
            data[key] = val
        return data
