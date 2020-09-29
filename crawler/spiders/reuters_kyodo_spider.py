from crawler.spiders.reuters_spider import ReutersSpider


class ReutersKyodoSpider(ReutersSpider):
    name = 'reuters_kyodo'
    publisher = 'ロイター'
    limit = 3

    def __init__(self, *args, **kwargs):
        super(ReutersKyodoSpider, self).__init__(*args, **kwargs)
        self.next_page = 1

    def build_next_url(self):
        return f'https://jp.reuters.com/news/archive/kyodoPoliticsNews?view=page&page={self.next_page}&pageSize=10'
