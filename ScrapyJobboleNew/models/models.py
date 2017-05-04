#coding:utf-8

from datetime import datetime
from elasticsearch_dsl import DocType, Date, Integer, Keyword, Text
from elasticsearch_dsl.connections import connections


# Define a default Elasticsearch client
connections.create_connection(hosts=['localhost'])
from elasticsearch_dsl import Completion
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}

ik_analyzer = CustomAnalyzer('ik_max_word',filter=['lowercase'])

class Article(DocType):
    suggest = Completion(analyzer=ik_analyzer, search_analyzer=ik_analyzer)
    title = Text(analyzer='ik_max_word', search_analyzer="ik_max_word", fields={'title': Keyword()})
    id = Text()
    url = Text()
    front_image_url = Text()
    front_image_path = Text()
    create_date = Date()
    praise_nums = Integer()
    comment_nums = Integer()
    fav_nums = Integer()
    tags = Text(analyzer='ik_max_word', fields={'tags': Keyword()})
    content = Text(analyzer='ik_max_word')
    class Meta:
        index = 'search',
        doc_type = 'article'

if __name__ == '__main__':
    Article.init()
