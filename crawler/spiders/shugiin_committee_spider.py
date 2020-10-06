from logging import getLogger

from crawler.spiders import SpiderTemplate
from crawler.utils import extract_text, build_committee, clean_topic

LOGGER = getLogger(__name__)


class ShugiinCommitteeSpider(SpiderTemplate):
    name = 'shugiin_committee'
    start_urls = [
        'http://www.shugiin.go.jp/internet/itdb_iinkai.nsf/html/iinkai/iinkai_jounin.htm',
        'http://www.shugiin.go.jp/internet/itdb_iinkai.nsf/html/iinkai/iinkai_tokubetu.htm'
    ]

    def parse(self, response):
        table = response.xpath('//table')[0]
        committees = self.scrape_committees_from_table(table)
        self.gql_client.bulk_merge(committees)
        LOGGER.info(f'merged {len(committees)} committees')

    @staticmethod
    def scrape_committees_from_table(table):
        committees = []
        for row in table.xpath('.//tr')[1:]:  # skip header
            cells = row.xpath('.//td')
            assert len(cells) == 3
            try:
                committee_name = '衆議院' + extract_text(cells[0]).strip()
                num_members = int(extract_text(cells[1]).replace('人', ''))
                topics = ShugiinCommitteeSpider.extract_topics(cells[2])
            except Exception as e:
                LOGGER.warning(f'failed to parse row:\n{row.get()}\n{e}')
                continue
            committee = build_committee(committee_name, 'REPRESENTATIVES', num_members, topics)
            committees.append(committee)
        return committees

    @staticmethod
    def extract_topics(cell):
        topics = []
        for li in cell.xpath('.//li'):
            topics.append(clean_topic(extract_text(li)))
        if len(topics) == 0:
            topics.append(clean_topic(extract_text(cell)))
        return topics
