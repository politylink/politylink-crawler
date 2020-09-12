import re
from enum import Enum
from urllib.parse import urljoin

from politylink.graphql.schema import Bill, Url, Minutes, Speech, _Neo4jDateTimeInput
from politylink.idgen import idgen


class UrlTitle(str, Enum):
    GAIYOU = '概要'
    KEIKA = '経過'
    HONBUN = '本文'
    GIAN_ZYOUHOU = '議案情報'
    GAIYOU_PDF = '概要PDF'
    SINKYU_PDF = '新旧対照表PDF'
    IINKAI_KEIKA = '委員会経過'
    IINKAI_SITSUGI = '質疑項目'


def extract_text(cell):
    return cell.xpath('.//text()').get()


def extract_full_href_or_none(cell, root_url):
    selector = cell.xpath('.//a/@href')
    if len(selector) == 1:
        return urljoin(root_url, selector[0].get())
    return None


def build_bill(bill_category, diet_number, submission_number, bill_name):
    bill = Bill(None)
    bill.name = bill_name
    bill.bill_number = f'第{diet_number}回国会{bill_category}第{submission_number}号'
    bill.id = idgen(bill)
    return bill


def build_url(href, title, domain):
    url = Url(None)
    url.url = href
    url.title = title.value if isinstance(title, UrlTitle) else title
    url.domain = domain
    url.id = idgen(url)
    return url


def build_minutes(diet_number, house_name, meeting_name, meeting_number, topics, url, date_time):
    minutes = Minutes(None)
    minutes.name = f'第{diet_number}回{house_name}{meeting_name}第{meeting_number}号'
    minutes.topics = topics
    minutes.url = url  # ToDo: remove once frontend migrated to Minutes.urls
    minutes.start_date_time = to_neo4j_datetime(date_time)
    minutes.id = idgen(minutes)
    return minutes


def build_speech(minutes_name, speaker_name, order):
    speech = Speech(None)
    speech.name = f'{minutes_name}{order}'
    speech.speakerName = speaker_name
    speech.orderInMinutes = order
    speech.id = idgen(speech)
    return speech


def to_neo4j_datetime(dt):
    return _Neo4jDateTimeInput(year=dt.year, month=dt.month, day=dt.day)


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

    return topics
