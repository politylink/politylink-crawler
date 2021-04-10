import json
from collections import defaultdict
from datetime import datetime
from logging import getLogger

import scrapy
from crawler.spiders import SpiderTemplate
from crawler.utils import build_minutes, build_speech, extract_topics, build_url, UrlTitle, build_minutes_activity, \
    clean_speech, extract_discussed_bill, extract_billstatus, clean_report, build_billstatus
from politylink.elasticsearch.client import ElasticsearchClient
from politylink.elasticsearch.schema import MinutesText
from politylink.nlp.keyphrase import KeyPhraseExtractor

LOGGER = getLogger(__name__)


class MinutesSpider(SpiderTemplate):
    name = 'minutes'
    domain = 'ndl.go.jp'

    def __init__(self, start_date, end_date, speech='false', text='false', overwrite='false',
                 elasticsearch='http://localhost:9200', *args, **kwargs):
        super(MinutesSpider, self).__init__(*args, **kwargs)
        self.start_date = start_date
        self.end_date = end_date
        self.collect_speech = speech == 'true'
        self.collect_text = text == 'true'
        self.overwrite_url = overwrite == 'true'
        self.next_pos = 1
        self.num_key_phrases = 3
        self.key_phrase_extractor = KeyPhraseExtractor()
        self.es_client = ElasticsearchClient(url=elasticsearch)

    def build_next_url(self):
        return 'https://kokkai.ndl.go.jp/api/meeting?from={0}&until={1}&startRecord={2}&maximumRecords=5&recordPacking=JSON'.format(
            self.start_date, self.end_date, self.next_pos)

    def start_requests(self):
        yield scrapy.Request(self.build_next_url(), self.parse)

    def parse(self, response):
        """
        Minutes, Activity, Speech, UrlをGraphQLに保存する
        """

        LOGGER.info(f'requested {response.url}')
        response_body = json.loads(response.body)
        minutes_lst, minutes_text_lst, activity_lst, speech_lst, url_lst = \
            self.scrape_minutes_activities_speeches_urls(response_body)

        self.gql_client.bulk_merge(minutes_lst)
        LOGGER.info(f'merged {len(minutes_lst)} minutes')
        for minutes in minutes_lst:
            if self.overwrite_url:
                self.delete_old_urls(minutes.id, UrlTitle.HONBUN)
            self.link_minutes(minutes)

        billstatus_lst = self.scrape_billstatus(response_body)
        self.gql_client.bulk_merge(billstatus_lst)
        LOGGER.info(f'merged {len(billstatus_lst)} bill status')
        self.link_billstatus(billstatus_lst)

        self.gql_client.bulk_merge(activity_lst)
        LOGGER.info(f'merged {len(activity_lst)} activities')
        if self.overwrite_url:
            for activity in activity_lst:
                self.delete_old_urls(activity.id, UrlTitle.HONBUN)
        self.link_activities(activity_lst)

        self.gql_client.bulk_merge(url_lst)
        LOGGER.info(f'merged {len(url_lst)} urls')
        self.link_urls(url_lst)

        if self.collect_speech:
            self.gql_client.bulk_merge(speech_lst)
            self.link_speeches(speech_lst)
            LOGGER.info(f'merged {len(speech_lst)} speeches')

        if self.collect_text:
            for minutes_text in minutes_text_lst:
                self.es_client.index(minutes_text)
            LOGGER.info(f'merged {len(minutes_text_lst)} minutes texts')

        self.next_pos = response_body['nextRecordPosition']
        if self.next_pos is not None:
            yield response.follow(self.build_next_url(), callback=self.parse)

    def scrape_minutes_activities_speeches_urls(self, response_body):
        minutes_lst, minutes_text_lst, activity_lst, speech_lst, url_lst = [], [], [], [], []

        for meeting_rec in response_body['meetingRecord']:
            try:
                minutes = build_minutes(
                    meeting_rec['nameOfHouse'] + meeting_rec['nameOfMeeting'],
                    datetime.strptime(meeting_rec['date'], '%Y-%m-%d'))
                minutes.ndl_min_id = meeting_rec['issueID']
                topics = extract_topics(meeting_rec['speechRecord'][0]['speech'])
                if topics:
                    minutes.topics = topics
                    minutes.topic_ids = self.get_topic_ids(topics)
            except ValueError as e:
                LOGGER.warning(f'failed to parse minutes: {e}')
                continue
            minutes_lst.append(minutes)

            url = build_url(meeting_rec['meetingURL'], UrlTitle.HONBUN, self.domain)
            url.to_id = minutes.id
            url_lst.append(url)

            speaker2recs = defaultdict(list)
            full_text = ''
            for speech_rec in meeting_rec['speechRecord']:
                speaker = speech_rec['speaker']
                speaker2recs[speaker].append(speech_rec)
                full_text += clean_speech(speech_rec['speech'])
                speech = build_speech(minutes.id, int(speech_rec['speechOrder']))
                speech.speaker_name = speaker
                speech_lst.append(speech)

            for speaker, recs in speaker2recs.items():
                try:
                    member = self.member_finder.find_one(speaker)
                except Exception:
                    pass
                else:
                    speech = ''.join([rec['speech'] for rec in recs])
                    activity = build_minutes_activity(member.id, minutes.id, minutes.start_date_time)
                    activity.keyphrases = self.key_phrase_extractor.extract(speech, self.num_key_phrases)
                    url = build_url(recs[0]['speechURL'], UrlTitle.HONBUN, self.domain)
                    url.to_id = activity.id
                    activity_lst.append(activity)
                    url_lst.append(url)

            minutes_text_lst.append(MinutesText({
                'id': minutes.id,
                'title': minutes.name,
                'body': full_text
            }))

        return minutes_lst, minutes_text_lst, activity_lst, speech_lst, url_lst

    def scrape_billstatus(self, response_body):
        billstatus_lst = []

        for meeting_rec in response_body['meetingRecord']:
            minutes = self.get_minutes(meeting_rec['issueID'])
            bills = minutes.discussed_bills
            bill_name2id = {}
            for bill in bills:
                bill_name2id[bill.name] = bill.id

            bill2status = defaultdict(set)
            bill2speech = defaultdict(set)
            discussed_bill = None
            is_report = False
            for speech_rec in meeting_rec['speechRecord']:
                if is_report and (discussed_bill is not None):
                    bill2speech[discussed_bill] = clean_report(speech_rec['speech'])
                    is_report = False

                if speech_rec['speakerPosition'] == '議長':
                    discussed_bill = extract_discussed_bill(speech_rec['speech'], list(bill_name2id.keys()),
                                                            discussed_bill)
                    if discussed_bill is not None:
                        billstatus = extract_billstatus(speech_rec['speech'])
                        if len(billstatus) > 0:
                            bill2status[discussed_bill].update(billstatus)
                        if '委員長報告' in billstatus:
                            is_report = True

            for bill_name, bill_id in bill_name2id.items():
                if bill_name in bill2status.keys():
                    billstatus = build_billstatus(bill_id, minutes.id, bill2status[bill_name])
                    if bill_name in bill2speech.keys():
                        billstatus.speech = bill2speech[bill_name]
                    billstatus_lst.append(billstatus)

        return billstatus_lst
