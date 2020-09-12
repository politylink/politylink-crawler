import json
from datetime import datetime
from logging import getLogger

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import build_minutes, build_speech, extract_topics, build_url, UrlTitle
from politylink.graphql.schema import Minutes, Url

LOGGER = getLogger(__name__)


class MinutesSpider(SpiderTemplate):
    name = 'minutes'
    domain = 'ndl.go.jp'

    def __init__(self, start_date, end_date, *args, **kwargs):
        super(MinutesSpider, self).__init__(*args, **kwargs)
        self.start_date = start_date
        self.end_date = end_date
        self.next_pos = 1

    def build_next_url(self):
        return 'https://kokkai.ndl.go.jp/api/meeting?from={0}&until={1}&startRecord={2}&maximumRecords=5&recordPacking=JSON'.format(
            self.start_date, self.end_date, self.next_pos)

    def start_requests(self):
        yield scrapy.Request(self.build_next_url(), self.parse)

    def parse(self, response):
        """
        Minutes, URL, SpeechをGraphQLに保存する
        """

        LOGGER.info(f'requested {response.url}')
        response_body = json.loads(response.body)
        minutes_lst, url_lst, speech_lst = self.scrape_minutes_and_speeches(response_body)

        for minutes in minutes_lst:
            assert isinstance(minutes, Minutes)
            self.client.exec_merge_minutes(minutes)
            LOGGER.debug(f'merged {minutes.id}')
            for topic in minutes.topics:
                bills = self.bill_finder.find(topic)
                LOGGER.debug(f'found {len(bills)} bills for topic={topic}')
                for bill in bills:
                    self.client.exec_merge_minutes_discussed_bills(minutes.id, bill.id)
        LOGGER.info(f'merged {len(minutes_lst)} minutes')

        for url in url_lst:
            assert isinstance(url, Url)
            self.client.exec_merge_url(url)
            self.client.exec_merge_url_referred_minutes(url.id, url.meta['minutes_id'])
            LOGGER.debug(f'merged {url.id}')
        LOGGER.info(f'merged {len(url_lst)} urls')

        # ToDo: enable speech collection after implementing batch GraphQL method (POL-36)
        # for speech in speech_lst:
        #     assert isinstance(speech, Speech)
        #     self.client.exec_merge_speech(speech)
        #     self.client.exec_merge_speech_belonged_to_minutes(speech.id, speech.meta['minutes_id'])
        #     LOGGER.debug(f'merged {speech.id}')
        # LOGGER.info(f'merged {len(speech_lst)} speeches')

        self.next_pos = response_body['nextRecordPosition']
        if self.next_pos is not None:
            yield response.follow(self.build_next_url(), callback=self.parse)

    @staticmethod
    def scrape_minutes_and_speeches(response_body):
        minutes_lst, url_lst, speech_lst = [], [], []

        for meeting_rec in response_body['meetingRecord']:
            try:
                minutes = build_minutes(
                    int(meeting_rec['session']),
                    meeting_rec['nameOfHouse'],
                    meeting_rec['nameOfMeeting'],
                    int(meeting_rec['issue'][1:-1]),  # ToDo: fix failure of adhoc removal of 第 and 号
                    extract_topics(meeting_rec['speechRecord'][0]['speech']),
                    meeting_rec['meetingURL'],
                    datetime.strptime(meeting_rec['date'], '%Y-%m-%d')
                )
            except ValueError as e:
                LOGGER.warning(f'failed to parse minutes: {e}')
                continue
            minutes_lst.append(minutes)

            url = build_url(meeting_rec['meetingURL'], UrlTitle.HONBUN, MinutesSpider.domain)
            url.meta = {'minutes_id': minutes.id}
            url_lst.append(url)

            for speech_rec in meeting_rec['speechRecord']:
                speech = build_speech(
                    minutes.name,
                    speech_rec['speaker'],
                    int(speech_rec['speechOrder'])
                )
                speech.meta = {'minutes_id': minutes.id}
                speech_lst.append(speech)

        return minutes_lst, url_lst, speech_lst
