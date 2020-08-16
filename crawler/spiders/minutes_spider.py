from logging import getLogger

import json
import re
import scrapy
from politylink.graphql.client import GraphQLClient
from politylink.graphql.schema import Minutes, Speech
from crawler.utils import build_minutes, build_speech, extract_topics


LOGGER = getLogger(__name__)


MAX_NUM = 5
OUTPUT_FORMAT = 'json'


class MinutesSpider(scrapy.Spider):
    name = 'minutes'
    domain = 'kokkai.ndl.go.jp'
    end_point = 'https://kokkai.ndl.go.jp/api/meeting?from={0}&until={1}&startRecord={2}&maximumRecords={3}&recordPacking={4}'
    full2half = str.maketrans({'０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
                               '５': '5', '６': '6', '７': '7', '８': '8', '９': '9'})
    topic_patterns = [re.compile(r'第(一|二|三|四|五|六|七|八|九|十)+\s\S+'),
                      re.compile(r'\w+\S+(法律案|決議案|議決案|調査|特別措置法案|予算|互選|件|決算書|計算書|請願)(\（.+\）)?')]

    def __init__(self, start_date, end_date, *args, **kwargs):
        super(MinutesSpider, self).__init__(*args, **kwargs)
        self.client = GraphQLClient()
        self.start_date = start_date
        self.end_date = end_date
        self.next_pos = 1

    def start_requests(self):
        url = self.end_point.format(self.start_date, self.end_date, 1, MAX_NUM, OUTPUT_FORMAT)
        yield scrapy.Request(url, self.parse)

    def parse(self, response):
        """
        Minutes, SpeechをGraphQLに保存する
        """

        LOGGER.info(f'requested {response.url}')
        response_body = json.loads(response.body)
        meeting_lst = response_body['meetingRecord']
        minutes, speeches = self.scrape_minutes_and_speeches(meeting_lst)

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

        # set next start position of record
        self.next_pos = response_body['nextRecordPosition']

        if self.next_pos is not None:
            url = self.end_point.format(self.start_date, self.end_date, self.next_pos, MAX_NUM, OUTPUT_FORMAT)
            yield response.follow(url, callback=self.parse)

    def scrape_minutes_and_speeches(self, meeting_lst):
        """
        """
        minutes_lst, speech_lst = [], []

        for meeting in meeting_lst:
            minutes_name = '第{0}回{1}{2}{3}'.format(
                int(meeting['session']), meeting['nameOfHouse'],
                meeting['nameOfMeeting'], meeting['issue'].translate(self.full2half))

            speeches = meeting['speechRecord']
            first_speech = speeches[0]['speech']
            topics = extract_topics(self.topic_patterns, first_speech)
            minutes = build_minutes(minutes_name, topics)
            minutes_lst.append(minutes)

            for current_speech in speeches:
                speaker_name = current_speech['speaker']
                order = current_speech['speechOrder']
                speech_name = '{0}{1}'.format(minutes_name, int(order))
                speech = build_speech(speech_name, speaker_name, order)
                speech.meta = {'minutes_id': minutes.id}
                speech_lst.append(speech)

        return minutes_lst, speech_lst
