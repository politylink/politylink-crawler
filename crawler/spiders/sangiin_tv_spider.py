from datetime import datetime
from logging import getLogger

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import build_minutes, build_url, UrlTitle

LOGGER = getLogger(__name__)
FAILURE_IN_ROW_LIMIT = 10


class SangiinTvSpider(SpiderTemplate):
    name = 'sangiin_tv'
    domain = 'sangiin.go.jp'
    house_name = '参議院'

    def __init__(self, *args, **kwargs):
        super(SangiinTvSpider, self).__init__(*args, **kwargs)
        self.next_id = 5900
        self.failure_in_row = 0

    def build_next_url(self):
        self.next_id += 1
        return 'https://www.webtv.sangiin.go.jp/webtv/detail.php?sid={}'.format(self.next_id)

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
            self.failure_in_row = 0
        else:
            LOGGER.info(f'failed to parse minutes from {response.url}. skipping...')
            self.failure_in_row += 1

        if self.failure_in_row < FAILURE_IN_ROW_LIMIT:
            yield response.follow(self.build_next_url(), callback=self.parse)

    def scrape_minutes(self, response):
        content = response.xpath('//div[@id="detail-contents-inner"]')
        date_time, meeting_name = None, None
        for dl in content.xpath('//dl'):
            term = dl.xpath('./dt/text()').get()
            desc = dl.xpath('./dd/text()').get()
            if term == '開会日':
                date_time = datetime.strptime(desc, '%Y年%m月%d日')
            elif term == '会議名':
                meeting_name = desc
        if date_time and meeting_name:
            minutes = build_minutes(self.house_name, meeting_name, date_time)
            summary = ''.join(map(lambda x: x.strip(), content.xpath('./span/text()').getall()))
            if summary:
                minutes.summary = summary
            return minutes
        return None
