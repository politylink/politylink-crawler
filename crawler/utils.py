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


def extract_topics(first_speech):
    def format_first_speech(first_speech):
        start_idx, end_idx = re.search(r'○?本日の会議に付した案件|○?本日の公聴会で意見を聞いた案件', first_speech).span()
        speech_lst = []

        # 議事日程を取得
        # 議題が記載されている以前の文章を除くためのindex
        schedule_idx = re.search(r'議事日程', first_speech)
        if schedule_idx is not None:
            speech_lst.append(first_speech[schedule_idx.end():start_idx])

        # 明示的に記載されて案件を取得
        speech_lst.append(first_speech[end_idx:])  # end_idxより後の文章を取得

        # 改行を削除
        format_speech = ''
        for speech in speech_lst:
            if re.search(r'\r\n○', speech) is not None:
                speech = speech.replace('\r\n\u3000', '')  # トピック名の途中の\r\n\u3000を削除
                speech = speech.replace('\r\n○', '\u3000')  # \r\n○はトピック名の区切りとして\u3000に置換
            else:
                speech = speech.replace('\r\n\u3000\u3000', '')  # \r\n○がない場合は、\r\n\u3000はトピック名の区切りなので削除しない

            speech = speech.replace('、', '\u3000')  # 読点はトピック名の区切りとして\u3000に置換
            speech = speech.replace('）及び', '）\u3000')  # "）及び"はトピック名の区切りとして"及び"を削除し\u3000に置換

            format_speech += speech
        return format_speech

    topics = []
    try:
        first_speech = format_first_speech(first_speech)
        topic_pattern = re.compile(r'\w+\S+(法律案|法案|決議案|議決案|調査|使用(総)?調書|特別措置法案|予算|互選|件|決算書|計算書|請願|質疑)(（.+?）)?')
        for m in topic_pattern.finditer(first_speech):
            topic = m.group()
            topic = re.sub(r'^第?(一|二|三|四|五|六|七|八|九|十)+(　|、)?', '', topic)
            # remove start and end spaces
            topic = topic.strip()
            if topic not in topics:
                topics.append(topic)
    except Exception:
        LOGGER.exception(f'failed to parse topics from {first_speech}')
    return topics


def clean_topic(topic):
    topic = topic.strip()
    if topic.endswith('ため'):
        return topic[:-2]
    return topic


def extract_topic_ids(speech, bill_id2names):
    topic_ids = []
    for bill_id, bill_name in bill_id2names.items():
        if bill_name in speech:
            topic_ids.append(bill_id)
    if len(topic_ids) > 1:
        LOGGER.debug(f'found multiple topics: speech={speech}, topic_ids={topic_ids}')
    return topic_ids


def extract_bill_action_types(speech):
    def speech_contains(allow_list, block_list=None):
        if block_list is None:
            block_list = []
        has_allow_word = any(w in speech for w in allow_list)
        has_block_word = any(w in speech for w in block_list)
        return has_allow_word and not has_block_word

    action_lst = []
    if speech_contains(['説明'], ['省略', '終わり', '既に聴取']):
        if speech_contains(['修正案']):
            action_lst.append(BillActionType.AMENDMENT_EXPLANATION)
        elif speech_contains(['附帯決議']):
            action_lst.append(BillActionType.SUPPLEMENTARY_EXPLANATION)
        elif speech_contains(['趣旨の説明', '趣旨説明']):
            action_lst.append(BillActionType.BILL_EXPLANATION)
    if speech_contains(['質疑']):
        action_lst.append(BillActionType.QUESTION)
    if speech_contains(['討論']):
        action_lst.append(BillActionType.DEBATE)
    if speech_contains(['採決']):
        action_lst.append(BillActionType.VOTE)
    if speech_contains(['委員長の報告']):
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
