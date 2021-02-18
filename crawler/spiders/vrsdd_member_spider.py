from logging import getLogger

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import build_url, UrlTitle

LOGGER = getLogger(__name__)


class VrsddMemberSpiider(SpiderTemplate):
    handle_httpstatus_list = [404]
    name = 'vrsdd_member'
    domain = 'grips.ac.jp'

    def __init__(self, next_id=0, last_id=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.next_id = int(next_id)
        self.last_id = int(last_id)

    def build_next_url(self):
        self.next_id += 1
        return 'http://gclip1.grips.ac.jp/video/dietmember/{}/show'.format(self.next_id)

    def start_requests(self):
        yield scrapy.Request(self.build_next_url(), self.parse)

    def parse(self, response):
        if response.status != 404:
            name = response.xpath('//h1//text()').get()
            try:
                member = self.member_finder.find_one(name)
                url = build_url(response.url, UrlTitle.VRSDD, self.domain)
                self.gql_client.merge(url)
                self.gql_client.link(url.id, member.id)
                LOGGER.info(f'[{self.next_id}/{self.last_id}] linked {url.id} to {member.id}')
            except Exception:
                LOGGER.exception(f'failed to process {response.url}')
        if self.next_id < self.last_id:
            yield response.follow(self.build_next_url(), callback=self.parse)
