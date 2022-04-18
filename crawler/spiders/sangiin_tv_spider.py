import re
from logging import getLogger

import scrapy

from crawler.spiders import TvSpiderTemplate
from crawler.utils import build_minutes, build_url, UrlTitle, deduplicate, extract_datetime

LOGGER = getLogger(__name__)


class SangiinTvSpider(TvSpiderTemplate):
    name = 'sangiin_tv'
    domain = 'sangiin.go.jp'
    house_name = '参議院'

    def __init__(self, next_id=-1, last_id=100000, failure_in_row_limit=10, *args, **kwargs):
        super(SangiinTvSpider, self).__init__(*args, **kwargs)
        if next_id == -1:
            try:
                next_id = self.get_last_sid() - failure_in_row_limit
            except Exception as e:
                msg = f'failed to get last sid from GraphQL, you need to specify next_id argument'
                raise Exception(msg) from e

        self.next_id = int(next_id)
        self.last_id = int(last_id)
        self.failure_in_row_limit = failure_in_row_limit
        self.failure_in_row = 0

    def get_last_sid(self):
        query = """
        {
          Minutes(orderBy:startDateTime_desc, first:10, filter:{name_contains:"参議院"}) {
            urls{title, url}
          }
        }
        """
        data = self.gql_client.exec(query)
        for minutes in data['Minutes']:
            for url in minutes['urls']:
                if url['title'] == UrlTitle.SHINGI_TYUKEI.value:
                    sid = int(re.search('sid=(\d+)', url['url']).group(1))
                    return sid
        raise ValueError('sid does not found in the latest {} minutes'.format(len(data['minutes'])))

    def build_next_url(self):
        self.next_id += 1
        return 'https://www.webtv.sangiin.go.jp/webtv/detail.php?sid={}'.format(self.next_id)

    def start_requests(self):
        yield scrapy.Request(self.build_next_url(), self.parse)

    def parse(self, response):
        try:
            minutes, activity_list, url_list = self.scrape_minutes_activities_urls(response)
        except Exception:
            LOGGER.warning(f'failed to parse minutes from {response.url}')
            self.failure_in_row += 1
            if self.next_id < self.last_id and self.failure_in_row < self.failure_in_row_limit:
                yield response.follow(self.build_next_url(), callback=self.parse)
            return

        self.gql_client.bulk_merge([minutes] + activity_list + url_list)
        LOGGER.info(f'merged 1 Minutes, {len(activity_list)} activities and {len(url_list)} urls')
        self.link_minutes(minutes)
        self.link_activities(activity_list)
        self.link_urls(url_list)

        self.failure_in_row = 0
        if self.next_id < self.last_id:
            yield response.follow(self.build_next_url(), callback=self.parse)

    def scrape_minutes_activities_urls(self, response):
        content = response.xpath('//div[@id="detail-contents-inner"]')
        if not content:
            content = response.xpath('//div[@id="detail-contents-inner2"]')
        date_time, meeting_name = None, None
        for dl in content.xpath('//dl'):
            term = dl.xpath('./dt/text()').get()
            desc = dl.xpath('./dd/text()').get()
            if term == '開会日':
                date_time = extract_datetime(desc)
            elif term == '会議名':
                meeting_name = desc.replace('、', '')
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
            minutes.topic_ids = self.get_topic_ids(topics)
        speakers = content.xpath('./ul/li/a/text()').getall()
        speakers = deduplicate(speakers)
        if speakers:
            LOGGER.debug(f'scraped speakers={speakers}')
            minutes.speakers = speakers
            minutes.speaker_ids = self.get_speakers_ids(speakers)

        activity_list, url_list = self.build_activities_and_urls(content.xpath('./ul/li/a'), minutes, response.url)
        url = build_url(response.url, UrlTitle.SHINGI_TYUKEI, self.domain)
        url.to_id = minutes.id
        url_list.append(url)

        return minutes, activity_list, url_list
