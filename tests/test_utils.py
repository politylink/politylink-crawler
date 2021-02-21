from crawler.utils import parse_name_str, extract_bill_number_or_none, deduplicate


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
