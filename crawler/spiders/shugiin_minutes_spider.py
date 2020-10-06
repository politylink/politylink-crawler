import re
from datetime import datetime
from logging import getLogger

from crawler.spiders import SpiderTemplate
from crawler.utils import extract_full_href_or_none, extract_text, build_url, UrlTitle
from politylink.graphql.schema import Committee

LOGGER = getLogger(__name__)


class ShugiinMinutesSpider(SpiderTemplate):
    name = 'shugiin_minutes'
    domain = 'shugiin.go.jp'
    start_urls = ['http://www.shugiin.go.jp/internet/itdb_rchome.nsf/html/rchome/IinkaiNews_m.htm']

    def parse(self, response):
        committees = []
        for table in response.xpath('//table')[:2]:
            committees += self.scrape_committees_from_table(table, response.url)
        LOGGER.debug(f'scraped {len(committees)} committees')

        for committee in committees:
            yield response.follow(
                committee.url,
                callback=self.parse_committee,
                meta={'committee_name': committee.name}
            )

    def parse_committee(self, response):
        minutes_urls = self.scrape_minutes_urls_from_response(response)
        LOGGER.debug(f'scraped {len(minutes_urls)} minutes urls')

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

        # merge with Minutes if exists
        committee_name = response.meta['committee_name']
        title = extract_text(response.xpath('//title'))
        dt = self.extract_datetime_from_title(title)
        minutes_list = self.minutes_finder.find(committee_name, dt)
        if len(minutes_list) != 1:  # multiple Minutes can be found when 分科会
            LOGGER.warning(
                f'found {len(minutes_list)} Minutes that match with ({committee_name}, {dt}): {minutes_list}')
        self.gql_client.bulk_link([url.id] * len(minutes_list), map(lambda x: x.id, minutes_list))

    @staticmethod
    def extract_datetime_from_title(title):
        pattern = r'第(.*)回国会(.*)月(.*)日'
        match = re.search(pattern, title)
        if not match:
            raise ValueError(f'failed to extract datetime from {title}')
        return datetime(year=2020, month=int(match.group(2)), day=int(match.group(3)))  # ToDo: properly handle year

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
