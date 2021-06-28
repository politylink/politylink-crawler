"""
GraphQLインスタンスを生成するためのbuildメソッドを定義する
"""

from enum import Enum
from logging import getLogger

from crawler.utils.common import contains_word
from politylink.elasticsearch.schema import BillText
from politylink.graphql.schema import Bill, Url, Minutes, Speech, Committee, News, Member, Diet, \
    Activity, BillAction, _Neo4jDateTimeInput, BillActionType
from politylink.idgen import idgen

LOGGER = getLogger(__name__)


class UrlTitle(str, Enum):
    GAIYOU = '概要'
    KEIKA = '経過'
    HONBUN = '本文'
    GIAN_ZYOUHOU = '議案情報'
    GAIYOU_PDF = '概要PDF'
    SINKYU_PDF = '新旧対照表PDF'
    IINKAI_KEIKA = '委員会経過'
    IINKAI_SITSUGI = '質疑項目'
    SHINGI_TYUKEI = '審議中継'
    PUBLIC_COMMENT = 'パブリックコメント'
    GIIN_ZYOUHOU = '議員情報'
    VRSDD = '国会審議映像検索システム'


class BillCategory(str, Enum):
    KAKUHOU = '閣法'
    SHUHOU = '衆法'
    SANHOU = '参法'


def build_bill(bill_category, diet_number, submission_number, bill_name):
    bill = Bill(None)
    assert isinstance(bill_category, BillCategory)
    bill.category = bill_category.name
    bill.name = bill_name
    bill.bill_number = f'第{diet_number}回国会{bill_category.value}第{submission_number}号'
    bill.id = idgen(bill)
    return bill


def build_url(href, title, domain):
    url = Url(None)
    url.url = href
    url.title = title.value if isinstance(title, UrlTitle) else title
    url.domain = domain
    url.id = idgen(url)
    return url


def build_news(href, publisher):
    news = News(None)
    news.url = href
    news.publisher = publisher
    news.id = idgen(news)
    return news


def build_minutes(committee_name, date_time):
    minutes = Minutes(None)
    minutes.name = committee_name
    minutes.start_date_time = to_neo4j_datetime(date_time)
    minutes.id = idgen(minutes)
    return minutes


def build_speech(minutes_id, order_in_minutes):
    speech = Speech(None)
    speech.minutes_id = minutes_id
    speech.order_in_minutes = order_in_minutes
    speech.id = idgen(speech)
    return speech


def build_committee(committee_name, house):
    committee = Committee(None)
    committee.name = committee_name
    committee.house = house
    committee.id = idgen(committee)
    return committee


def build_member(name):
    member = Member(None)
    member.name = name
    member.id = idgen(member)
    return member


def build_diet(number):
    diet = Diet(None)
    diet.number = number
    diet.id = idgen(diet)
    return diet


def build_minutes_activity(member_id, minutes_id, dt):
    activity = Activity(None)
    activity.member_id = member_id
    activity.minutes_id = minutes_id
    activity.datetime = to_neo4j_datetime(dt)
    activity.id = idgen(activity)
    return activity


def build_bill_activity(member_id, bill_id, dt):
    activity = Activity(None)
    activity.member_id = member_id
    activity.bill_id = bill_id
    activity.datetime = to_neo4j_datetime(dt)
    activity.id = idgen(activity)
    return activity


def build_bill_action(bill_id, minutes_id, bill_action_type):
    bill_action = BillAction(None)
    bill_action.bill_id = bill_id
    bill_action.minutes_id = minutes_id
    bill_action.type = bill_action_type
    bill_action.id = idgen(bill_action)
    return bill_action


def build_bill_text(bill_id, texts):
    supplement_idx = texts.index('附 則')
    reason_idx = texts.index('理 由')
    if supplement_idx > reason_idx:
        raise ValueError(f'supplement_idx({supplement_idx}) > reason_idx=({reason_idx})')
    bill_text = BillText(None)
    bill_text.id = bill_id
    bill_text.body = ''.join(texts[:supplement_idx])
    bill_text.supplement = ''.join(texts[supplement_idx + 1:reason_idx])
    bill_text.reason = ''.join(texts[reason_idx + 1:])
    return bill_text


def to_neo4j_datetime(dt):
    return _Neo4jDateTimeInput(year=dt.year, month=dt.month, day=dt.day,
                               hour=dt.hour, minute=dt.minute, second=dt.second)


def extract_bill_action_types(speech):
    action_lst = []
    if contains_word(speech, ['説明'], ['省略', '終わり', '既に聴取']):
        if contains_word(speech, ['修正案']):
            action_lst.append(BillActionType.AMENDMENT_EXPLANATION)
        elif contains_word(speech, ['附帯決議']):
            action_lst.append(BillActionType.SUPPLEMENTARY_EXPLANATION)
        elif contains_word(speech, ['趣旨の説明', '趣旨説明']):
            action_lst.append(BillActionType.BILL_EXPLANATION)
    if contains_word(speech, ['質疑']):
        action_lst.append(BillActionType.QUESTION)
    if contains_word(speech, ['討論']):
        action_lst.append(BillActionType.DEBATE)
    if contains_word(speech, ['採決']):
        action_lst.append(BillActionType.VOTE)
    if contains_word(speech, ['委員長の報告']):
        action_lst.append(BillActionType.REPORT)
    return action_lst
