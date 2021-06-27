import json
import re
import unicodedata
from enum import Enum
from logging import getLogger
from urllib.parse import urljoin

from politylink.elasticsearch.schema import BillText
from politylink.graphql.schema import Bill, Url, Minutes, Speech, _Neo4jDateTimeInput, Committee, News, Member, Diet, \
    Activity, BillAction, BillActionType
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


def extract_text(cell):
    return cell.xpath('.//text()').get()


def extract_full_href_or_none(cell, root_url):
    selector = cell.xpath('.//a/@href')
    if len(selector) > 0:
        return urljoin(root_url, selector.get())
    return None


def extract_full_href_list(selector, root_url):
    urls = []
    for element in selector:
        maybe_url = extract_full_href_or_none(element, root_url)
        if maybe_url:
            urls.append(maybe_url)
    return urls


def extract_json_ld_or_none(response):
    maybe_text = response.xpath('//script[@type="application/ld+json"]//text()').get()
    if not maybe_text:
        return None
    return json.loads(maybe_text)


def extract_thumbnail_or_none(ld_json):
    if 'image' not in ld_json or 'url' not in ld_json['image']:
        return None
    return ld_json['image']['url']


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


def to_neo4j_datetime(dt):
    return _Neo4jDateTimeInput(year=dt.year, month=dt.month, day=dt.day,
                               hour=dt.hour, minute=dt.minute, second=dt.second)


def to_date_str(dt):
    return '{:02d}-{:02d}-{:02d}'.format(dt.year, dt.month, dt.day)


def contains_word(text, allow_list=None, block_list=None):
    allow_list = allow_list or list()
    block_list = block_list or list()
    has_allow_word = any(w in text for w in allow_list)
    has_block_word = any(w in text for w in block_list)
    return has_allow_word and not has_block_word


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


def clean_speech(speech):
    return ''.join(speech.split()[1:])  # drop speaker name (first item)


def is_moderator(speech):
    speaker = speech.split()[0]
    moderators = ['議長', '委員長', '会長', '主査']
    return any([m in speaker for m in moderators])


def strip_join(str_list, sep=''):
    return sep.join(map(lambda x: x.strip(), str_list))


def validate_item_or_raise(obj, fields):
    for field in fields:
        if not hasattr(obj, field) or not getattr(obj, field):
            raise ValueError(f'{type(obj)} does not have required field: {field}')


def validate_news_or_raise(news):
    validate_item_or_raise(news, ['id', 'title', 'published_at'])


def validate_news_text_or_raise(news):
    validate_item_or_raise(news, ['id', 'title', 'body'])


def parse_name_str(name_str):
    """
    :input: "逢沢　一郎（あいさわ　いちろう）" or "蓮舫（れんほう）"
    :return: (first_name, last_name, first_name_hira, last_name_hira)
    """
    name_str = name_str.strip()
    pattern = r'([^（）]+)（([^（）]+)）'
    if not re.fullmatch(pattern, name_str):
        raise ValueError(f'invalid name_str="{name_str}"')
    parts = re.split('[ |　|（|）]', name_str)
    if len(parts) == 3:
        return parts[0], '', parts[1], ''
    elif len(parts) == 5:
        return parts[1], parts[0], parts[3], parts[2]
    else:
        raise ValueError(f'invalid split result: name_str={name_str}, parts={parts}')


def extract_bill_number_or_none(text):
    def kansuji2arabic(s):
        kansuji = '一二三四五六七八九'
        kansuji_digit = '十百千'
        s_arabic = [s[0]]
        for i in range(1, len(s)):
            if s[i] in kansuji:
                s_arabic.append(str(int(unicodedata.numeric(s[i]))))
            elif s[i] in kansuji_digit:
                if s[i - 1] not in kansuji and s[i - 1] not in kansuji_digit:
                    s_arabic.append('1')
            else:
                s_arabic.append(s[i])
        return ''.join(s_arabic)

    pattern = r'第?([0-9]+)回?(国会)?(閣|衆|参|)法?第?([0-9]+)号?'
    match = re.search(pattern, kansuji2arabic(text))
    if not match:
        return None
    bill_number = '第{}回国会{}法第{}号'.format(match.group(1), match.group(3), match.group(4))
    return bill_number


def extract_category_or_none(text):
    pattern = r'(内閣|衆議院|参議院)提出|(閣法|衆法|参法)'
    match = re.search(pattern, text)
    if not match:
        return None
    if match.group() == '内閣提出' or match.group() == '閣法':
        return 'KAKUHOU'
    elif match.group() == '衆議院提出' or match.group() == '衆法':
        return 'SHUHOU'
    elif match.group() == '参議院提出' or match.group() == '参法':
        return 'SANHOU'
    else:
        return None


def deduplicate(items):
    return list(dict.fromkeys(items))


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


def get_offset(s):
    for i, c in enumerate(s):
        if c not in {' ', '　'}:
            return i
    return -1
