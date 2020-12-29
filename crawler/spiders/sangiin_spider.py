from logging import getLogger

from crawler.spiders import SpiderTemplate
from crawler.utils import extract_text, extract_full_href_or_none, build_bill, build_url, build_committee, \
    to_neo4j_datetime, UrlTitle, BillCategory, build_diet
from politylink.graphql.schema import Url, Bill, House
from politylink.utils import DateConverter

LOGGER = getLogger(__name__)


class SangiinSpider(SpiderTemplate):
    name = 'sangiin'
    domain = 'sangiin.go.jp'

    def __init__(self, diet, *args, **kwargs):
        super(SangiinSpider, self).__init__(*args, **kwargs)
        self.diet = build_diet(diet)
        self.start_urls = [self.build_start_url(self.diet)]

    @staticmethod
    def build_start_url(diet):
        return f'https://www.sangiin.go.jp/japanese/joho1/kousei/gian/{diet.number}/gian.htm'

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
            if url.title == UrlTitle.GIAN_ZYOUHOU:
                yield response.follow(url.url, callback=self.parse_meisai, meta=url.meta)

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

        def extract_first_house_or_none(data, key):
            if key in data:
                val = data[key].strip()
                if val == '衆先議':
                    return House.REPRESENTATIVES
                elif val == '本院先議':
                    return House.COUNCILORS
            return None

        def extract_committee_id_or_none(data, key, house):
            if key in data:
                committee_name = data[key].strip()
                if len(committee_name) > 0:
                    if house == 'COUNCILORS':
                        committee_name = '参議院' + committee_name
                    elif house == 'REPRESENTATIVES':
                        committee_name = '衆議院' + committee_name
                    committee = build_committee(committee_name, house)
                    return committee.id
            return None

        tables = response.xpath('//table')
        bill = Bill(None)
        bill.id = response.meta['bill_id']

        submission_data = self.parse_meisai_table(tables[1])
        set_datetime_if_exists(
            'submitted_date',
            extract_datetime_or_none(submission_data, '提出日')
        )

        maybe_first_house = extract_first_house_or_none(submission_data, '先議区分')
        if maybe_first_house:
            bill.first_house = maybe_first_house

        sangiin_committee_data = self.parse_meisai_table(tables[2])
        if sangiin_committee_data.get('議決・継続結果') in ['可決', '修正']:
            set_datetime_if_exists(
                'passed_councilors_committee_date',
                extract_datetime_or_none(sangiin_committee_data, '議決日')
            )
        sangiin_data = self.parse_meisai_table(tables[3])
        if sangiin_data.get('議決') in ['可決', '修正']:
            set_datetime_if_exists(
                'passed_councilors_date',
                extract_datetime_or_none(sangiin_data, '議決日')
            )
        shugiin_committee_data = self.parse_meisai_table(tables[4])
        if shugiin_committee_data.get('議決・継続結果') in ['可決', '修正']:
            set_datetime_if_exists(
                'passed_representatives_committee_date',
                extract_datetime_or_none(shugiin_committee_data, '議決日')
            )
        shugiin_data = self.parse_meisai_table(tables[5])
        if shugiin_data.get('議決') in ['可決', '修正']:
            set_datetime_if_exists(
                'passed_representatives_date',
                extract_datetime_or_none(shugiin_data, '議決日')
            )
        proclaim_data = self.parse_meisai_table(tables[6])
        set_datetime_if_exists(
            'proclaimed_date',
            extract_datetime_or_none(proclaim_data, '公布年月日')
        )

        bill.is_passed = hasattr(bill, 'proclaimed_date') or \
                         (hasattr(bill, 'passed_representatives_date') and hasattr(bill, 'passed_councilors_date'))
        self.gql_client.merge(bill)
        LOGGER.info(f'merged date for {bill.id}')

        maybe_sangiin_committee_id = extract_committee_id_or_none(sangiin_committee_data, '付託委員会等',
                                                                  'COUNCILORS')
        if maybe_sangiin_committee_id:
            self.gql_client.link(bill.id, maybe_sangiin_committee_id)
            LOGGER.info(f'linked {bill.id} to {maybe_sangiin_committee_id}')

        maybe_shugiin_committee_id = extract_committee_id_or_none(shugiin_committee_data, '付託委員会等',
                                                                  'REPRESENTATIVES')
        if maybe_shugiin_committee_id:
            self.gql_client.link(bill.id, maybe_shugiin_committee_id)
            LOGGER.info(f'linked {bill.id} to {maybe_shugiin_committee_id}')

    @staticmethod
    def scrape_bills_and_urls(response):
        def get_bill_category_or_none(caption):
            if caption == '法律案（内閣提出）一覧':
                return BillCategory.KAKUHOU
            elif caption == '法律案（衆法）一覧':
                return BillCategory.SHUHOU
            elif caption == '法律案（参法）一覧':
                return BillCategory.SANHOU
            else:
                return None

        bills, urls = [], []

        div = response.xpath('//div[@id="ContentsBox"]')[0]
        tables = div.xpath('./table')
        captions = list(map(lambda x: extract_text(x), div.css('h2.title_text')))
        assert len(tables) == len(captions)

        for table, caption in zip(tables, captions):
            maybe_bill_category = get_bill_category_or_none(caption)
            if maybe_bill_category:
                res = SangiinSpider.scrape_bills_and_urls_from_table(table, maybe_bill_category, response.url)
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
                url = build_url(maybe_meisai_href, UrlTitle.GIAN_ZYOUHOU, SangiinSpider.domain)
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
