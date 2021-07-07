from datetime import datetime

import pytest

from crawler.utils import extract_datetime


def test_extract_datetime():
    assert extract_datetime('2021年7月7日') == datetime(2021, 7, 7)
    assert extract_datetime('2021年7月7日') == datetime(2021, 7, 7)
    with pytest.raises(ValueError):
        extract_datetime('ワンワン')
