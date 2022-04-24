import json
from collections import defaultdict
from datetime import datetime
from logging import getLogger

import scrapy

from crawler.spiders import SpiderTemplate
from crawler.utils import build_minutes, build_speech, extract_topics, build_url, UrlTitle, build_minutes_activity, \
    clean_speech, extract_topic_ids, build_bill_action, is_moderator
from politylink.elasticsearch.schema import MinutesText, SpeechText
from politylink.nlp.keyphrase import KeyPhraseExtractor
from politylink.utils.bill import extract_bill_action_types

LOGGER = getLogger(__name__)


class MinutesSpider(SpiderTemplate):
    name = 'minutes'
    domain = 'ndl.go.jp'

    def __init__(self, start_date, end_date, pos=1, text='false', keyphrase='false', overwrite='false',
                 *args, **kwargs):
        super(MinutesSpider, self).__init__(*args, **kwargs)
        self.start_date = start_date
        self.end_date = end_date
        self.collect_text = text == 'true'
        self.collect_keyphrase = keyphrase == 'true'
        self.overwrite_url = overwrite == 'true'
        self.next_pos = int(pos)
        self.num_key_phrases = 3
        self.key_phrase_extractor = KeyPhraseExtractor()
        self.bill_id2names = {bill['id']: bill['name'] for bill in
                              self.gql_client.get_all_bills(fields=['id', 'name'])}

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
        minutes_lst, minutes_text_lst, activity_lst, speech_lst, speech_text_lst, bill_action_lst, url_lst = \
            self.scrape_minutes_activities_speeches_urls(response_body)

        self.gql_client.bulk_merge(minutes_lst)
        LOGGER.info(f'merged {len(minutes_lst)} minutes')
        for minutes in minutes_lst:
            if self.overwrite_url:
                self.delete_old_urls(minutes.id, UrlTitle.HONBUN)
            self.link_minutes(minutes)

        self.gql_client.bulk_merge(speech_lst)
        self.link_speeches(speech_lst)
        LOGGER.info(f'merged {len(speech_lst)} speeches')

        self.gql_client.bulk_merge(bill_action_lst)
        LOGGER.info(f'merged {len(bill_action_lst)} bill actions')
        if self.overwrite_url:
            for bill_action in bill_action_lst:
                self.delete_old_urls(bill_action.id, UrlTitle.HONBUN)
        self.link_bill_action(bill_action_lst)

        self.gql_client.bulk_merge(activity_lst)
        LOGGER.info(f'merged {len(activity_lst)} activities')
        if self.overwrite_url:
            for activity in activity_lst:
                self.delete_old_urls(activity.id, UrlTitle.HONBUN)
        self.link_activities(activity_lst)

        self.gql_client.bulk_merge(url_lst)
        LOGGER.info(f'merged {len(url_lst)} urls')
        self.link_urls(url_lst)

        if self.collect_text:
            self.es_client.bulk_index(minutes_text_lst)
            LOGGER.info(f'merged {len(minutes_text_lst)} minutes texts')
            self.es_client.bulk_index(speech_text_lst)
            LOGGER.info(f'merged {len(speech_text_lst)} speech texts')

        self.next_pos = response_body['nextRecordPosition']
        if self.next_pos is not None:
            yield response.follow(self.build_next_url(), callback=self.parse)

    def scrape_minutes_activities_speeches_urls(self, response_body):
        minutes_lst, minutes_text_lst, activity_lst, speech_lst, speech_text_lst, bill_action_lst, url_lst = [], [], [], [], [], [], []

        for meeting_rec in response_body['meetingRecord']:
            try:
                minutes = build_minutes(
                    meeting_rec['nameOfHouse'] + meeting_rec['nameOfMeeting'],
                    datetime.strptime(meeting_rec['date'], '%Y-%m-%d'))
                minutes.ndl_min_id = meeting_rec['issueID']
                minutes.ndl_url = meeting_rec['meetingURL']
                topics = extract_topics(meeting_rec['speechRecord'][0]['speech'])
                if topics:
                    minutes.topics = topics
                    minutes.topic_ids = self.get_topic_ids(topics, minutes.start_date_time)
                else:
                    LOGGER.warning(f'failed to extract topic for {minutes}')
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

            speaker2recs = defaultdict(list)  # for Activity
            moderator_recs = []  # for BillAction
            full_text = ''  # for MinutesText

            for speech_rec in meeting_rec['speechRecord'][1:]:  # skip 会議録情報
                speaker = speech_rec['speaker']
                speaker2recs[speaker].append(speech_rec)
                cleaned_speech = clean_speech(speech_rec['speech'])
                full_text += cleaned_speech
                speech = build_speech(minutes.id, int(speech_rec['speechOrder']))
                speech.ndl_url = speech_rec['speechURL']
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

                if is_moderator(speech_rec['speech']):
                    moderator_recs.append(speech_rec)

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

            bill_action_lst += self.scrape_bill_actions(moderator_recs, minutes, self.bill_id2names)

            minutes_text_lst.append(MinutesText({
                'id': minutes.id,
                'title': minutes.name,
                'body': full_text,
                'date': meeting_rec['date']
            }))

        return minutes_lst, minutes_text_lst, activity_lst, speech_lst, speech_text_lst, bill_action_lst, url_lst

    @staticmethod
    def scrape_bill_actions(moderator_recs, minutes, bill_id2names):
        bill_action_lst = []

        if not hasattr(minutes, 'topics'):
            return bill_action_lst

        minutes_bill_id2names = {}
        for topic_id in minutes.topic_ids:
            if topic_id in bill_id2names.keys():
                minutes_bill_id2names[topic_id] = bill_id2names[topic_id]

        current_topic_ids = list()
        prev_bill_action_types = defaultdict(set)  # key: bill_id, value: set of action types
        for speech_rec in moderator_recs:
            speech = build_speech(minutes.id, int(speech_rec['speechOrder']))
            if any(topic in speech_rec['speech'] for topic in
                   minutes.topics + list(minutes_bill_id2names.values())):
                current_topic_ids = extract_topic_ids(speech_rec['speech'], minutes_bill_id2names)
            bill_action_types = extract_bill_action_types(speech_rec['speech'])
            if current_topic_ids and bill_action_types:
                for current_topic_id in current_topic_ids:
                    for bill_action_type in bill_action_types:
                        if bill_action_type not in prev_bill_action_types[current_topic_id]:
                            bill_action = build_bill_action(current_topic_id, minutes.id, bill_action_type)
                            bill_action.speech_id = speech.id  # only for link
                            bill_action_lst.append(bill_action)
                            prev_bill_action_types[current_topic_id].add(bill_action_type)
        return bill_action_lst
