### Requirements
* poetry

### Set up
```
git clone https://github.com/politylink/politylink-crawler.git
cd politylink-crawler
poetry install
``` 

### Run

* 議案取得用のクローラー
```shell script
poetry run scrapy crawl shugiin
poetry run scrapy crawl sangiin
```

* 議事録取得用のクローラー
```shell script
poetry run scrapy crawl minutes -a start_date=2020-01-01 -a end_date=2020-07-01 -a speech=false
```

* PDFクローラー
```shell script
./crawl_pdfs.sh
```