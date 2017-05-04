#coding=utf-8
import os,sys
from scrapy.cmdline import execute

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(['scrapy','crawl','jobbole'])
# execute(['scrapy','crawl','zhihu'])
# execute(['scrapy','crawl','xizi_agent'])

