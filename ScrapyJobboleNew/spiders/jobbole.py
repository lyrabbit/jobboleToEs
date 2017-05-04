# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.http import Request
import urlparse
from ScrapyJobboleNew.items import jobBoleArticleItem,ArticleItemLoader
from scrapy.loader import ItemLoader
from ScrapyJobboleNew.items import get_md5
import datetime
class JobboleSpider(scrapy.Spider):
    name = "jobbole"
    allowed_domains = ["blog.jobbole.com"]
    start_urls = (
        'http://blog.jobbole.com/all-posts',
    )

    def parse(self, response):
        '''
        获取列表中的所有文章 url ，并交给scrapy下载后调用回调函数进进行解析
        '''
        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            image_url = urlparse.urljoin(response.url,post_node.css("img::attr(src)").extract()[0])
            post_url = urlparse.urljoin(response.url,post_node.css("::attr(href)").extract()[0])
            yield Request(url=post_url,meta={"front_image_url":image_url},callback= self.scrapy_detail)

        #提取下一页url交给scrapy进行下载
        next_url = response.css(".next.page-numbers::attr(href)").extract()[0]
        if next_url:
            next_url = urlparse.urljoin(response.url,next_url)
            yield Request(url=next_url,callback=self.parse)

    def scrapy_detail(self,response):
        article_item =jobBoleArticleItem()

        ##通过item_loader加载item
        article_item = jobBoleArticleItem()
        front_image_url = response.meta.get("front_image_url","") #文章封面图
        item_loader = ArticleItemLoader(item=jobBoleArticleItem(),response=response)
        item_loader.add_css("title", ".entry-header h1::text")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("create_date", "p.entry-meta-hide-on-mobile::text")
        item_loader.add_value("front_image_url", [front_image_url])
        item_loader.add_css("praise_nums", ".vote-post-up h10::text")
        item_loader.add_css("comment_nums", "a[href='#article-comment'] span::text")
        item_loader.add_css("fav_nums", ".bookmark-btn::text")
        item_loader.add_css("tags", "p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", "div.entry")

        article_item = item_loader.load_item()

        yield article_item

'''
xpath节点关系
1. 父节点  上一层节点
2. 子节点
3. 同胞节点
4. 先辈节点
5. 后代节点
'''