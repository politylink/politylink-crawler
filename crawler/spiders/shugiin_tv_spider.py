import re
from datetime import datetime, timedelta
from logging import getLogger

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import build_minutes, build_url, UrlTitle

LOGGER = getLogger(__name__)


class ShugiinTvSpider(SpiderTemplate):
    name = 'shugiin_tv'
    domain = 'shugiintv.go.jp'
    house_name = '衆議院'

    def __init__(self, start_date, end_date, *args, **kwargs):
        def to_date(date_str):
            return datetime.strptime(date_str, '%Y-%m-%d').date()

        super(ShugiinTvSpider, self).__init__(*args, **kwargs)
        start_date = to_date(start_date)
        end_date = to_date(end_date)
        self.start_urls = []
        for i in range((end_date - start_date).days):
            self.start_urls.append(self.build_start_url(start_date + timedelta(i)))

    @staticmethod
    def build_start_url(date):
        return 'https://www.shugiintv.go.jp/jp/index.php?ex=VL&u_day={}'.format(date.strftime('%Y%m%d'))

    @staticmethod
    def build_minutes_url(deli_id):
        return 'https://www.shugiintv.go.jp/jp/index.php?ex=VL&deli_id={}'.format(deli_id)

    def parse(self, response):
        deli_ids = []
        h_pages = []
        for a in response.xpath('//table//td/a'):
            href = a.xpath('./@href').get()
            text = a.xpath('./text()').get()
            match = re.search('deli_id=([0-9]+)', href)
            if match:
                deli_ids.append(match.group(1))
            if text == '次の結果':
                match = re.search("h_page.value='([0-9]+)'", href)
                if match:
                    h_pages.append(match.group(1))
        LOGGER.info(f'scraped {len(deli_ids)} deli_ids from {response.url}: {deli_ids}')
        LOGGER.info(f'scraped {len(h_pages)} h_pages from {response.url}: {h_pages}')

        for deli_id in deli_ids:
            yield response.follow(
                self.build_minutes_url(deli_id),
                callback=self.parse_minutes
            )
        for h_page in h_pages:
            yield scrapy.FormRequest.from_response(
                response,
                formdata={'h_page': h_page},
                callback=self.parse
            )

    def parse_minutes(self, response):
        maybe_minutes = self.scrape_minutes(response)
        if not maybe_minutes:
            LOGGER.warning(f'failed to parse minutes from {response.url}. skipping...')

        minutes = maybe_minutes
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

    def scrape_minutes(self, response):
        date_time, meeting_name = None, None
        for row in response.xpath('//div[@id="library"]/table//tr'):
            tds = row.xpath('./td')
            term = tds[1].xpath('.//text()').get()
            desc = tds[3].xpath('.//text()').get().split()[0]
            if term == '開会日':
                date_time = datetime.strptime(desc, '%Y年%m月%d日')
            if term == '会議名':
                meeting_name = self.get_full_meeting_name(desc)
        if date_time and meeting_name:
            minutes = build_minutes(self.house_name + meeting_name, date_time)
            topics = []
            tables = response.xpath('//div[@id="library2"]/table')
            if tables:
                for row in tables[0].xpath('./tr'):
                    topic = row.xpath('./td//text()').get()
                    if topic and not topic.startswith('案件'):
                        topics.append(topic)
            if topics:
                minutes.topics = topics
            return minutes
        return None

    @staticmethod
    def get_full_meeting_name(meeting_name):
        # copied from https://www.shugiintv.go.jp/jp/index.php?ex=IF
        full_name_map = {
            '倫理選挙特別委員会': '政治倫理の確立及び公職選挙法改正に関する特別委員会',
            '沖縄北方特別委員会': '沖縄及び北方問題に関する特別委員会',
            '拉致問題特別委員会': '北朝鮮による拉致問題等に関する特別委員会',
            '消費者問題特別委員会': '消費者問題に関する特別委員会',
            '科学技術特別委員会': '科学技術・イノベーション推進特別委員会',
            '震災復興特別委員会': '東日本大震災復興特別委員会',
            '地方創生特別委員会': '地方創生に関する特別委員会'
        }
        if meeting_name in full_name_map:
            return full_name_map[meeting_name]
        return meeting_name
