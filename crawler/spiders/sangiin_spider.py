from logging import getLogger

from crawler.spiders import SpiderTemplate
from crawler.utils import extract_text, extract_full_href_or_none, build_bill, build_url, to_neo4j_datetime, UrlTitle, \
    BillCategory, build_diet, build_bill_activity
from politylink.graphql.schema import Url, Bill, House
from politylink.utils import DateConverter

LOGGER = getLogger(__name__)


class SangiinSpider(SpiderTemplate):
    name = 'sangiin'
    domain = 'sangiin.go.jp'

    def __init__(self, diet=None, *args, **kwargs):
        super(SangiinSpider, self).__init__(*args, **kwargs)
        self.diet = build_diet(diet) if diet else self.get_latest_diet()
        self.start_urls = [self.build_start_url(self.diet.number)]

    @staticmethod
    def build_start_url(diet_number):
        return f'https://www.sangiin.go.jp/japanese/joho1/kousei/gian/{diet_number}/gian.htm'

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
        議案情報ページからBillとActivityを取得し、GraphQLに保存する
        """

        bill, activities = self.scrape_bill_and_activities_from_meisai(response)
        self.gql_client.bulk_merge([bill] + activities)
        LOGGER.info(f'merged 1 Bill and {len(activities)} Activity')
        LOGGER.debug(f'Bill={bill}, Activity={activities}')
        if bill.committee_ids:
            self.gql_client.bulk_link([bill.id] * len(bill.committee_ids), bill.committee_ids)
            LOGGER.debug(f'linked {bill.id} to {bill.committee_ids}')
        self.link_activities(activities)

    def scrape_bills_and_urls(self, response):
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
                res = self.scrape_bills_and_urls_from_table(table, maybe_bill_category, response.url)
                bills.extend(res[0])
                urls.extend(res[1])
        return bills, urls

    def scrape_bills_and_urls_from_table(self, table, bill_category, response_url):
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
                url = build_url(maybe_meisai_href, UrlTitle.GIAN_ZYOUHOU, self.domain)
                url.meta = {'bill_id': bill.id}
                urls.append(url)

        return bills, urls

    def scrape_bill_and_activities_from_meisai(self, response):

        def set_datetimes_to_bill():
            """
            set 6 datetime fields in Bill if data exists
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

            set_datetime_if_exists(
                'submitted_date',
                extract_datetime_or_none(submission_data, '提出日')
            )
            if sangiin_committee_data.get('議決・継続結果') in ['可決', '修正']:
                set_datetime_if_exists(
                    'passed_councilors_committee_date',
                    extract_datetime_or_none(sangiin_committee_data, '議決日')
                )
            if sangiin_data.get('議決') in ['可決', '修正']:
                set_datetime_if_exists(
                    'passed_councilors_date',
                    extract_datetime_or_none(sangiin_data, '議決日')
                )
            if shugiin_committee_data.get('議決・継続結果') in ['可決', '修正']:
                set_datetime_if_exists(
                    'passed_representatives_committee_date',
                    extract_datetime_or_none(shugiin_committee_data, '議決日')
                )
            if shugiin_data.get('議決') in ['可決', '修正']:
                set_datetime_if_exists(
                    'passed_representatives_date',
                    extract_datetime_or_none(shugiin_data, '議決日')
                )
            set_datetime_if_exists(
                'proclaimed_date',
                extract_datetime_or_none(proclaim_data, '公布年月日')
            )

        def set_first_house_to_bill():
            """
            set Bill.first_house if data exists
            """

            data, key = submission_data, '先議区分'
            if key in data:
                val = data[key].strip()
                if val == '衆先議':
                    bill.first_house = House.REPRESENTATIVES
                elif val == '本院先議':
                    bill.first_house = House.COUNCILORS

        def extract_committee_ids():
            """
            extract assigned Committee IDs if data exists
            """

            def extract_committee_id_or_none(data, key, house_name):
                if key in data:
                    val = data[key].strip()
                    if len(val) > 0:
                        try:
                            committee = self.committee_finder.find_one(house_name + val)
                            return committee.id
                        except Exception as e:
                            LOGGER.warning(e)
                return None

            maybe_ids = [
                extract_committee_id_or_none(sangiin_committee_data, '付託委員会等', '参議院'),
                extract_committee_id_or_none(shugiin_committee_data, '付託委員会等', '衆議院')
            ]
            return list(filter(None, maybe_ids))

        def extract_member_ids():
            """
            extract submitters' Member IDs if data exists
            """

            data, key = submission_data, '発議者'
            if key in data:
                val = data[key].strip()
                if val:
                    return self.member_finder.find(val)
            return []

        tables = response.xpath('//table')
        submission_data = self.parse_meisai_table(tables[1])
        sangiin_committee_data = self.parse_meisai_table(tables[2])
        sangiin_data = self.parse_meisai_table(tables[3])
        shugiin_committee_data = self.parse_meisai_table(tables[4])
        shugiin_data = self.parse_meisai_table(tables[5])
        proclaim_data = self.parse_meisai_table(tables[6])

        bill = Bill(None)
        bill.id = response.meta['bill_id']
        set_datetimes_to_bill()
        set_first_house_to_bill()
        bill.is_passed = hasattr(bill, 'proclaimed_date') or \
                         (hasattr(bill, 'passed_representatives_date') and hasattr(bill, 'passed_councilors_date'))
        bill.committee_ids = extract_committee_ids()  # to link Committee to Bill

        activity_list = []
        for member in extract_member_ids():
            activity = build_bill_activity(member.id, bill.id, bill.submitted_date)
            activity_list.append(activity)

        return bill, activity_list

    @staticmethod
    def parse_meisai_table(table):
        data = dict()
        for row in table.xpath('./tr'):
            key = extract_text(row.xpath('./th'))
            val = extract_text(row.xpath('./td'))
            data[key] = val
        return data
