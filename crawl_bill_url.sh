#!/bin/bash

spiders=("caa" "cao" "cas" "maff" "mlit" "mof" "mofa" "npa" "sanhou" "shuhou" "soumu")
for spider in "${spiders[@]}"
do
  poetry run scrapy crawl ${spider}
done