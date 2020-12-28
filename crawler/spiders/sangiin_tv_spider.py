import re
from datetime import datetime
from logging import getLogger

import scrapy

from crawler.spiders import TvSpiderTemplate
from crawler.utils import build_minutes, build_url, UrlTitle

LOGGER = getLogger(__name__)


class SangiinTvSpider(TvSpiderTemplate):
    name = 'sangiin_tv'
    domain = 'sangiin.go.jp'
    house_name = '参議院'

    def __init__(self, next_id=-1, failure_in_row_limit=10, *args, **kwargs):
        super(SangiinTvSpider, self).__init__(*args, **kwargs)
        if next_id == -1:
            try:
                next_id = self.get_last_sid() - failure_in_row_limit
            except Exception as e:
                msg = f'failed to get last sid from GraphQL, you need to specify next_id argument'
                raise Exception(msg) from e

        self.next_id = next_id
        self.failure_in_row_limit = failure_in_row_limit
        self.failure_in_row = 0

    def get_last_sid(self):
        query = """
        {
          Minutes(orderBy:startDateTime_desc, first:1, filter:{name_contains:"参議院"}) {
            urls{title, url}
          }
        }
        """
        data = self.gql_client.exec(query)
        if len(data['Minutes']) == 0:
            raise ValueError(f'Minutes does not exist in GraphQL response: {data}')
        for url in data['Minutes'][0]['urls']:
            if url['title'] == UrlTitle.SHINGI_TYUKEI.value:
                sid = int(re.search('sid=(\d+)', url['url']).group(1))
                return sid
        raise ValueError(f'sid does not exist in GraphQL response: {data}')

    def build_next_url(self):
        self.next_id += 1
        return 'https://www.webtv.sangiin.go.jp/webtv/detail.php?sid={}'.format(self.next_id)

    def start_requests(self):
        yield scrapy.Request(self.build_next_url(), self.parse)

    def parse(self, response):
        try:
            minutes = self.scrape_minutes(response)
        except Exception:
            LOGGER.info(f'failed to parse minutes from {response.url}')
            self.failure_in_row += 1
            if self.failure_in_row < self.failure_in_row_limit:
                yield response.follow(self.build_next_url(), callback=self.parse)
            return

        url = build_url(response.url, UrlTitle.SHINGI_TYUKEI, self.domain)
        self.store_minutes_and_url(minutes, url)

        self.failure_in_row = 0
        yield response.follow(self.build_next_url(), callback=self.parse)

    def scrape_minutes(self, response):
        content = response.xpath('//div[@id="detail-contents-inner"]')
        if not content:
            content = response.xpath('//div[@id="detail-contents-inner2"]')
        date_time, meeting_name = None, None
        for dl in content.xpath('//dl'):
            term = dl.xpath('./dt/text()').get()
            desc = dl.xpath('./dd/text()').get()
            if term == '開会日':
                date_time = datetime.strptime(desc, '%Y年%m月%d日')
            elif term == '会議名':
                meeting_name = desc
        if not (date_time and meeting_name):
            msg = f'failed to extract minutes detail: date_time={date_time}, meeting_name={meeting_name}'
            raise ValueError(msg)

        minutes = build_minutes(self.house_name + meeting_name, date_time)
        summary = ''.join(map(lambda x: x.strip(), content.xpath('./span/text()').getall()))
        if summary:
            minutes.summary = summary
        topics = content.xpath('./ul/li/text()').getall()
        if topics:
            LOGGER.debug(f'scraped topics={topics}')
            minutes.topics = topics
        speakers = content.xpath('./ul/li/a/text()').getall()
        if speakers:
            LOGGER.debug(f'scraped speakers={topics}')
            minutes.speakers = speakers
        return minutes
