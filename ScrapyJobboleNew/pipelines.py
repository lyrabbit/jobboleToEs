# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.pipelines.images import ImagesPipeline
import codecs
import json
import sys
import MySQLdb
import MySQLdb.cursors
from twisted.enterprise import adbapi
from scrapy.exporters import JsonItemExporter

reload(sys)
sys.setdefaultencoding('utf-8')

class ScrapyjobbolenewPipeline(object):
    def process_item(self, item, spider):
        return item

class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        for key ,value in results:
            front_image_path = value["path"]
        item['front_image_path'] = front_image_path.decode("utf-8")
        return item

##将需要存储的值转换为json格式的数据
class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open('article.json','w',encoding='utf-8')

    def process_item(self,item,spider):
        lines = json.dumps(dict(item),ensure_ascii=False) + "\n"
        self.file.write(lines,encoding='utf-8')
        return item

    def spider_closed(self,spider):
        self.file.close()

#同步写入到数据库
class MysqlPipeline(object):
    def __init__(self):
        self.conn = MySQLdb.connect(host="127.0.0.1",user="root",passwd="123456",db="jobbole",use_unicode=True,charset="utf8")
        self.cursor = self.conn.cursor()

    def process_item(self ,item,spider):
        insert = """
            insert into article(title, url, create_date, fav_nums)
            VALUES (%s, %s, %s, %s)
        """
        self.cursor.execute(insert,(item['title'],item['url'],item['create_date'],item['content']))
        self.conn.commit()
        return item

####异步方式存储数据
class MysqlTwistedPipeline(object):
    def __init__(self,dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls,settings):
        dbparms = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWORD"],
            charset = 'utf8',
            cursorclass = MySQLdb.cursors.DictCursor,
            use_unicode = True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb",**dbparms)
        return cls(dbpool)

    def process_item(self,item,spider):
        #使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert,item)
        query.addErrback(self.handle_error,item,spider)
        return item

    def handle_error(self,failure,item,spider):
        print failure

    def do_insert(self ,cursor,item):
        #执行具体的插入
        #根据不同的item 构建不同的sql语句并插入到mysql中
        insert_sql, params = item.get_insert_sql()
        # print (insert_sql, params)
        cursor.execute(insert_sql, params)

class ElasticsearchPipeline(object):
    def process_item(self,item,spider):
        item.item_to_es()
        return item


