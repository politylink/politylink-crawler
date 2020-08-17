import json
from logging import getLogger

import scrapy

from crawler.utils import build_minutes, build_speech, extract_topics
from politylink.graphql.client import GraphQLClient
from politylink.graphql.schema import Minutes, Speech

LOGGER = getLogger(__name__)


class MinutesSpider(scrapy.Spider):
    name = 'minutes'
    domain = 'kokkai.ndl.go.jp'

    def __init__(self, start_date, end_date, *args, **kwargs):
        super(MinutesSpider, self).__init__(*args, **kwargs)
        self.client = GraphQLClient()
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
        minutes, speeches = self.scrape_minutes_and_speeches(response_body)

        for current_minutes in minutes:
            assert isinstance(current_minutes, Minutes)
            self.client.exec_merge_minutes(current_minutes)
            LOGGER.debug(f'merged {current_minutes.id}')
        LOGGER.info(f'merged {len(minutes)} minutes')

        for speech in speeches:
            assert isinstance(speech, Speech)
            self.client.exec_merge_speech(speech)
            self.client.exec_merge_speech_belonged_to_minutes(speech.id, speech.meta['minutes_id'])
            LOGGER.debug(f'merged {speech.id}')
        LOGGER.info(f'merged {len(speeches)} speeches')

        self.next_pos = response_body['nextRecordPosition']
        if self.next_pos is not None:
            url = self.build_next_url()
            yield response.follow(url, callback=self.parse)

    @staticmethod
    def scrape_minutes_and_speeches(response_body):
        minutes_lst, speech_lst = [], []

        for meeting_rec in response_body['meetingRecord']:
            minutes = build_minutes(
                int(meeting_rec['session']),
                meeting_rec['nameOfHouse'],
                meeting_rec['nameOfMeeting'],
                int(meeting_rec['issue'][1:-1]),  # drop 第 and 号
                extract_topics(meeting_rec['speechRecord'][0]['speech'])
            )
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
