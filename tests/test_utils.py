from crawler.utils import parse_name_str


def test_parse_name_str():
    assert ('一郎', '逢沢', 'いちろう', 'あいさわ') == parse_name_str('逢沢　一郎（あいさわ　いちろう）')
    assert ('蓮舫', '', 'れんほう', '') == parse_name_str('蓮舫（れんほう）')
