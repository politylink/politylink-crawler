from datetime import datetime
from logging import getLogger

from crawler.spiders import TvSpiderTemplate
from crawler.utils import build_minutes

LOGGER = getLogger(__name__)


class ShugiinTvSpider(TvSpiderTemplate):
    name = 'shugiin_tv'
    domain = 'shugiintv.go.jp'
    house_name = '衆議院'

    def __init__(self, *args, **kwargs):
        super(ShugiinTvSpider, self).__init__(50000, 20, *args, **kwargs)

    def build_next_url(self):
        self.next_id += 1
        return 'https://www.shugiintv.go.jp/jp/index.php?ex=VL&deli_id={}'.format(self.next_id)

    def scrape_minutes(self, response):
        date_time, meeting_name = None, None
        for row in response.xpath('//div[@id="library"]/table//tr'):
            tds = row.xpath('./td')
            term = tds[1].xpath('.//text()').get()
            desc = tds[3].xpath('.//text()').get().split()[0]
            if term == '開会日':
                date_time = datetime.strptime(desc, '%Y年%m月%d日')
            if term == '会議名':
                meeting_name = self.get_full_meeting_name(desc)
        if date_time and meeting_name:
            minutes = build_minutes(self.house_name, meeting_name, date_time)
            topics = []
            tables = response.xpath('//div[@id="library2"]/table')
            if tables:
                for row in tables[0].xpath('./tr'):
                    topic = row.xpath('./td//text()').get()
                    if topic and not topic.startswith('案件'):
                        topics.append(topic)
            if topics:
                minutes.topics = topics
            return minutes
        return None

    @staticmethod
    def get_full_meeting_name(meeting_name):
        full_name_map = {
            '倫理選挙特別委員会': '政治倫理の確立及び公職選挙法改正に関する特別委員会',
            '沖縄北方特別委員会': '沖縄及び北方問題に関する特別委員会',
            '拉致問題特別委員会': '北朝鮮による拉致問題等に関する特別委員会',
            '消費者問題特別委員会': '消費者問題に関する特別委員会',
            '科学技術特別委員会': '科学技術・イノベーション推進特別委員会',
            '震災復興特別委員会': '東日本大震災復興特別委員会',
            '地方創生特別委員会': '地方創生に関する特別委員会'
        }
        if meeting_name in full_name_map:
            return full_name_map[meeting_name]
        return meeting_name
