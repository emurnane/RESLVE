# -*- coding: utf-8 -*-
"""
Computes content-based and category-based similarity scores between a
user's topics of interest and a candidate resource's corresponding topic.
"""

from collections import OrderedDict
from knowledge_context.content import text_processor
from knowledge_context.content.tfidf import TfIdf_Weight_Util
import math
import operator

def score_candidates(candidate_graphs, user_interest_graph):
    """ Compares each candidate to the user's interests and returns a sorted
    ranking of candidates with the most user-relevant candidate at position 1. """
    sim_scores = {}
    
    # compute content and category based measures of similarity
    sim_content_scores = sim_content(candidate_graphs, user_interest_graph)
    sim_category_scores = sim_category(candidate_graphs, user_interest_graph)
    
    # combine scores
    for candidate_title in candidate_graphs:
        sim_scores[candidate_title] = sim(candidate_title, sim_content_scores, sim_category_scores)
    
    # now sort them
    sorted_scores = OrderedDict(sorted(sim_scores.iteritems(), key=operator.itemgetter(1), reverse=True))
    return sorted_scores
        
def sim(candidate, sim_content_scores, sim_category_scores):
    """ A composite scoring function to get an overall measure
    of relevance of a candidate topic to a particular user. """
    alpha = 0.5
    sim = alpha*sim_content_scores[candidate] + (1-alpha)*sim_category_scores[candidate]
    return sim

def sim_content(candidate_graphs, user_interest_graph):
    """ Measures relevance between each candidate and the user's interests based on
    the similarity in the text-based descriptions of those candidates and interests. """
    sim_content_scores = {} # candidate title -> sim_content score

    # Make a single string built by concatenating the
    # description of each topic in which the user is interested
    user_query = ' '.join(user_interest_graph.get_topic_descriptions())
    user_query = text_processor.format_doc_for_sim_scoring(user_query)
    
    # Map candidate titles to the description of the corresponding topic
    candidate_title_to_desc = {}
    for candidate_title in candidate_graphs:
        candidate_graph = candidate_graphs[candidate_title]
        candidate_document = ' '.join(candidate_graph.get_topic_descriptions())
        candidate_document = text_processor.format_doc_for_sim_scoring(candidate_document)
        candidate_title_to_desc[candidate_title] = candidate_document
    
    # Create corpus of candidate docs
    tfidf_util = TfIdf_Weight_Util(candidate_title_to_desc.values())
    
    # Treat user model as query doc and compute 
    # similarity of each candidate to user's interests
    user_tfidfs = tfidf_util.compute_term_weights(user_query)
    for candidate_title in candidate_title_to_desc:
        candidate_doc = candidate_title_to_desc[candidate_title]
        cand_tfidfs = tfidf_util.compute_term_weights(candidate_doc)
        candidate_sim_content = compute_sim(user_tfidfs, cand_tfidfs)
        sim_content_scores[candidate_title] = candidate_sim_content
    return sim_content_scores
        
def sim_category(candidate_graphs, user_interest_graph):
    """ Measures relevance between each candidate and the user's interests based on
    those candidates' and interests' semantic relationships in the knowledge graph."""
    sim_category_scores = {}
    
    user_category_weights = user_interest_graph.get_category_weights()
    for candidate_title in candidate_graphs:
        candidate_topic_graph = candidate_graphs[candidate_title]
        candidate_category_weights = candidate_topic_graph.get_category_weights()
        
        candidate_sim_category = compute_sim(user_category_weights, candidate_category_weights)
        sim_category_scores[candidate_title] = candidate_sim_category
    return sim_category_scores

def compute_sim(user_weight_matrix, candidate_weight_matrix):
    """ Creates vectors for user and for candidate 
    and computes cosine similarity between them """
    
    # Copy so don't mutate the original data structures
    weight_matrix_user = user_weight_matrix.copy()
    weight_matrix_cand = candidate_weight_matrix.copy()
    
    # Make sure all items (terms or categories) in both vectors
    for cand_item in candidate_weight_matrix:
        if cand_item not in weight_matrix_user:
            weight_matrix_user[cand_item] = 0.0
    for user_item in user_weight_matrix:
        if user_item not in weight_matrix_cand:
            weight_matrix_cand[user_item] = 0.0    
            
    # Create weighted vectors
    user_vector = get_weighted_vector(weight_matrix_user)
    cand_vector = get_weighted_vector(weight_matrix_cand) 
    
    # Compute similarity between vectors
    return cos_sim(user_vector, cand_vector)

def get_weighted_vector(entry_weight_matrix):
    return [entry_score_tuple[1] for entry_score_tuple in sorted(entry_weight_matrix.items())]

def cos_sim(a,b):
    return __dot__(a,b) / (__norm__(a) * __norm__(b))
def __dot__(a,b):
    n = len(a)
    sum_val = 0
    for i in xrange(n):
        sum_val += a[i] * b[i];
    return sum_val
def __norm__(a):
    ''' Prevents division by 0'''
    n = len(a)
    sum_val = 0
    for i in xrange(n):
        sum_val += a[i] * a[i]
    if sum_val==0:
        sum_val=1 # prevent division by 0 in cosine sim calculation
    return math.sqrt(sum_val)
