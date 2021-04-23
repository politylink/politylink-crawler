from datetime import datetime

from crawler.spiders.minutes_spider import MinutesSpider
from crawler.utils import build_minutes
from politylink.graphql.schema import BillActionType


class TestMinutesSpider:
    def test_scrape_bill_actions(self):
        speeches = [
            'これより会議を始めます',
            '法律案Xを議題とします',
            '質疑に入ります',
            '法律案Yを議題とします',
            '採決に入ります',
            '法律案Zを議題とします',
            '趣旨説明お願いします',
            '採決に入ります',
            'お疲れ様でした',
        ]
        speech_recs = list(map(lambda x: self.build_rec(x), speeches))
        minutes = build_minutes('猫ちゃん会議', datetime(2021, 1, 1))
        minutes.topics = ['法律案X', '法律案Y', '法律案Z']
        minutes.topic_ids = ['Bill:X', 'Bill:Z']
        bill_id2name = {'Bill:X': '法律案X', 'Bill:Z': '法律案Z'}

        bill_actions = MinutesSpider.scrape_bill_actions(speech_recs, minutes, bill_id2name)
        assert len(bill_actions) == 3
        self.assert_bill_action('Bill:X', BillActionType.QUESTION, bill_actions[0])
        self.assert_bill_action('Bill:Z', BillActionType.BILL_EXPLANATION, bill_actions[1])
        self.assert_bill_action('Bill:Z', BillActionType.VOTE, bill_actions[2])

    @staticmethod
    def assert_bill_action(bill_id, bill_action_type, bill_action):
        assert bill_id == bill_action.bill_id
        assert bill_action_type == bill_action.type

    @staticmethod
    def build_rec(speech):
        return {'speech': speech, 'speechURL': 'https://google.com'}
