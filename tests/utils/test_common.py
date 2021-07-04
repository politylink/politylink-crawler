from crawler.utils import parse_name_str, clean_speech


def test_clean_speech():
    speech = '○議長（大島理森君）　各請願は委員長の報告を省略して採択するに御異議ありませんか。 　　　　〔「異議なし」と呼ぶ者あり〕'
    expected = '各請願は委員長の報告を省略して採択するに御異議ありませんか。〔「異議なし」と呼ぶ者あり〕'
    assert clean_speech(speech) == expected


def test_parse_name_str():
    assert parse_name_str('逢沢　一郎（あいさわ　いちろう）') == ('一郎', '逢沢', 'いちろう', 'あいさわ')
    assert parse_name_str('蓮舫（れんほう）') == ('蓮舫', '', 'れんほう', '')
