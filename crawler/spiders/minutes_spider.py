import json
from datetime import datetime
from logging import getLogger

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import build_minutes, build_speech, extract_topics, build_url, UrlTitle

LOGGER = getLogger(__name__)


class MinutesSpider(SpiderTemplate):
    name = 'minutes'
    domain = 'ndl.go.jp'

    def __init__(self, start_date, end_date, speech='false', *args, **kwargs):
        super(MinutesSpider, self).__init__(*args, **kwargs)
        self.start_date = start_date
        self.end_date = end_date
        self.collect_speech = speech == 'true'
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

        self.gql_client.bulk_merge(minutes_lst + url_lst)
        LOGGER.info(f'merged {len(minutes_lst)} minutes, {len(url_lst)} urls')
        if self.collect_speech:
            self.gql_client.bulk_merge(speech_lst)
            LOGGER.info(f'merged {len(speech_lst)} speeches')

        from_ids, to_ids = [], []
        for minutes in minutes_lst:
            for topic in minutes.topics:
                bills = self.bill_finder.find(topic)
                LOGGER.debug(f'found {len(bills)} bills for topic={topic}')
                for bill in bills:
                    from_ids.append(minutes.id)
                    to_ids.append(bill.id)
            try:
                committee = self.committee_finder.find_one(minutes.name)
                from_ids.append(minutes.id)
                to_ids.append(committee.id)
            except ValueError as e:
                LOGGER.warning(e)
        for url in url_lst:
            from_ids.append(url.id)
            to_ids.append(url.meta['minutes_id'])
        if self.collect_speech:
            for speech in speech_lst:
                from_ids.append(speech.id)
                to_ids.append(speech.minutes_id)
        self.gql_client.bulk_link(from_ids, to_ids)
        LOGGER.info(f'merged {len(from_ids)} relationships')

        self.next_pos = response_body['nextRecordPosition']
        if self.next_pos is not None:
            yield response.follow(self.build_next_url(), callback=self.parse)

    @staticmethod
    def scrape_minutes_and_speeches(response_body):
        minutes_lst, url_lst, speech_lst = [], [], []

        for meeting_rec in response_body['meetingRecord']:
            try:
                minutes = build_minutes(
                    meeting_rec['nameOfHouse'],
                    meeting_rec['nameOfMeeting'],
                    datetime.strptime(meeting_rec['date'], '%Y-%m-%d'))
                minutes.topics = extract_topics(meeting_rec['speechRecord'][0]['speech'])
            except ValueError as e:
                LOGGER.warning(f'failed to parse minutes: {e}')
                continue
            minutes_lst.append(minutes)

            url = build_url(meeting_rec['meetingURL'], UrlTitle.HONBUN, MinutesSpider.domain)
            url.meta = {'minutes_id': minutes.id}
            url_lst.append(url)

            for speech_rec in meeting_rec['speechRecord']:
                speech = build_speech(
                    minutes.id,
                    int(speech_rec['speechOrder']))
                speech.speaker_name = speech_rec['speaker']
                speech_lst.append(speech)

        return minutes_lst, url_lst, speech_lst
