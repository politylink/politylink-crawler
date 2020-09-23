from datetime import datetime

from crawler.spiders.nikkei_spider import NikkeiSpider


class TestNikkeiSpider:
    def test_extract_datetime_pair(self):
        text = None
        dt1, dt2 = NikkeiSpider.extract_datetime_pair(text)
        assert dt1 is None
        assert dt2 is None

        text = '2020/9/1 00:00'
        dt1, dt2 = NikkeiSpider.extract_datetime_pair(text)
        assert datetime(2020, 9, 1, 0, 0) == dt1
        assert dt2 is None

        text = ' 2020/9/4 16:00  (2020/9/5 5:09更新) '
        dt1, dt2 = NikkeiSpider.extract_datetime_pair(text)
        assert datetime(2020, 9, 4, 16, 0) == dt1
        assert datetime(2020, 9, 5, 5, 9) == dt2
