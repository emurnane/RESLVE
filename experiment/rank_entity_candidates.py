# -*- coding: utf-8 -*-
from knowledge_context import similarity
from knowledge_context.graph.wikipedia.wikipedia_kbgraph import \
    WikipediaKnowledgeGraph
from nltk.compat import defaultdict
import csv_util

def run():
    
    usernames = get_bridged_usernames()
        
    resolved_entities = get_resolved_ambiguous_entities()
    for entity_id in resolved_entities:
        entity_obj = resolved_entities[entity_id]
        
        # Interest model of a user is simply an aggregated set of all
        # topic-interest graphs built from each topic the user has shown
        # interest in (i.e., has edited)
        username = usernames[entity_obj.userkey]
        user_graph = build_user_interest_graph(username)
        
        # Get set of all topic graphs built from each topic 
        # that corresponds to a candidate meaning of the entity
        candidate_graphs = build_candidate_graphs(entity_obj)
        
        # RESLVE ranked candidates
        similarity.score_candidates(candidate_graphs, user_graph)

def get_bridged_usernames():
        usernames = {}
        userhashes = csv_util.query_csv_for_rows('labeled_data/user_privacy/anonymized_userhash.csv')
        for (userkey, username) in userhashes:
            usernames[userkey] = username
              
def get_resolved_ambiguous_entities():
    ''' Returns the ambiguous entities for which the intended 
    meaning has been unanimously resolved by human annotators. '''
    
    all_entities = defaultdict(list)
    correct_meaning_label = 'Y'
    
    row_count = -1
    labeled_entities_dataset = csv_util.query_csv_for_rows('labeled_data/entities.csv', False)
    for candidate_row in labeled_entities_dataset:
        row_count = row_count+1
        if row_count==0:
            # header row
            surfaceform_col = candidate_row.index('surface_form')
            shorttext_col = candidate_row.index('short_text')
            
            candidate_meaning_col = candidate_row.index('candidate_meaning')
            candidate_label_col = candidate_row.index('candidate_is_relevant')
            
            userkey_col = candidate_row.index('user_key')
            continue
        
        # use "surfaceform_shorttext" as ID for entity
        surfaceform = candidate_row[surfaceform_col]
        shorttext = candidate_row[shorttext_col]
        entity_id = surfaceform+'_'+shorttext
        
        meaning = candidate_row[candidate_meaning_col]
        label = candidate_row[candidate_label_col] 
        userkey = candidate_row[userkey_col]
        all_entities[entity_id].append((meaning, label, surfaceform, shorttext, userkey))
        
    # test if entity is ambiguous (i.e., has more than one candidate meaning) and
    # if so if entity has been resolved (i.e., has at least one candidate labeled
    # as the intended meaning)
    resolved_entities = {}
    for entity in all_entities:
        entity_tuple_list = all_entities[entity]
        if len(entity_tuple_list) < 2:
            continue 
        
        candidate_meanings = []
        intended_meanings = []
        user = None
        for (meaning, label, surfaceform, shorttext, userkey) in entity_tuple_list:
            
            # title of a potential meaning of the ambiguous entity
            if not meaning in candidate_meanings:
                candidate_meanings.append(meaning)
            
            # annotated label indicating whether this candidate 
            # meaning is the intended meaning of the entity
            if label==correct_meaning_label and not meaning in intended_meanings:
                intended_meanings.append(meaning)
            
            if user is None:
                user = userkey
        if len(intended_meanings)>1 and len(intended_meanings)>0 and user!=None:
            # this entity is ambiguous, has been manually resolved, 
            # and we know the user who wrote it
            entity_obj = ResolvedEntity(candidate_meanings, intended_meanings, surfaceform, shorttext, user)
            entity_id = entity_obj.get_id()
            resolved_entities[entity_id] = entity_obj
    return resolved_entities

class ResolvedEntity:
    def __init__(self, candidate_meanings, intended_meanings, surfaceform, shorttext, userkey):
        self.candidate_meanings = candidate_meanings
        self.intended_meanings = intended_meanings
        
        self.surfaceform = surfaceform
        self.shorttext = shorttext
        self.userkey = userkey
        
    def get_id(self):
        return self.surfaceform+'_'+self.shorttext
    
def build_user_interest_graph(username):
    """ Builds a topic-interest graph for a user whose identity 
    was successfully bridged between the social Web and Wikipedia """
    return WikipediaKnowledgeGraph(username=username)

def build_candidate_graphs(entity):
    ''' Builds topic graphs for an ambiguous enity's multiple candidate meanings.
        @param entity: an Entity object '''    
    candidate_graphs = {}
    for candidate_title in entity.candidate_meanings:
        candidate_graph = WikipediaKnowledgeGraph(topic_titles=[candidate_title])
        candidate_graphs[candidate_title] = candidate_graph
    return candidate_graphs
    
if __name__=='__main__':
    run()