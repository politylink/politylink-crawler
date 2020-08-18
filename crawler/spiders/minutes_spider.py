import json
from datetime import datetime
from logging import getLogger

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import build_minutes, build_speech, extract_topics
from politylink.graphql.schema import Minutes

LOGGER = getLogger(__name__)


class MinutesSpider(SpiderTemplate):
    name = 'minutes'
    domain = 'kokkai.ndl.go.jp'

    def __init__(self, start_date, end_date, *args, **kwargs):
        super(MinutesSpider, self).__init__(*args, **kwargs)
        self.start_date = start_date
        self.end_date = end_date
        self.next_pos = 1

    def build_next_url(self):
        return 'https://kokkai.ndl.go.jp/api/meeting?from={0}&until={1}&startRecord={2}&maximumRecords=5&recordPacking=JSON'.format(
            self.start_date, self.end_date, self.next_pos)

    def start_requests(self):
        url = self.build_next_url()
        yield scrapy.Request(url, self.parse)

    def parse(self, response):
        """
        Minutes, SpeechをGraphQLに保存する
        """

        LOGGER.info(f'requested {response.url}')
        response_body = json.loads(response.body)
        minutes_lst, speech_lst = self.scrape_minutes_and_speeches(response_body)

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

        # ToDo: enable speech collection after implementing batch GraphQL method
        # for speech in speech_lst:
        #     assert isinstance(speech, Speech)
        #     self.client.exec_merge_speech(speech)
        #     self.client.exec_merge_speech_belonged_to_minutes(speech.id, speech.meta['minutes_id'])
        #     LOGGER.debug(f'merged {speech.id}')
        # LOGGER.info(f'merged {len(speech_lst)} speeches')

        self.next_pos = response_body['nextRecordPosition']
        if self.next_pos is not None:
            url = self.build_next_url()
            yield response.follow(url, callback=self.parse)

    @staticmethod
    def scrape_minutes_and_speeches(response_body):
        minutes_lst, speech_lst = [], []

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

            for speech_rec in meeting_rec['speechRecord']:
                speech = build_speech(
                    minutes.name,
                    speech_rec['speaker'],
                    int(speech_rec['speechOrder'])
                )
                speech.meta = {'minutes_id': minutes.id}
                speech_lst.append(speech)

        return minutes_lst, speech_lst
