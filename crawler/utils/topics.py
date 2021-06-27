import re

from crawler.utils.common import contains_word, getLogger, get_offset

LOGGER = getLogger(__name__)

TOPIC_SECTIONS = ['議事日程', '本日の会議に付した案件', '本日の公聴会で意見を聞いた案件']
TOPIC_WORDS = ['法律案', '法案', '決議案', '議決案', '調査', '調書', '協定', '承認', '予算', '互選', '件', '決算書', '計算書', '請願', '質疑']
IGNORE_WORDS = ['-', '―', '━', '─', '◇', '開議']


def extract_topics_v3(first_speech, split=False):
    lines = first_speech.split('\n')

    topic_lines = []
    for i, line in enumerate(lines):
        if contains_word(line, TOPIC_SECTIONS):
            topic_lines = lines[i + 1:]
            break

    topics = []
    buffer = ''
    parent_offset = 0  # check offset to remove unnecessary line breaks
    for line in topic_lines + ['']:  # add sentinel to flush buffer
        offset = get_offset(line)  # -1 when ''
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
                topics.append(buffer)
            buffer = ''
        if append_line:
            buffer += line
    return topics


def extract_minutes_schedule(first_speech, bullets=None, blocks=None):
    """
    会議録の最初の発言（=会議録情報）からその会議に付された案件のリストを抽出する
    a.k.a format_first_speech

    :param first_speech: 会議録の最初の発言
    :param bullets: 議題の先頭文字の集合
    :param blocks: セクション区切り文字の集合

    :return: 会議に付された案件のリスト
    """

    bullets = bullets or set()
    blocks = blocks or set()

    is_schedule = False
    schedule_lines = list()
    buffer = ''
    for line in first_speech.split('\n'):
        line = line.strip()
        if contains_word(line, ['本日の会議に付した案件', '本日の公聴会で意見を聞いた案件']):
            is_schedule = True
            schedule_lines = list()  # 複数回ヒットする場合は最後を優先する
            continue
        if line and is_schedule:
            if line[0] in blocks:
                is_schedule = False
                continue

            if bullets:  # トピック内の改行が存在する可能性あり
                if line[0] in bullets:
                    if buffer:
                        schedule_lines.append(buffer)
                    buffer = line[1:]
                else:
                    buffer += line
            else:  # トピック内の改行は存在しない
                schedule_lines.append(line)
    if buffer:
        schedule_lines.append(buffer)
    return schedule_lines


def extract_topics_from_line(line):
    line = re.sub(r'^第?(一|二|三|四|五|六|七|八|九|十)+(　|、)?', '', line)
    line = line.replace('、', '\u3000')  # 読点はトピック名の区切りとして\u3000に置換
    line = line.replace('）及び', '）\u3000')  # "）及び"はトピック名の区切りとして"及び"を削除し\u3000に置換

    topic_words = ['法律案', '法案', '決議案', '議決案', '調査', '調書', '協定', '承認', '予算', '互選', '件', '決算書', '計算書', '請願', '質疑']
    topics = []
    for maybe_topic in line.split():
        if contains_word(maybe_topic, topic_words):
            topics.append(maybe_topic)
    return topics


def extract_topics_v2(first_speech, house):
    if house == '衆議院':
        minutes_schedule = extract_minutes_schedule(first_speech, bullets={}, blocks={'―', '◇'})
    elif house == '参議院':
        minutes_schedule = extract_minutes_schedule(first_speech, bullets={'○'}, blocks={'─'})
    else:
        raise ValueError(f'unknown house: {house}')

    topics = []
    for line in minutes_schedule:
        topics += extract_topics_from_line(line)
    return topics


def extract_topics(first_speech, split=False):
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
