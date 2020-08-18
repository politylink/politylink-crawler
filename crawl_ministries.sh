#!/bin/bash

ministries=("caa" "cao" "cas" "env" "fsa" "maff" "mext" "mhlw" "mlit" "mod" "mof" "mofa" "moj" "npa" "soumu")
for ministry in "${ministries[@]}"
do
  poetry run scrapy crawl ${ministry}
done