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


def build_minutes(minutes_name, topics):
    minutes = Minutes(None)
    minutes.name = minutes_name
    minutes.topics = topics
    minutes.id = idgen(minutes)
    return minutes


def build_speech(speech_name, speaker, order):
    speech = Speech(None)
    speech.name = speech_name
    speech.speakerName = speaker
    speech.orderInMinutes = order
    speech.id = idgen(speech)
    return speech


def to_neo4j_datetime(dt):
    return _Neo4jDateTimeInput(year=dt.year, month=dt.month, day=dt.day)
