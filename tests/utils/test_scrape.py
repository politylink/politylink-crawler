from datetime import datetime

import pytest

from crawler.utils import extract_datetime, extract_parliamentary_group_or_none
from politylink.graphql.schema import ParliamentaryGroup


def test_extract_datetime():
    assert extract_datetime('2021年7月7日') == datetime(2021, 7, 7)
    assert extract_datetime('	2021年7月7日(水)   ') == datetime(2021, 7, 7)
    with pytest.raises(ValueError):
        extract_datetime('ワンワン')


def test_extract_parliamentary_group_or_none():
    assert extract_parliamentary_group_or_none('自民') == ParliamentaryGroup.JIMIN
    assert extract_parliamentary_group_or_none('自由民主党・無所属の会') == ParliamentaryGroup.JIMIN
    assert extract_parliamentary_group_or_none('立民') == ParliamentaryGroup.RIKKEN
    assert extract_parliamentary_group_or_none('立憲民主党・無所属') == ParliamentaryGroup.RIKKEN
    assert extract_parliamentary_group_or_none('ウサイン・ボルト') == None
