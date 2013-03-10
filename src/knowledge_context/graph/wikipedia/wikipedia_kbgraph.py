# -*- coding: utf-8 -*-
"""
Implements the knowledge graph using Wikipedia.
"""

from knowledge_context.graph.abstract_kbgraph import KnowledgeGraph
from knowledge_context.graph.abstract_kbnode import TopicNode, CategoryNode
from knowledge_context.graph.wikipedia import wikipedia_api_util
import WikiExtractor

class WikipediaKnowledgeGraph(KnowledgeGraph):
    """ In Wikipedia, an article represents a topic """
    
    def construct_topic_node(self, topic_title, description):
        return WikipediaTopicNode(topic_title, description)
    
    def construct_category_node(self, category_title):
        return WikipediaCategoryNode(category_title)
    
    def get_kb_description(self, topic_title):
        raw_content = wikipedia_api_util.get_raw_page_text(topic_title)
        cleaned = WikiExtractor.clean(raw_content)
        compacted = WikiExtractor.compact(cleaned)
        desc = ' '.join(compacted)
        if desc is None or desc.strip()=='':
            return topic_title
        return desc
    
    def get_kb_categories(self, title):
        return wikipedia_api_util.get_categories_of_res(title)
    
    def get_kb_user_interests(self, username):
        """ Returns a list of titles of articles in which the given user 
        has shown interest (i.e. has made at least one non-trivial edit). """
        article_to_editnum = wikipedia_api_util.query_usercontribs(username, True)
        article_titles = [wikipedia_api_util.get_page_title(article_id) 
                          for article_id in article_to_editnum]
        return article_titles
    
class WikipediaTopicNode(TopicNode):
    def __init__(self, topic_title, description):
        TopicNode.__init__(self, topic_title, description)
        
class WikipediaCategoryNode(CategoryNode):
    def __init__(self, category_title):
        CategoryNode.__init__(self, category_title)
