import json
from collections import defaultdict
from datetime import datetime
from logging import getLogger

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import build_minutes, build_speech, extract_topics, build_url, UrlTitle, build_minutes_activity, \
    clean_speech
from politylink.elasticsearch.schema import MinutesText, SpeechText
from politylink.nlp.keyphrase import KeyPhraseExtractor

LOGGER = getLogger(__name__)


class MinutesSpider(SpiderTemplate):
    name = 'minutes'
    domain = 'ndl.go.jp'

    def __init__(self, start_date, end_date, pos=1, speech='false', text='false', keyphrase='true', overwrite='false',
                 *args, **kwargs):
        super(MinutesSpider, self).__init__(*args, **kwargs)
        self.start_date = start_date
        self.end_date = end_date
        self.collect_speech = speech == 'true'
        self.collect_text = text == 'true'
        self.collect_keyphrase = keyphrase == 'true'
        self.overwrite_url = overwrite == 'true'
        self.next_pos = int(pos)
        self.num_key_phrases = 3
        self.key_phrase_extractor = KeyPhraseExtractor()

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
        minutes_lst, minutes_text_lst, activity_lst, speech_lst, speech_text_lst, url_lst = \
            self.scrape_minutes_activities_speeches_urls(response_body)

        self.gql_client.bulk_merge(minutes_lst)
        LOGGER.info(f'merged {len(minutes_lst)} minutes')
        for minutes in minutes_lst:
            if self.overwrite_url:
                self.delete_old_urls(minutes.id, UrlTitle.HONBUN)
            self.link_minutes(minutes)

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
                self.es_client.bulk_index(speech_text_lst)
                LOGGER.info(f'merged {len(speech_text_lst)} speech texts')

        if self.collect_text:
            self.es_client.bulk_index(minutes_text_lst)
            LOGGER.info(f'merged {len(minutes_text_lst)} minutes texts')

        self.next_pos = response_body['nextRecordPosition']
        if self.next_pos is not None:
            yield response.follow(self.build_next_url(), callback=self.parse)

    def scrape_minutes_activities_speeches_urls(self, response_body):
        minutes_lst, minutes_text_lst, activity_lst, speech_lst, speech_text_lst, url_lst = [], [], [], [], [], []

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

            # pre-calculate speaker-member map until MemberFinder becomes fast (POL-285)
            speaker2member = dict()
            for speaker in set(map(lambda x: x['speaker'], meeting_rec['speechRecord'])):
                try:
                    speaker2member[speaker] = self.member_finder.find_one(speaker, exact_match=True)
                except Exception:
                    continue

            speaker2recs = defaultdict(list)
            full_text = ''
            for speech_rec in meeting_rec['speechRecord']:
                speaker = speech_rec['speaker']
                speaker2recs[speaker].append(speech_rec)
                cleaned_speech = clean_speech(speech_rec['speech'])
                full_text += cleaned_speech

                speech = build_speech(minutes.id, int(speech_rec['speechOrder']))
                speech.speaker_name = speaker
                if speaker in speaker2member:
                    speech.member_id = speaker2member[speaker].id  # only for link
                speech_lst.append(speech)
                speech_text_lst.append(SpeechText({
                    'id': speech.id,
                    'title': minutes.name,
                    'speaker': speaker,
                    'body': cleaned_speech,
                    'date': meeting_rec['date']
                }))

            for speaker, recs in speaker2recs.items():
                if speaker not in speaker2member:
                    continue  # ignore non member speaker
                member = speaker2member[speaker]
                speech = ''.join([rec['speech'] for rec in recs])
                activity = build_minutes_activity(member.id, minutes.id, minutes.start_date_time)
                if self.collect_keyphrase:
                    activity.keyphrases = self.key_phrase_extractor.extract(speech, self.num_key_phrases)
                url = build_url(recs[0]['speechURL'], UrlTitle.HONBUN, self.domain)
                url.to_id = activity.id
                activity_lst.append(activity)
                url_lst.append(url)

            minutes_text_lst.append(MinutesText({
                'id': minutes.id,
                'title': minutes.name,
                'body': full_text,
                'date': meeting_rec['date']
            }))

        return minutes_lst, minutes_text_lst, activity_lst, speech_lst, speech_text_lst, url_lst
