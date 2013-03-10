# -*- coding: utf-8 -*-
"""
A node represents a piece of information found in a knowledge 
base about a topic or its categorical organization scheme.
"""

class KnowledgeGraphNode:
    """ A node in a knowledge graph has a unique identifier
    and can be a topic node or a category node. """
    
    def __init__(self, title):
        self.title = title
    
    def get_id(self):
        """ Returns this node's unique identifier (its title) """
        return self.title
    
class TopicNode(KnowledgeGraphNode):
    """ A topic node has a unique identifier, belongs to one 
    or more categories, and carries a textual description. """
    
    def __init__(self, topic_title, description):
        """ @param topic_title: The unique identifier of this topic node.
            @param desc: The description associated with this topic."""
        KnowledgeGraphNode.__init__(self, topic_title)
        self.description = description
        
    def get_description(self):
        """ Returns the textual description associated with this topic """
        return self.description
    
class CategoryNode(KnowledgeGraphNode):
    """ A category node has a unique identifier and a set of 
        semantic relationships with other nodes (incoming rels from 
        topics and sub-categories; outgoing to super-categories). """
        
    def __init__(self, category_title):
        """ @param category_title: The unique identifier of this category node. """
        KnowledgeGraphNode.__init__(self, category_title)
        self.freq = 1
        self.dist = 1
        
    def increment_freq(self):
        self.freq = self.freq+1
        
    def increment_dist(self):
        self.dist = self.dist+1
        
    def get_freq(self):
        return self.freq
    
    def get_dist(self):
        return self.dist
        
    def get_inverse_distance(self):
        """ Returns 1/p, the inverse path distance between this 
        category and the topic node to which it is connected by an edge. 
        The larger this inverse distance value returned, the greater
        the semantic relevance between the topic and category. """
        return float(1/self.dist)
    
    def get_weight(self):
        return float(self.freq*self.dist)
