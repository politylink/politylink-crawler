#!/bin/bash

ministries=("caa" "cao")
for ministry in "${ministries[@]}"
do
  poetry run scrapy crawl ${ministry}
done