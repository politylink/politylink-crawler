import pytest

from crawler.utils.elasticsearch import build_bill_text


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
        '法律案は附則と理由を含む必要がある'
    ]
    with pytest.raises(ValueError):
        build_bill_text('Bill:1', texts)
