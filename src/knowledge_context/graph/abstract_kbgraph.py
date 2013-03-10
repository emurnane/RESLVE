# -*- coding: utf-8 -*-
"""
A representation of the semantic network of structured information 
found in a knowledge base that is used to organize entities and the 
relations among them. 
"""

from knowledge_context.graph.abstract_kbnode import CategoryNode
from networkx.classes.graph import Graph

class KnowledgeGraph(Graph):
    
    """
    Interface methods that need to be implemented by subclasses of KnowledgeGraph:
    def get_kb_user_interests(username) returns a list of titles 
        for topics in which the given user has shown interest.
    def get_kb_description(topic_title) returns a string 
        description of the given topic.
    def get_kb_categories(title) returns a list of titles 
        of categories that contain the given title.
    """
    
    def __init__(self, topic_titles=None, username=None):
        """ Constructs a knowledge graph from a list of topic titles. 
        
        Instead of passing topic titles, a username may be passed; and 
        that user's interests will be determined in terms of topic titles, 
        which will be used to construct a knowledge graph. 
        
        If both topic titles and a username are given, the username will
        be ignored, and a knowledge graph will be constructed from the passed
        topic titles; if neither are given, an exception will be thrown. """
        
        if topic_titles==None and username==None:
            raise Exception("Must provide either username and topic titles "+\
                            "from which to build knowledge graph.")
        if topic_titles==None:
            topic_titles = self.get_kb_user_interests(username)

        self.topic_nodes = {} # topic title -> TopicNode instance
        self.category_nodes = {} # category title -> CategoryNode instance
        
        # The maximum path length that should exist between any two nodes in this graph
        self.__path_length_threshold__ = 1
        
        for topic_title in topic_titles:
            
            # construct topic nodes in graph
            topic_description = self.get_kb_description(topic_title)
            topic_node = self.construct_topic_node(topic_title, topic_description)
            self.topic_nodes[topic_title] = topic_node
            
            # construct nodes for super categories originating from this
            # topic, out to a threshold distance away for efficiency's sake
            self.__construct_category_nodes__(topic_node)
            
    def get_topic_titles(self):
        """ Returns a list containing the title of each topic in this graph. """
        return self.topic_nodes.keys()
    
    def get_topic_descriptions(self):
        """ Returns a list containing the description of each topic in this graph. """
        return [self.topic_nodes[topic_title].get_description() 
                for topic_title in self.topic_nodes]
    
    def get_category_weights(self):
        """ Returns a mapping of title to weight for each category in this graph. """
        category_weights = {}
        for category_title in self.category_nodes:
            category_node = self.category_nodes[category_title]
            category_weights[category_title] = category_node.get_weight()
        return category_weights
    
    def __construct_category_nodes__(self, src_node):    
        """ Recursively add parent categories of given
        src node until reach path length threshold."""   
        
        src_title = src_node.get_id()
        parent_categories = self.get_kb_categories(src_title)
        for category_title in parent_categories:
            
            if category_title in self.category_nodes:
                # category already in graph, so increase  
                # its frequency by 1 and continue
                category_node = self.category_nodes[category_title]
                category_node.increment_freq()
                continue
                
            # create category node and add it to graph
            category_node = self.construct_category_node(category_title)
            self.category_nodes[category_title] = category_node
            
            # want bipartite graph (no category-category edges), so 
            # apply transformation if src node is a category node
            if isinstance(src_node,CategoryNode):
                # distance from topic node to this category is one
                # greater than the path that already exists from the 
                # topic node to the source of this category-category edge
                category_node.increment_dist()
                
            path_length = category_node.get_dist()
            if path_length < self.__path_length_threshold__:
                # continue traversing through parent categories
                # until reach maximum path length threshold
                self.__construct_category_nodes__(category_node)    
