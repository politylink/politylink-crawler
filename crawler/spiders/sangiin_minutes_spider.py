from logging import getLogger
from urllib.parse import urljoin

from crawler.spiders import SpiderTemplate
from crawler.utils import extract_text, build_url, UrlTitle
from politylink.graphql.schema import Minutes
from politylink.utils import DateConverter

LOGGER = getLogger(__name__)


class SangiinMinutesSpider(SpiderTemplate):
    name = 'sangiin_minutes'
    domain = 'sangiin.go.jp'
    start_urls = ['https://www.sangiin.go.jp/japanese/kon_kokkaijyoho/index.html']

    def parse(self, response):
        keika_urls = []
        sitsugi_urls = []
        for a in response.xpath('//a'):
            text = a.xpath('./text()').get()
            href = a.xpath('./@href').get()
            if text and '経過' in text:
                keika_urls.append(href)
            elif text == '質疑項目':
                sitsugi_urls.append(href)
        LOGGER.info(f'scraped {len(keika_urls)} keika urls')
        LOGGER.info(f'scraped {len(sitsugi_urls)} sitsugi urls')

        for url in keika_urls:
            yield response.follow(url, callback=self.parse_keika)
        for url in sitsugi_urls:
            yield response.follow(url, callback=self.parse_sitsugi)

    def parse_keika(self, response):
        url = build_url(response.url, title=UrlTitle.IINKAI_KEIKA, domain=self.domain)
        self.gql_client.merge(url)

        contents = response.xpath('//div[@id="ContentsBox"]')
        h2_text = contents.xpath('.//h2/text()').get()
        assert h2_text[-2:] == '経過'
        committee_name = '参議院' + h2_text[:-2]

        h4_list = contents.xpath('./h4')
        pre_list = contents.xpath('./pre')
        assert len(h4_list) == len(pre_list)
        for h4, pre in zip(h4_list, pre_list):
            dt = DateConverter.convert(extract_text(h4))
            summary = ''.join(extract_text(pre).strip().split())
            if '誤りにつき訂正' in summary:
                LOGGER.warning(f'skip non summary: {summary}')
                continue
            minutes_list = self.minutes_finder.find(committee_name, dt)
            if len(minutes_list) != 1:
                LOGGER.warning(
                    f'found {len(minutes_list)} Minutes that match with ({committee_name}, {dt}): {minutes_list}')
            for minutes in minutes_list:
                minutes = Minutes({'id': minutes.id, 'summary': summary})
                self.gql_client.merge(minutes)
                self.gql_client.link(url.id, minutes.id)

    def parse_sitsugi(self, response):
        contents = response.xpath('//div[@id="list-style"]')
        h3_text = contents.xpath('.//h3/text()').get()
        committee_name = '参議院' + h3_text.split()[-1]

        for a in contents.xpath('.//a'):
            text = a.xpath('./text()').get()
            href = urljoin(response.url, a.xpath('./@href').get())
            try:
                url = build_url(href, UrlTitle.IINKAI_SITSUGI, self.domain)
            except Exception as e:
                LOGGER.error(f'failed to build url from {a} in {response.url}')
                return
            self.gql_client.merge(url)

            dt = DateConverter.convert(text)
            minutes_list = self.minutes_finder.find(committee_name, dt)
            if len(minutes_list) != 1:
                LOGGER.warning(
                    f'found {len(minutes_list)} Minutes that match with ({committee_name}, {dt}): {minutes_list}')
            for minutes in minutes_list:
                self.gql_client.link(url.id, minutes.id)
