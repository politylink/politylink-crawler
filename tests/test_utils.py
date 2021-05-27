import pytest

from crawler.utils import parse_name_str, extract_bill_number_or_none, deduplicate, clean_speech, \
    extract_bill_action_types, build_bill_text, extract_minutes_schedule, extract_topics_from_line, extract_topics_v2
from politylink.graphql.schema import BillActionType


def test_parse_name_str():
    assert ('一郎', '逢沢', 'いちろう', 'あいさわ') == parse_name_str('逢沢　一郎（あいさわ　いちろう）')
    assert ('蓮舫', '', 'れんほう', '') == parse_name_str('蓮舫（れんほう）')


def test_extract_bill_number_or_none():
    assert '第204回国会閣法第9号' == extract_bill_number_or_none('地方税法等の一部を改正する法律案（204国会閣9）')
    assert '第204回国会閣法第9号' == extract_bill_number_or_none('第204回国会閣法第9号')
    assert '第200回国会衆法第1号' == extract_bill_number_or_none('200衆1')
    assert extract_bill_number_or_none('地方税法等の一部を改正する法律案') is None


def test_deduplicate():
    assert [] == deduplicate([])
    assert ['aaa', 'bbb', 'ccc', 'ddd'] == deduplicate(['aaa', 'bbb', 'ccc', 'aaa', 'ddd', 'bbb'])


def test_clean_speech():
    before = '○議長（大島理森君）　各請願は委員長の報告を省略して採択するに御異議ありませんか。 　　　　〔「異議なし」と呼ぶ者あり〕'
    after = '各請願は委員長の報告を省略して採択するに御異議ありませんか。〔「異議なし」と呼ぶ者あり〕'
    assert after == clean_speech(before)


def test_extract_bill_action_types():
    assert [BillActionType.QUESTION] == extract_bill_action_types('これより質疑に入ります。')
    assert [] == extract_bill_action_types('本案の趣旨の説明につきましては、これを省略します')


def test_build_bill_text():
    texts = [
        '犬法の一部を次のように改正する。',
        '「芝犬」を「柴犬」に改める。',
        '附 則',
        'この法律は、別に法律で定める日から施行する。',
        '理 由',
        '誤字を修正するため。'
    ]

    bill_text = build_bill_text('Bill:1', texts)
    assert bill_text.id == 'Bill:1'
    assert bill_text.body == '犬法の一部を次のように改正する。「芝犬」を「柴犬」に改める。'
    assert bill_text.supplement == 'この法律は、別に法律で定める日から施行する。'
    assert bill_text.reason == '誤字を修正するため。'


def test_build_bill_text_fail():
    texts = [
        'ワンワンワン'
    ]
    with pytest.raises(ValueError):
        build_bill_text('Bill:1', texts)


def test_extract_topics_from_line():
    assert extract_topics_from_line('日程第一　猫と犬との間の協定について承認を求めるの件') \
           == ['猫と犬との間の協定について承認を求めるの件']
    assert extract_topics_from_line('日程第二　猫法を改正する法律案（内閣提出）及び愛猫法（内閣提出）の趣旨説明及び質疑') \
           == ['猫法を改正する法律案（内閣提出）', '愛猫法（内閣提出）の趣旨説明及び質疑']
    assert extract_topics_from_line('午後一時二分開議') == []


def test_extract_topics_shugiin():
    # https://kokkai.ndl.go.jp/txt/120405254X02520210427/0
    first_speech = """
    （省略）
    　　　　―――――――――――――
    ○本日の会議に付した案件
    　日程第一　猫と犬との間の協定について承認を求めるの件
    　日程第二　猫法を改正する法律案（内閣提出）及び愛猫法（内閣提出）の趣旨説明及び質疑
    　日程第三　犬法を改正する法律案（内閣提出）
    　愛犬法（内閣提出）の趣旨説明及び質疑
    　　　　午後一時二分開議
    """

    expected_minutes_schedule = [
        '日程第一　猫と犬との間の協定について承認を求めるの件',
        '日程第二　猫法を改正する法律案（内閣提出）及び愛猫法（内閣提出）の趣旨説明及び質疑',
        '日程第三　犬法を改正する法律案（内閣提出）',
        '愛犬法（内閣提出）の趣旨説明及び質疑',
        '午後一時二分開議'  # should be removed as non-topic
    ]

    expected_topics = [
        '猫と犬との間の協定について承認を求めるの件',
        '猫法を改正する法律案（内閣提出）',
        '愛猫法（内閣提出）の趣旨説明及び質疑',
        '犬法を改正する法律案（内閣提出）',
        '愛犬法（内閣提出）の趣旨説明及び質疑'
    ]

    assert extract_minutes_schedule(first_speech, bullets={}, blocks={'―', '◇'}) == expected_minutes_schedule
    assert extract_topics_v2(first_speech, '衆議院') == expected_topics


def test_extract_topics_sangiin():
    # https://kokkai.ndl.go.jp/txt/120115007X01520200617/0
    first_speech = """
        （省略）
    　　　　─────────────
        　　本日の会議に付した案件
        ○猫と犬に関する請願（第一号外一件
        　）
        ○フェレット祭りの中止に関する請願（第二号外
        　三件）
        　　　　─────────────
        """

    expected_minutes_schedule = [
        '猫と犬に関する請願（第一号外一件）',
        'フェレット祭りの中止に関する請願（第二号外三件）'
    ]

    expected_topics = [
        '猫と犬に関する請願（第一号外一件）',
        'フェレット祭りの中止に関する請願（第二号外三件）'
    ]
    assert extract_minutes_schedule(first_speech, bullets={'○'}, blocks={'─'}) == expected_minutes_schedule
    assert extract_topics_v2(first_speech, '参議院') == expected_topics
