from datetime import datetime
from logging import getLogger

from crawler.spiders import TvSpiderTemplate
from crawler.utils import build_minutes

LOGGER = getLogger(__name__)


class SangiinTvSpider(TvSpiderTemplate):
    name = 'sangiin_tv'
    domain = 'sangiin.go.jp'
    house_name = '参議院'

    def __init__(self, *args, **kwargs):
        super(SangiinTvSpider, self).__init__(5900, 10, *args, **kwargs)

    def build_next_url(self):
        self.next_id += 1
        return 'https://www.webtv.sangiin.go.jp/webtv/detail.php?sid={}'.format(self.next_id)

    def scrape_minutes(self, response):
        content = response.xpath('//div[@id="detail-contents-inner"]')
        if not content:
            content = response.xpath('//div[@id="detail-contents-inner2"]')
        date_time, meeting_name = None, None
        for dl in content.xpath('//dl'):
            term = dl.xpath('./dt/text()').get()
            desc = dl.xpath('./dd/text()').get()
            if term == '開会日':
                date_time = datetime.strptime(desc, '%Y年%m月%d日')
            elif term == '会議名':
                meeting_name = desc
        if date_time and meeting_name:
            minutes = build_minutes(self.house_name + meeting_name, date_time)
            summary = ''.join(map(lambda x: x.strip(), content.xpath('./span/text()').getall()))
            if summary:
                minutes.summary = summary
            return minutes
        return None
