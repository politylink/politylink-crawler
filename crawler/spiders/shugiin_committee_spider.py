from logging import getLogger

from crawler.spiders import SpiderTemplate
from crawler.utils import extract_text, build_committee

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
        LOGGER.info(f'scraped {len(committees)} committees')

        for committee in committees:
            self.client.exec_merge_committee(committee)
        LOGGER.info(f'merged {len(committees)} committees')

    @staticmethod
    def scrape_committees_from_table(table):
        committees = []
        for row in table.xpath('.//tr')[1:]:  # skip header
            cells = row.xpath('.//td')
            assert len(cells) == 3
            try:
                committee_name = '衆議院' + extract_text(cells[0]).strip()
                LOGGER.info(committee_name)
                num_members = int(extract_text(cells[1]).replace('人', ''))
                matters = ShugiinMinutesSpider.extract_matters(cells[2])
            except Exception as e:
                LOGGER.warning(f'failed to parse row:\n{row.get()}\n{e}')
                continue
            committee = build_committee(committee_name, 'REPRESENTATIVES', num_members, matters)
            committees.append(committee)
        return committees

    @staticmethod
    def extract_matters(cell):
        matters = []
        for li in cell.xpath('.//li'):
            matters.append(extract_text(li).strip())
        if len(matters) == 0:
            matters.append(extract_text(cell).strip())
        return matters
