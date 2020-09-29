from crawler.spiders.reuters_spider import ReutersSpider


class ReutersKyodoSpider(ReutersSpider):
    name = 'reuters_kyodo'
    publisher = 'ロイター'

    def __init__(self, limit, *args, **kwargs):
        super(ReutersKyodoSpider, self).__init__(limit, *args, **kwargs)

    def build_next_url(self):
        return f'https://jp.reuters.com/news/archive/kyodoPoliticsNews?view=page&page={self.next_page}&pageSize=10'
