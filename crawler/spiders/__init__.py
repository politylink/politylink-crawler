import logging
from urllib.parse import urljoin

import scrapy

from crawler.utils import extract_text, build_url, UrlTitle, validate_news_or_raise, validate_news_text_or_raise, \
    build_minutes_activity
from politylink.elasticsearch.client import ElasticsearchClient
from politylink.elasticsearch.schema import NewsText
from politylink.graphql.client import GraphQLClient
from politylink.graphql.schema import News
from politylink.helpers import BillFinder, MinutesFinder, CommitteeFinder, MemberFinder
from politylink.utils.bill import extract_bill_number_or_none, extract_bill_category_or_none

LOGGER = logging.getLogger(__name__)


class SpiderTemplate(scrapy.Spider):
    domain = NotImplemented

    def __init__(self, *args, **kwargs):
        super(SpiderTemplate, self).__init__(*args, **kwargs)
        logging.getLogger('elasticsearch').setLevel(logging.WARNING)
        logging.getLogger('sgqlc').setLevel(logging.WARNING)
        self.gql_client = GraphQLClient()
        self.es_client = ElasticsearchClient()
        self.bill_finder = BillFinder()
        self.minutes_finder = MinutesFinder()
        self.committee_finder = CommitteeFinder()
        self.member_finder = MemberFinder()

    def parse(self, response):
        NotImplemented

    def link_urls(self, urls):
        """
        link Url to parent resource
        """

        from_ids, to_ids = [], []
        for url in urls:
            if hasattr(url, 'to_id'):
                from_ids.append(url.id)
                to_ids.append(url.to_id)
        if from_ids:
            self.gql_client.bulk_link(from_ids, to_ids)

    def link_activities(self, activities):
        """
        link Activity to Member, Bill, and Minutes
        """

        from_ids, to_ids = [], []
        for activity in activities:
            for id_field in ['member_id', 'bill_id', 'minutes_id']:
                if hasattr(activity, id_field):
                    from_ids.append(activity.id)
                    to_ids.append(getattr(activity, id_field))
        if from_ids:
            self.gql_client.bulk_link(from_ids, to_ids)

    def link_bill_action(self, bill_action_lst):
        """
        link BillAction to Bill, Minutes, and Speech
        """

        from_ids, to_ids = [], []
        for bill_action in bill_action_lst:
            for id_field in ['bill_id', 'minutes_id', 'speech_id']:
                if hasattr(bill_action, id_field):
                    from_ids.append(bill_action.id)
                    to_ids.append(getattr(bill_action, id_field))
        if from_ids:
            self.gql_client.bulk_link(from_ids, to_ids)

    def link_minutes(self, minutes):
        """
        link Minutes to Bill, Member, and Committee
        """

        if hasattr(minutes, 'topic_ids'):
            bill_ids = list(filter(lambda x: x, minutes.topic_ids))
            if bill_ids:
                self.gql_client.bulk_link([minutes.id] * len(bill_ids), bill_ids)
                LOGGER.info(f'linked {len(bill_ids)} bills to {minutes.id}')

        if hasattr(minutes, 'speaker_ids'):
            member_ids = list(filter(lambda x: x, minutes.speaker_ids))
            if member_ids:
                self.gql_client.bulk_link(member_ids, [minutes.id] * len(member_ids))
                LOGGER.info(f'linked {len(member_ids)} members to {minutes.id}')

        try:
            committee = self.committee_finder.find_one(minutes.name)
        except ValueError as e:
            LOGGER.warning(e)
        else:
            self.gql_client.link(minutes.id, committee.id)

    def link_speeches(self, speeches):
        from_ids, to_ids = [], []
        for speech in speeches:
            from_ids.append(speech.id)
            to_ids.append(speech.minutes_id)
            if hasattr(speech, 'member_id'):
                from_ids.append(speech.member_id)
                to_ids.append(speech.id)
        if from_ids:
            self.gql_client.bulk_link(from_ids, to_ids)

    def delete_old_urls(self, src_id, url_title):
        obj = self.gql_client.get(src_id, fields=['urls'])
        for url in obj.urls:
            if url.title == url_title:
                self.gql_client.delete(url.id)
                LOGGER.info(f'deleted {url.id}')

    def get_diet(self, diet_number=None):
        if diet_number:
            return self.gql_client.get(f'Diet:{diet_number}', ['id', 'number', 'start_date'])
        else:
            return self.get_latest_diet()

    def get_latest_diet(self):
        diets = sorted(self.gql_client.get_all_diets(['id', 'number', 'start_date']), key=lambda x: x.number)
        return diets[-1]

    def get_topic_ids(self, topics):
        def get_topic_id(topic):
            maybe_bill_number = extract_bill_number_or_none(topic)
            maybe_category = extract_bill_category_or_none(topic)
            try:
                if maybe_bill_number:
                    bill = self.bill_finder.find_one(maybe_bill_number)
                elif maybe_category:
                    bill = self.bill_finder.find_one(topic, category=maybe_category)
                else:
                    bill = self.bill_finder.find_one(topic)
                return bill.id
            except ValueError as e:
                LOGGER.debug(e)  # this is expected when topic does not include bill
            return ''

        return list(map(lambda x: get_topic_id(x), topics))

    def get_speakers_ids(self, speakers):
        def get_speaker_id(speaker):
            try:
                member = self.member_finder.find_one(speaker)
                return member.id
            except ValueError as e:
                LOGGER.debug(e)  # this is expected when speaker is not member
            return ''

        return list(map(lambda x: get_speaker_id(x), speakers))


class TableSpiderTemplate(SpiderTemplate):
    table_idx = NotImplemented
    bill_col = NotImplemented
    url_col = NotImplemented
    bill_category = None
    diet_number = None

    def parse(self, response):
        table = response.xpath('//table')[self.table_idx]
        self.parse_table(table, self.bill_category, self.diet_number)

    def parse_table(self, table, bill_category=None, diet_number=None):
        for row in table.xpath('.//tr'):
            cells = row.xpath('.//td')
            if len(cells) > max(self.bill_col, self.url_col):
                try:
                    bill_query = extract_text(cells[self.bill_col]).strip()
                    urls = self.extract_urls(cells[self.url_col])
                    LOGGER.info(f'scraped {len(urls)} urls for {bill_query}')
                    self.store_urls_for_bill(urls, bill_query, bill_category, diet_number)
                except Exception as e:
                    LOGGER.warning(f'failed to parse {row}: {e}')
                    continue

    def extract_urls(self, cell):
        urls = []
        for a in cell.xpath('.//a'):
            text = extract_text(a)
            href = urljoin(self.start_urls[0], a.xpath('./@href').get())
            if '概要' in text:
                urls.append(build_url(href, UrlTitle.GAIYOU_PDF, self.domain))
            elif '新旧' in text:
                urls.append(build_url(href, UrlTitle.SINKYU_PDF, self.domain))
        return urls

    def store_urls_for_bill(self, urls, bill_query, bill_category=None, diet_number=None):
        if not urls:
            return
        kwargs = {'exact_match': True}
        if bill_category:
            kwargs['category'] = bill_category
        if diet_number:
            kwargs['diet_number'] = diet_number
        try:
            bill = self.bill_finder.find_one(bill_query, **kwargs)
        except ValueError as e:
            LOGGER.warning(e)
        else:
            self.gql_client.bulk_merge(urls)
            self.gql_client.bulk_link(map(lambda x: x.id, urls), [bill.id] * len(urls))
            LOGGER.info(f'linked {len(urls)} urls to {bill.bill_number}')


class DietTableSpiderTemplate(TableSpiderTemplate):
    def __init__(self, diet=None, *args, **kwargs):
        super(DietTableSpiderTemplate, self).__init__(*args, **kwargs)
        self.diet = self.get_diet(diet)
        self.start_urls = [self.build_start_url(self.diet.number)]

    def parse(self, response):
        table = response.xpath('//table')[self.table_idx]
        self.parse_table(table, self.bill_category, self.diet.number)

    @staticmethod
    def build_start_url(diet_number):
        NotImplemented


class TvSpiderTemplate(SpiderTemplate):

    def build_activities_and_urls(self, atags, minutes, response_url):
        """
        build Minutes Activities from a tags listed in TV page
        """

        activity_list, url_list = [], []
        for a in atags:
            text = a.xpath('./text()').get()
            href = a.xpath('./@href').get()
            try:
                member = self.member_finder.find_one(text)
            except ValueError as e:
                LOGGER.debug(e)  # this is expected when speaker is not member
            else:
                activity = build_minutes_activity(member.id, minutes.id, minutes.start_date_time)
                url = build_url(urljoin(response_url, href), UrlTitle.SHINGI_TYUKEI, self.domain)
                url.to_id = activity.id
                activity_list.append(activity)
                url_list.append(url)
        return activity_list, url_list


class NewsSpiderTemplate(SpiderTemplate):
    def parse_news(self, response):
        """
        NewsとNewsTextをGraphQLとElasticSearchにそれぞれ保存する
        """

        try:
            news, news_text = self.scrape_news_and_text(response)
            validate_news_or_raise(news)
            validate_news_text_or_raise(news_text)
            self.gql_client.merge(news)
            self.es_client.index(news_text)
            LOGGER.info(f'saved {news.id}')
        except Exception:
            LOGGER.exception(f'failed to save News from {response.url}')

    def scrape_news_and_text(self, response) -> (News, NewsText):
        NotImplemented
