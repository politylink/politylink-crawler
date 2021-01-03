import json
import re
from enum import Enum
from logging import getLogger
from urllib.parse import urljoin

from politylink.graphql.schema import Bill, Url, Minutes, Speech, _Neo4jDateTimeInput, Committee, News, Member, Diet, \
    Activity
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


def to_neo4j_datetime(dt):
    return _Neo4jDateTimeInput(year=dt.year, month=dt.month, day=dt.day,
                               hour=dt.hour, minute=dt.minute, second=dt.second)


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
        speech_lst.append(first_speech[end_idx:])  # start_idxより後の文章を取得

        # 改行を削除
        format_speech = ''
        for speech in speech_lst:
            if re.search(r'\r\n○', speech) is not None:
                speech = speech.replace('\r\n\u3000', '')
                speech = speech.replace('\r\n○', '\r\n\u3000')
            else:
                speech = speech.replace('\r\n\u3000\u3000', '')

            format_speech += speech
        return format_speech

    topics = []
    try:
        first_speech = format_first_speech(first_speech)
        topic_pattern = re.compile(r'\w+\S+(法律案|決議案|議決案|調査|使用(総)?調書|特別措置法案|予算|互選|件|決算書|計算書|請願|質疑)')
        for m in topic_pattern.finditer(first_speech):
            topic = m.group()
            topic = re.sub(r'^第?(一|二|三|四|五|六|七|八|九|十)+(　|、)?', '', topic)
            # remove brackets and text
            topic = re.sub(r'(\(|（)[^)]*(\)|）)', '', topic)
            # remove insufficient brackets and text
            topic = re.sub(r'(\(|（)[^)]*', '', topic)
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
