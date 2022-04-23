from logging import getLogger

from crawler.spiders import SpiderTemplate
from crawler.utils.elasticsearch import build_bill_text
from crawler.utils.graphql import build_bill, build_url, UrlTitle
from crawler.utils.scrape import extract_text, extract_full_href_or_none, extract_parliamentary_groups
from politylink.elasticsearch.client import OpType
from politylink.graphql.schema import Bill, Url, BillCategory

LOGGER = getLogger(__name__)


class ShugiinSpider(SpiderTemplate):
    name = 'shugiin'
    domain = 'shugiin.go.jp'

    def __init__(self, diet=None, *args, **kwargs):
        super(ShugiinSpider, self).__init__(*args, **kwargs)
        self.diet = self.get_diet(diet)
        self.start_urls = [self.build_start_url(self.diet.number)]

    @staticmethod
    def build_start_url(diet_number):
        return f'http://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/kaiji{diet_number}.htm'

    def parse(self, response):
        """
        議案一覧ページからBillとURLを取得し、GraphQLに保存する
        """

        LOGGER.info(f'got response from {response.url}')
        bills, urls = self.scrape_bills_and_urls(response)
        self.gql_client.bulk_merge(bills)
        self.gql_client.bulk_link(map(lambda x: x.id, bills), [self.diet.id] * len(bills))
        LOGGER.info(f'merged {len(bills)} bills')

        for url in urls:
            bill_id = url.meta['bill_id']
            self.delete_old_urls(bill_id, url.title)
            self.gql_client.merge(url)
            self.gql_client.link(url.id, bill_id)
        LOGGER.info(f'merged {len(urls)} urls')

        for url in urls:
            assert isinstance(url, Url)
            if url.title == UrlTitle.HONBUN:
                yield response.follow(url.url, callback=self.parse_honbun, meta=url.meta)
            elif url.title == UrlTitle.KEIKA:
                yield response.follow(url.url, callback=self.parse_keika, meta=url.meta)

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

        def extract_clean_text(paragraph):
            text = ''.join(paragraph.xpath('.//text()').getall())
            return ' '.join(text.split()).strip()  # standardize delimiter

        bill_id = response.meta['bill_id']
        paragraphs = response.xpath('//div[@id="mainlayout"]/p')
        if not paragraphs:
            paragraphs = response.xpath('//div[@id="mainlayout"]/div[@class="WordSection1"]/p[position()>3]')
        texts = [extract_clean_text(p) for p in paragraphs]
        try:
            bill_text = build_bill_text(bill_id, texts)
        except ValueError as e:
            LOGGER.warning(e)
            return
        self.es_client.index(bill_text, op_type=OpType.MERGE)
        LOGGER.info(f'merged BillText in Elasticsearch for {bill_id}')

        bill = Bill(None)
        bill.id = bill_id
        bill.reason = bill_text.reason
        self.gql_client.merge(bill)
        LOGGER.info(f'merged reason in GraphQL for {bill_id}')

    def parse_keika(self, response):
        """
        経過ページから賛成/反対会派を取得し、GraphQLに保存する
        """

        bill_id = response.meta['bill_id']
        bill = Bill(None)
        bill.id = bill_id

        table = response.xpath('//table')[0]
        for row in table.xpath('./tr')[1:]:  # skip header
            cells = row.xpath('./td')
            assert len(cells) == 2
            key = extract_text(cells[0])
            value = extract_text(cells[1])
            if key and value:
                if key == '衆議院審議時賛成会派':
                    groups = extract_parliamentary_groups(value)
                    if groups:
                        bill.supported_groups = groups
                elif key == '衆議院審議時反対会派':
                    groups = extract_parliamentary_groups(value)
                    if groups:
                        bill.opposed_groups = groups

        if hasattr(bill, 'supported_groups') or hasattr(bill, 'opposed_groups'):
            self.gql_client.merge(bill)
            LOGGER.info(f'merged groups in GraphQL for {bill_id}')

    @staticmethod
    def scrape_bills_and_urls(response):
        bills, urls = [], []
        tables = response.xpath('//table')
        for table in tables[:3]:
            res = ShugiinSpider.scrape_bills_and_urls_from_table(table, response.url)
            bills.extend(res[0])
            urls.extend(res[1])
        return bills, urls

    @staticmethod
    def scrape_bills_and_urls_from_table(table, response_url):
        def get_bill_category_or_none(caption):
            if caption == '閣法の一覧':
                return BillCategory.KAKUHOU
            elif caption == '衆法の一覧':
                return BillCategory.SHUHOU
            elif caption == '参法の一覧':
                return BillCategory.SANHOU
            else:
                return None

        bills, urls = [], []

        caption = extract_text(table.xpath('./caption')).strip()
        maybe_bill_category = get_bill_category_or_none(caption)
        if not maybe_bill_category:
            return bills, urls
        bill_category = maybe_bill_category

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
            bill = build_bill(bill_category, diet_number, submission_number, bill_name)
            bills.append(bill)

            # build keika URL if exists
            maybe_keika_href = extract_full_href_or_none(cells[4], response_url)
            if maybe_keika_href:
                url = build_url(maybe_keika_href, UrlTitle.KEIKA, ShugiinSpider.domain)
                url.meta = {'bill_id': bill.id}
                urls.append(url)

            # build honbun URL if exists
            maybe_honbun_href = extract_full_href_or_none(cells[5], response_url)
            if maybe_honbun_href:
                url = build_url(maybe_honbun_href, UrlTitle.HONBUN, ShugiinSpider.domain)
                url.meta = {'bill_id': bill.id}
                urls.append(url)

        return bills, urls
