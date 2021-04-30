from datetime import datetime

from crawler.spiders.minutes_spider import MinutesSpider
from crawler.utils import build_minutes, build_speech
from politylink.graphql.schema import BillActionType


class TestMinutesSpider:
    def test_scrape_bill_actions(self):
        speeches = [
            'これより会議を始めます',
            '法律案Xを議題とします',
            '質疑に入ります',  # 2
            '法律案Xの質疑を終わります',
            '法律案Yを議題とします',
            '採決に入ります',
            '法律案Zを議題とします',
            '趣旨説明お願いします',  # 7
            '採決に入ります',  # 8
            'お疲れ様でした',
        ]
        speech_recs = [self.build_rec(speech, i) for i, speech in enumerate(speeches)]
        minutes = build_minutes('猫ちゃん会議', datetime(2021, 1, 1))
        minutes.topics = ['法律案X', '法律案Y', '法律案Z']
        minutes.topic_ids = ['Bill:X', 'Bill:Z']
        bill_id2name = {'Bill:X': '法律案X', 'Bill:Z': '法律案Z'}

        bill_actions = MinutesSpider.scrape_bill_actions(speech_recs, minutes, bill_id2name)
        assert len(bill_actions) == 3
        self.assert_bill_action('Bill:X', minutes.id, 2, BillActionType.QUESTION, bill_actions[0])
        self.assert_bill_action('Bill:Z', minutes.id, 7, BillActionType.BILL_EXPLANATION, bill_actions[1])
        self.assert_bill_action('Bill:Z', minutes.id, 8, BillActionType.VOTE, bill_actions[2])

    @staticmethod
    def assert_bill_action(bill_id, minutes_id, speech_order, bill_action_type, bill_action):
        assert bill_id == bill_action.bill_id
        assert minutes_id == bill_action.minutes_id
        assert build_speech(minutes_id, speech_order).id == bill_action.speech_id
        assert bill_action_type == bill_action.type

    @staticmethod
    def build_rec(speech, speech_order):
        return {
            'speech': speech,
            'speechOrder': speech_order,
            'speechURL': 'https://google.com'
        }
