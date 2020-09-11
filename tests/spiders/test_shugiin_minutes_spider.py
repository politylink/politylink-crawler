from datetime import datetime

import pytest

from crawler.spiders.shugiin_minutes_spider import ShugiinMinutesSpider


class TestShugiinMinutesSpider:
    def test_extract_datetime_from_title(self):
        title = '第201回国会8月26日内閣委員会ニュース'
        expected = datetime(year=2020, month=8, day=26)
        actual = ShugiinMinutesSpider.extract_datetime_from_title(title)
        assert expected == actual

    def test_extract_datetime_from_title_fail(self):
        title = 'ネコちゃんニュース'
        with pytest.raises(ValueError):
            ShugiinMinutesSpider.extract_datetime_from_title(title)
