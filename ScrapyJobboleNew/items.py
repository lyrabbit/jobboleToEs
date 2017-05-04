# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose,TakeFirst ,Join
import datetime
from settings import SQL_DATETIME_FORMAT, SQL_DATE_FORMAT
from ScrapyJobboleNew.models.models import Article
import re
import hashlib
from w3lib.html import remove_tags

class ScrapyjobbolenewItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

def get_md5(url):
    if isinstance(url,unicode):
        url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()

def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()

    return create_date


def get_nums(value):
    match_re = re.match(".*?(\d+).*", value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0

    return nums

def return_value(value):
    return value

##生成输入提示

from elasticsearch_dsl.connections import connections
# Define a default Elasticsearch client
es = connections.create_connection(Article._doc_type.using)
def gen_suggests(index,info_tuple):
    used_words = set()  ##去重  先来的建议为主
    suggests =[]
    for text,weigt in info_tuple:
        if text:   ###调用es的nanlyze接口分析字符串
            words = es.indices.analyze(index=index,analyzer="ik_max_word",params={'filter':['lowercase']},body=text)
            analyzed_words = set([r["token"] for r in words['tokens'] if len(r["token"])>1])  ##过滤单个次
            # new_words = analyzed_words-used_words
            new_words = analyzed_words.difference(used_words)
            used_words.update(new_words)
        else:
            new_words = set()
        if new_words:
            suggests.append({"input":list(new_words),"weight":weigt})
    return suggests


def remove_comment_tags(value):
    #去掉tag中提取的评论
    if u"评论" in value:
        return ""
    else:
        return value


class ArticleItemLoader(ItemLoader):
    # 自定义itemloader
    default_output_processor = TakeFirst()

class jobBoleArticleItem(scrapy.Item):
    title = scrapy.Field()
    create_date = scrapy.Field(
        input_processor=MapCompose(date_convert),
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
        output_processor=MapCompose(return_value)
    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    comment_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(",")
    )
    content = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into article(title, url, create_date, fav_nums, front_image_url,
            praise_nums, comment_nums, tags, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)
        """
        fron_image_url = ""
        content = remove_tags(self["content"])

        if self["front_image_url"]:
            fron_image_url = self["front_image_url"][0]
        params = [self["title"], self["url"], self["create_date"], self["fav_nums"],
                  fron_image_url, self["praise_nums"], self["comment_nums"],
                  self["tags"], self["content"]]
        return insert_sql, params

    def item_to_es(self):
        article = Article()
        article.title = self["title"]
        article.create_date = self["create_date"]
        article.content = remove_tags(self["content"])
        article.front_image_url = self["front_image_url"]
        article.front_image_path = self["front_image_path"]
        article.praise_nums = self["praise_nums"]
        article.comment_nums = self["comment_nums"]
        article.fav_nums = self["fav_nums"]
        article.url = self["url"]
        article.tags = self["tags"]
        article.meta.id = self["url_object_id"]
        article.suggest = gen_suggests(Article._doc_type.index,((article.title,10),(article.tags,7)))
        # article.suggest = [{"input":['dd'],"weight":4},{"input":['dd'],"weight":4}]

        article.save()
        return

