import re
from datetime import datetime
from logging import getLogger

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import build_minutes, build_url, UrlTitle
from politylink.graphql.client import GraphQLException

LOGGER = getLogger(__name__)


class VrsddTvSpider(SpiderTemplate):
    name = 'vrsdd_tv'
    domain = 'grips.ac.jp'

    def __init__(self, next_id=-1, last_id=100000, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if next_id == -1:
            next_id = self.fetch_next_id()
        self.next_id = int(next_id)
        self.last_id = int(last_id)

    def build_next_url(self):
        self.next_id += 1
        return 'http://gclip1.grips.ac.jp/video/video/{}'.format(self.next_id)

    def fetch_next_id(self):
        query = """
        {
          Minutes(orderBy:startDateTime_desc, first:10) {
            urls{title, url}
          }
        }
        """
        next_id = -1
        data = self.gql_client.exec(query)
        for minutes in data['Minutes']:
            for url in minutes['urls']:
                if url['title'] == UrlTitle.VRSDD.value:
                    id_ = int(url['url'].split('/')[-1])
                    next_id = max(next_id, id_)
        if next_id == -1:
            raise ValueError('no vrsdd URLs found in GraphQL. Please manually specify next_id')
        return next_id

    def start_requests(self):
        yield scrapy.Request(self.build_next_url(), self.parse)

    def parse(self, response):
        page_title = response.xpath('//title/text()').get()
        house_name, meeting_name, date_time = self.parse_page_title(page_title)
        minutes = build_minutes(house_name + meeting_name, date_time)
        url = build_url(response.url, UrlTitle.VRSDD, self.domain)
        LOGGER.info(f'found url for minutes: {minutes}, {url}')
        try:
            # do not merge minutes because this is unofficial data source
            self.delete_old_urls(minutes.id, url.title)
            self.gql_client.merge(url)
            self.gql_client.link(url.id, minutes.id)
        except GraphQLException as e:  # expected when official minutes does not exist yet
            LOGGER.warning(e)
        if self.next_id < self.last_id:
            yield response.follow(self.build_next_url(), callback=self.parse)

    @staticmethod
    def parse_page_title(text):
        pattern = r'第(\d+)回\[(衆|参)\] (.+) ([0-9/]+)'
        match = re.search(pattern, text)
        if not match:
            raise ValueError(f'failed to parse minutes name from {text}')
        house_name = '{}議院'.format(match.group(2))
        meeting_name = match.group(3)
        date_time = datetime.strptime(match.group(4), '%Y/%m/%d')
        return house_name, meeting_name, date_time
