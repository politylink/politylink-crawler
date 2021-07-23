from datetime import datetime

import pytest

from crawler.utils.scrape import extract_datetime, extract_parliamentary_group_or_none, extract_parliamentary_groups
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


def test_extract_parliamentary_groups():
    assert extract_parliamentary_groups('') == []
    assert extract_parliamentary_groups('自由民主党・無所属の会; 公明党; 日本維新の会・無所属の会; 国民民主党・無所属クラブ') == \
           [ParliamentaryGroup.JIMIN, ParliamentaryGroup.KOMEI, ParliamentaryGroup.ISHIN, ParliamentaryGroup.KOKUMIN]
