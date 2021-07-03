import pytest

from crawler.utils import parse_name_str, extract_bill_number_or_none, deduplicate, clean_speech, \
    extract_bill_action_types, get_str_offset, replace_kansuji_to_number, convert_kansuji_to_int, \
    extract_bill_category_or_none
from politylink.graphql.schema import BillActionType


def test_parse_name_str():
    assert parse_name_str('逢沢　一郎（あいさわ　いちろう）') == ('一郎', '逢沢', 'いちろう', 'あいさわ')
    assert parse_name_str('蓮舫（れんほう）') == ('蓮舫', '', 'れんほう', '')


def test_extract_bill_number_or_none():
    assert extract_bill_number_or_none('地方税法等の一部を改正する法律案（204国会閣9）') == '第204回国会閣法第9号'
    assert extract_bill_number_or_none('第204回国会閣法第9号') == '第204回国会閣法第9号'
    assert extract_bill_number_or_none('200衆1') == '第200回国会衆法第1号'
    assert extract_bill_number_or_none('地方税法等の一部を改正する法律案') is None


def test_extract_bill_category_or_none():
    assert extract_bill_category_or_none('デジタル庁設置法案（内閣提出）') == 'KAKUHOU'
    assert extract_bill_number_or_none('デジタル庁設置法案') is None


def test_extract_bill_action_types():
    assert extract_bill_action_types('これより質疑に入ります。') == [BillActionType.QUESTION]
    assert extract_bill_action_types('本案の趣旨の説明につきましては、これを省略します') == []


def test_deduplicate():
    assert deduplicate([]) == []
    assert deduplicate(['aaa', 'bbb', 'ccc', 'aaa', 'ddd', 'bbb']) == ['aaa', 'bbb', 'ccc', 'ddd']


def test_clean_speech():
    speech = '○議長（大島理森君）　各請願は委員長の報告を省略して採択するに御異議ありませんか。 　　　　〔「異議なし」と呼ぶ者あり〕'
    expected = '各請願は委員長の報告を省略して採択するに御異議ありませんか。〔「異議なし」と呼ぶ者あり〕'
    assert clean_speech(speech) == expected


def test_get_str_offset():
    assert get_str_offset('') == -1
    assert get_str_offset('   ') == -1
    assert get_str_offset('   こんにちは') == 3


def test_convert_kansuji_to_int():
    assert convert_kansuji_to_int('一〇') == 10
    assert convert_kansuji_to_int('四二') == 42
    assert convert_kansuji_to_int('百') == 100
    assert convert_kansuji_to_int('百九十六') == 196
    assert convert_kansuji_to_int('一九六') == 196
    assert convert_kansuji_to_int('千二') == 1002
    assert convert_kansuji_to_int('千十') == 1010
    assert convert_kansuji_to_int('千十六') == 1016
    assert convert_kansuji_to_int('千九十六') == 1096


def test_convert_kansuji_to_int_fail():
    with pytest.raises(ValueError):
        assert convert_kansuji_to_int('百千')

    with pytest.raises(ValueError):
        assert convert_kansuji_to_int('犬百')


def test_replace_kansuji_to_number():
    assert replace_kansuji_to_number('第百九十六回国会衆法第四二号') == '第196回国会衆法第42号'
