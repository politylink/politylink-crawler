import json
import re
import unicodedata
from logging import getLogger
from urllib.parse import urljoin

LOGGER = getLogger(__name__)
KANSUJI = '〇一二三四五六七八九'
KANSUJI_DIGIT = '十百千万'


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


def to_date_str(dt):
    return '{:02d}-{:02d}-{:02d}'.format(dt.year, dt.month, dt.day)


def contains_word(text, allow_list=None, block_list=None):
    allow_list = allow_list or list()
    block_list = block_list or list()
    has_allow_word = any(w in text for w in allow_list)
    has_block_word = any(w in text for w in block_list)
    return has_allow_word and not has_block_word


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


def convert_kansuji_to_int(s):
    buffer = ''
    sr = s[::-1]
    for i, si in enumerate(sr):
        if si in KANSUJI_DIGIT:
            zeros = KANSUJI_DIGIT.find(si) + 1
            buffer += '〇' * (zeros - len(buffer))  # 〇で桁を揃える
            if i == len(sr) - 1 or sr[i + 1] not in KANSUJI:
                buffer += '一'
        else:
            buffer += si
    return int(''.join([str(int(unicodedata.numeric(x))) for x in buffer[::-1]]))


def replace_kansuji_to_number(s):
    pattern = f'[{KANSUJI + KANSUJI_DIGIT}]+'
    return re.sub(pattern, lambda x: str(convert_kansuji_to_int(x.group(0))), s)


def extract_bill_number_or_none(text):
    pattern = r'第?([0-9]+)回?(国会)?(閣|衆|参|)法?第?([0-9]+)号?'
    match = re.search(pattern, replace_kansuji_to_number(text))
    if not match:
        return None
    bill_number = '第{}回国会{}法第{}号'.format(match.group(1), match.group(3), match.group(4))
    return bill_number


def extract_category_or_none(text):
    if contains_word(text, ['内閣提出', '閣法']):
        return 'KAKUHOU'
    elif contains_word(text, ['衆議院提出', '衆法']):
        return 'SHUHOU'
    elif contains_word(text, ['参議院提出', '参法']):
        return 'SANHOU'
    else:
        return None


def deduplicate(items):
    return list(dict.fromkeys(items))


def get_offset(s):
    for i, c in enumerate(s):
        if c not in {' ', '　'}:
            return i
    return -1
