import re
from datetime import datetime
from logging import getLogger

from crawler.spiders import SpiderTemplate
from crawler.utils import extract_full_href_or_none, extract_text, build_url, UrlTitle, build_minutes
from politylink.graphql.client import GraphQLException
from politylink.graphql.schema import Committee

LOGGER = getLogger(__name__)


class ShugiinMinutesSpider(SpiderTemplate):
    name = 'shugiin_minutes'
    domain = 'shugiin.go.jp'

    def __init__(self, diet=None, *args, **kwargs):
        super(ShugiinMinutesSpider, self).__init__(*args, **kwargs)
        self.start_urls = [self.build_start_url(diet)]

    @staticmethod
    def build_start_url(diet=None):
        template = 'http://www.shugiin.go.jp/internet/itdb_rchome.nsf/html/rchome/IinkaiNews{}_m.htm'
        return template.format(diet) if diet else template.format('')

    def parse(self, response):
        LOGGER.info(f'got response from {response.url}')
        committees = []
        for table in response.xpath('//table')[:2]:
            committees += self.scrape_committees_from_table(table, response.url)
        LOGGER.info(f'scraped {len(committees)} committees from {response.url}')

        for committee in committees:
            yield response.follow(
                committee.url,
                callback=self.parse_committee,
                meta={'committee_name': committee.name}
            )

    def parse_committee(self, response):
        committee_name = response.meta["committee_name"]
        minutes_urls = self.scrape_minutes_urls_from_response(response)
        LOGGER.info(f'scraped {len(minutes_urls)} minutes urls for {committee_name}')

        for minutes_url in minutes_urls:
            yield response.follow(
                minutes_url,
                callback=self.parse_minutes,
                meta=response.meta
            )

    def parse_minutes(self, response):
        # merge url if exists
        maybe_href = extract_full_href_or_none(response.xpath('//h4'), response.url)
        if not maybe_href:
            LOGGER.warning(f'failed to find url in {response.url}')
            return
        url = build_url(maybe_href, title=UrlTitle.GAIYOU_PDF, domain=self.domain)
        self.gql_client.merge(url)
        LOGGER.debug(f'merged {url.id}')

        # link to minutes
        title = extract_text(response.xpath('//title'))
        committee_name = response.meta['committee_name']
        date_time = self.extract_datetime_from_title(title)
        minutes = build_minutes(committee_name, date_time)
        try:
            self.gql_client.get(minutes.id, ['id'])  # minutes should already exist
            self.gql_client.link(url.id, minutes.id)
        except GraphQLException:
            LOGGER.warning(f'failed to find minutes ({committee_name}, {date_time})')

    @staticmethod
    def extract_datetime_from_title(title):
        pattern = r'第(.*)回国会(.*)月(.*)日'
        match = re.search(pattern, title)
        if not match:
            raise ValueError(f'failed to extract datetime from {title}')
        # ToDo: properly handle year (POL-154)
        return datetime(year=2020, month=int(match.group(2)), day=int(match.group(3)))

    @staticmethod
    def scrape_committees_from_table(table, root_url):
        committees = []
        for row in table.xpath('./tr'):
            for cell in row.xpath('./td'):
                committee = Committee(None)
                committee.name = '衆議院' + extract_text(cell.xpath('./span/a'))
                committee.url = extract_full_href_or_none(cell, root_url)
                committees.append(committee)
        return committees

    @staticmethod
    def scrape_minutes_urls_from_response(response):
        urls = []
        for li in response.xpath('//div[@id="mainlayout"]/li'):
            url = extract_full_href_or_none(li, response.url)
            if url:
                urls.append(url)
        return urls
