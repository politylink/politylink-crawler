import re
from logging import getLogger

from crawler.spiders import SpiderTemplate
from crawler.utils import extract_text, build_committee

LOGGER = getLogger(__name__)


class SangiinCommitteeSpider(SpiderTemplate):
    name = 'sangiin_committee'
    start_urls = ['https://www.sangiin.go.jp/japanese/kon_kokkaijyoho/iinkai/tiinkai.html']

    def parse(self, response):
        committees = self.scrape_committees_from_response(response)
        LOGGER.info(f'scraped {len(committees)} committees')
        for committee in committees:
            self.client.exec_merge_committee(committee)
        LOGGER.info(f'merged {len(committees)} committees')

    @staticmethod
    def scrape_committees_from_response(response):
        div = response.xpath('//div[@id="ContentsBox"]')[0]
        name_list = SangiinCommitteeSpider.scrape_name_list(div)
        LOGGER.debug(f'scraped {len(name_list)} names: {name_list}')
        num_members_list = SangiinCommitteeSpider.scrape_num_members_list(div)
        LOGGER.debug(f'scraped {len(num_members_list)} num members: {num_members_list}')
        matters_list = SangiinCommitteeSpider.scrape_matters_list(div)
        LOGGER.debug(f'scraped {len(matters_list)} matters: {matters_list}')
        LOGGER.debug(matters_list)

        assert len(name_list) == len(num_members_list) == len(matters_list)
        committees = []
        for name, num_members, matters in zip(name_list, num_members_list, matters_list):
            committee = build_committee(name, "COUNCILORS", num_members, matters)
            committees.append(committee)
        return committees

    @staticmethod
    def scrape_name_list(div):
        ret = []
        for h4 in div.css('h4.ta_l').css('h4.mt20').css('h4.fl_l'):
            ret.append(extract_text(h4))
        return ret

    @staticmethod
    def scrape_num_members_list(div):
        ret = []
        for p in div.css('p'):
            text = extract_text(p)
            pattern = r'委員数：([0-9]+)人'
            match = re.fullmatch(pattern, text)
            if match:
                ret.append(int(match.group(1)))
        return ret

    @staticmethod
    def scrape_matters_list(div):
        ret = []
        for oul in div.css('ol, ul'):
            matters = []
            for li in oul.css('li'):
                matters.append(extract_text(li).strip())
            ret.append(matters)
        return ret
