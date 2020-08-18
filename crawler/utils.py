import re
from urllib.parse import urljoin

from politylink.graphql.schema import Bill, Url, Minutes, Speech, _Neo4jDateTimeInput
from politylink.idgen import idgen


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
    url.title = title
    url.domain = domain
    url.id = idgen(url)
    return url


def build_minutes(diet_number, house_name, meeting_name, meeting_number, topics, url, date_time):
    minutes = Minutes(None)
    minutes.name = f'第{diet_number}回{house_name}{meeting_name}第{meeting_number}号'
    minutes.topics = topics
    minutes.url = url
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
    def format_first_speech(speech):
        start_idx = re.search(r'本日の会議に付した案件', speech).end()
        speech = speech[start_idx:]
        if re.search(r'\r\n○', speech) is not None:
            speech = speech.replace('\r\n\u3000', '')
            speech = speech.replace('\r\n○', '\r\n\u3000')
        else:
            speech = speech.replace('\r\n\u3000\u3000', '')
        return speech

    topics = []
    first_speech = format_first_speech(first_speech)
    topic_patterns = [re.compile(r'第(一|二|三|四|五|六|七|八|九|十)+\s\S+'),
                      re.compile(r'\w+\S+(法律案|決議案|議決案|調査|特別措置法案|予算|互選|件|決算書|計算書|請願)(\（.+\）)?')]
    for pattern in topic_patterns:
        for m in pattern.finditer(first_speech):
            topic = m.group()
            topic = re.sub(r'^第?(一|二|三|四|五|六|七|八|九|十)+(　|、)?', '', topic)
            # remove brackets and text
            topic = re.sub(r'(\(|（)[^)]*(\)|）)?', '', topic)
            topic = topic.strip()
            if topic not in topics:
                topics.append(topic)

    return topics
