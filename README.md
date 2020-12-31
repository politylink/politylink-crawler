### Requirements
* poetry
* [politylink-backend](https://github.com/politylink/politylink-backend)

### Set up
```
git clone https://github.com/politylink/politylink-crawler.git
cd politylink-crawler
poetry install
``` 

### Run
```shell script
poetry run scrapy crawl shugiin -a diet=203
poetry run scrapy crawl sangiin -a diet=203
poetry run scrapy crawl shugiin_minutes -a diet=203
poetry run scrapy crawl minutes -a start_date=2020-12-01 -a end_date=2020-12-08 -a speech=false
poetry run scrapy crawl shugiin_tv -a start_date=2020-12-01 -a end_date=2020-12-08
poetry run scrapy crawl mainichi -a limit=5
```

add `--loglevel DEBUG` if needed.