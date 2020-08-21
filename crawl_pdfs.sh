#!/bin/bash

spiders=("caa" "cao" "cas" "env" "fsa" "maff" "meti" "mext" "mhlw" "mlit" "mod" "mof" "mofa" "moj" "npa" "ppc" "recon" "sanhou" "shuhou" "soumu")
for spider in "${spiders[@]}"
do
  poetry run scrapy crawl ${spider}
done