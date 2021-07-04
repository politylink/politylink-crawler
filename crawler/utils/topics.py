"""
国会会議録からトピックを抽出するためのメソッドを定義する
"""

import re
from logging import getLogger

from crawler.utils.common import contains_word
from politylink.utils import get_str_offset, deduplicate

LOGGER = getLogger(__name__)

TOPIC_SECTIONS = ['議事日程', '本日の会議に付した案件', '本日の公聴会で意見を聞いた案件']
TOPIC_WORDS = ['法律案', '法案', '決議案', '議決案', '調査', '調書', '協定', '承認', '予算', '互選', '件', '決算書', '計算書', '請願', '質疑']
IGNORE_WORDS = ['-', '―', '━', '─', '◇', '開議']


def extract_topics(first_speech, clean=True, split=True):
    """
    会議録の最初の発言（=会議録情報）からその会議のトピックのリストを抽出する

    :param first_speech: 会議録の最初の発言
    :param clean: 「日程第一」などの表記をトピックから除く
    :param split: 「、」もしくは「及び」を使って並列表記されたトピックを分割する

    :return: 会議のトピックのリスト


    不必要な行内の改行を取り除くために文字下げをチェックする必要がある。

    (Before)
    PARENT 1      // offset=0
        CHILD 11  //       =4
        CHILD 12  //       =4
    PARENT 2      //       =0 (flush buffer, update parent offset)
        CHILD 21  //       =4
        -------   //       =4 (flush buffer)
    PARENT 3      //       =0 (update parent offset)
    ""            //       =-1 (flush buffer)

    (After)
    PARENT1 + CHILD11 + CHILD12
    PARENT2 + CHILD21
    PARENT3
    """

    lines = first_speech.split('\n')

    topic_lines = []
    for i, line in enumerate(lines):
        if contains_word(line, TOPIC_SECTIONS):
            topic_lines = lines[i + 1:]
            break

    topics = []
    buffer = ''
    parent_offset = 0
    for line in topic_lines + ['']:  # 最後にbufferを処理するための番兵
        offset = get_str_offset(line)
        line = line.strip()

        if not buffer:
            parent_offset = offset

        if contains_word(line, IGNORE_WORDS + TOPIC_SECTIONS):
            flush_buffer, append_line = True, False
            parent_offset = 0  # update parent_offset with the next line
        elif offset <= parent_offset:  # found next parent line
            flush_buffer, append_line = True, True
            parent_offset = offset
        else:  # found child line
            flush_buffer, append_line = False, True

        if flush_buffer:
            if contains_word(buffer, TOPIC_WORDS):
                if clean:
                    buffer = clean_topic(buffer)
                if split:
                    topics += split_topic(buffer)
                else:
                    topics.append(buffer)
            buffer = ''
        if append_line:
            buffer += line
    return deduplicate(topics)


def clean_topic(topic):
    return re.sub(r'^○?(日程)?第?(一|二|三|四|五|六|七|八|九|十)*、?', '', topic).strip()


def split_topic(topic):
    # ）の後の「及び」を読点に変換
    topic = topic.replace('）及び', '）、')
    # ）の後の（）に含まれていない読点で分割
    # https://stackoverflow.com/questions/2785755/how-to-split-but-ignore-separators-in-quoted-strings-in-python
    pattern = '）、(?=(?:[^（）]|（[^（）]*）)*$)'
    topics = re.split(pattern, topic)
    return [x + '）' for x in topics[:-1]] + [topics[-1]]  # ）を復元


def clean_committee_topic(topic):
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
