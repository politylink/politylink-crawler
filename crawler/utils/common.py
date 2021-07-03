import re
import unicodedata
from logging import getLogger

from politylink.graphql.schema import BillActionType

LOGGER = getLogger(__name__)
KANSUJI = '〇一二三四五六七八九'
KANSUJI_DIGIT = '十百千万'


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
    moderators = {'議長', '委員長', '会長', '主査'}
    return any([m in speaker for m in moderators])


def strip_join(str_list, sep=''):
    return sep.join(map(lambda x: x.strip(), str_list))


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
    sr = s[::-1]  # digitを後ろから変換する
    for i, si in enumerate(sr):
        if si in KANSUJI_DIGIT:
            zeros = KANSUJI_DIGIT.find(si) + 1
            if len(buffer) > zeros:
                raise ValueError(f'too many numbers before "{si}": {s}')
            buffer += '〇' * (zeros - len(buffer))  # 〇で桁を埋める
            if i == len(sr) - 1 or sr[i + 1] not in KANSUJI:
                buffer += '一'
        elif si in KANSUJI:
            buffer += si
        else:
            raise ValueError(f'found non-kansuji "{si}": {s}')
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


def extract_bill_category_or_none(text):
    if contains_word(text, ['内閣提出', '閣法']):
        return 'KAKUHOU'
    elif contains_word(text, ['衆議院提出', '衆法']):
        return 'SHUHOU'
    elif contains_word(text, ['参議院提出', '参法']):
        return 'SANHOU'
    return None


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


def deduplicate(items):
    return list(dict.fromkeys(items))


def get_str_offset(s):
    for i, c in enumerate(s):
        if c not in {' ', '　'}:
            return i
    return -1
