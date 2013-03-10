# -*- coding: utf-8 -*-
"""
Finds named entities (Wikipedia resources) in a given full text string.

Specifically, uses DBPedia Spotlight candidates interface 
(http://dbpedia.org/spotlight) as well as Wikipedia Miner services 
(http://wikipedia-miner.cms.waikato.ac.nz) to identify possible 
DBPedia entities for a given input string.

@author: Bernhard Haslhofer
@author: Elizabeth Murnane
"""

from entity_recognition.timeout import timeout
from knowledge_context.content import text_processor
from urllib2 import Request, urlopen, URLError, HTTPError
import errno
import json
import os
import urllib

DBPEDIA_SPOTLIGHT_URI = \
    "http://spotlight.dbpedia.org/rest/candidates?text="
WIKIPEDIA_MINER_SEARCH_SERVICE_URI = \
    "http://wikipedia-miner.cms.waikato.ac.nz/services/search?"
WIKIPEDIA_MINER_WIKIFY_SERVICE_URI = \
    "http://samos.mminf.univie.ac.at:8080/wikipediaminer/services/wikify?"
    
SERVICE_WikipediaMiner = 'wikipedia_miner_algorithm'
SERVICE_DbpediaSpotlight = 'dbpedia_spotlight_algorithm'
    
@timeout(180, os.strerror(errno.ETIMEDOUT))
def find_and_construct_named_entities(shorttext_id, original_shorttext, 
                                      username, social_web_platform=None):
    # use Wikipedia Miner and DBPedia Spotlight to detect
    # named entities and their candidate resources
    detected_entities = []
    clean_shorttext = text_processor.format_text_for_NER(original_shorttext, 
                                                         social_web_platform)
    try:
        sf_to_candidates_wikiminer = find_candidates_wikipedia_miner(clean_shorttext)
    except:
        sf_to_candidates_wikiminer = {}
    try:
        sf_to_candidates_dbpedia = find_candidates_dbpedia(clean_shorttext)
    except:
        sf_to_candidates_dbpedia = {}
    
    all_detected_surface_forms = set(sf_to_candidates_wikiminer.keys()).union(sf_to_candidates_dbpedia.keys())
    
    # now construct a DetectedEntity object for each detected surface form
    for surface_form in all_detected_surface_forms:
        detected_entity = DetectedEntity(surface_form,
                                         shorttext_id, original_shorttext,
                                         username, social_web_platform)    
        
        # set the DetectedEntity's baseline candidate rankings 
        if surface_form in sf_to_candidates_wikiminer:
            detected_entity.set_wikipedia_miner_ranking(sf_to_candidates_wikiminer[surface_form])
        if surface_form in sf_to_candidates_dbpedia:
            detected_entity.set_dbpedia_spotlight_ranking(sf_to_candidates_dbpedia[surface_form])
    
        detected_entities.append(detected_entity)
    return detected_entities
    
def find_named_entities_wikipedia_miner(text):
    """Finds named entities in a given text using Wikipedia Miner"""
    
    request_uri = WIKIPEDIA_MINER_WIKIFY_SERVICE_URI + "source=" + urllib.quote(text)
    request_uri += "&sourceMode=auto"
    request_uri += "&responseFormat=json"
    request_uri += "&disambiguationPolicy=loose"
    request_uri += "&minProbability=0"
    
    request = Request(request_uri)
    
    try:
        response = urlopen(request)
    except HTTPError, e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError, e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
        
    result = json.loads(response.read())
    
    detected_entities = []
    for topic in result['detectedTopics']:
        article_id = topic['id']
        title = topic['title']
        weight = topic['weight']
        dbpedia_uri = "http://dbpedia.org/resource/" + title.replace(" ", "_")
        entity = {'article_id': article_id, 'title': title, 'weight': weight,
                        'dbpedia_uri': dbpedia_uri}
        detected_entities.append(entity)
    return detected_entities

def find_candidates_wikipedia_miner(text, prior_and_context_scores={}):
    """ Finds all named entities in the given text using Wikipedia Miner and 
    returns a mapping of each named entity's surface form -> candidate resources.
    
    An empty dict is returned if no entities are found. Entities for 
    which no candidate resources are found are not included in the map. """
    
    surface_form_to_candidates = {}
    result = query_wikipedia_miner_for_candidates(text)
    if not 'labels' in result:
        print "WIKIPEDIA MINER CANNOT HANDLE TEXT: "+str(text)
        return surface_form_to_candidates
    for entity_result in result['labels']:
        surface_form = entity_result['text'].lower()
        
        # handle multiple mentions of the same entity
        try:
            candidates = surface_form_to_candidates[surface_form]
        except:
            candidates = {} # candidate title -> candidate data
            
        # store prior and context score in case caller needs it
        # (in particular, RESLVE hybrid algorithm needs these scores)
        candidates_to_prior_and_context = {}
        prior_and_context_scores[surface_form] = candidates_to_prior_and_context
            
        for sense in entity_result['senses']:
            sense_title = sense['title'].replace(" ", "_")
            
            # cache the prior and context scores
            prior_score = sense['priorProbability']
            weight_score = sense['weight']
            context_score = __calculate_relatedness__(prior_score, weight_score)
            candidates_to_prior_and_context[sense_title] = (prior_score, context_score)
            
            if sense_title in candidates:
                # already mapped entity to this candidate (must be the second 
                # mention of the same entity, and both mentions share this candidate)
                continue
            
            sense_dbpedia_uri = "http://dbpedia.org/resource/"+sense_title
            sense_score = weight_score
            
            cand_meaning = CandidateMeaning(sense_title, sense_dbpedia_uri, 
                                            (SERVICE_WikipediaMiner, sense_score))
            candidates[sense_title] = cand_meaning
            
        if len(candidates)>0: # ignore entities that have no candidates
            surface_form_to_candidates[surface_form] = candidates 
    return surface_form_to_candidates
def __calculate_relatedness__(commoness, weight):
    ''' float weight = (commoness + (3*relatedness))/4 
    (See Wikiminer's SearchService.java weightCombo() for the formula) '''
    relatedness = (weight*4 - commoness)/3
    return relatedness
    
def find_candidates_dbpedia(text, prior_and_context_scores={}):
    """ Finds all named entities in the given text using DBPedia Spotlight and 
    returns a mapping of each named entity's surface form -> candidate resources.
    
    An empty dict is returned if no entities are found. Entities for 
    which no candidate resources are found are not included in the map. """
    
    surface_form_to_candidates = {}
    result = query_dbpedia_spotlight_for_candidates(text)
    surface_form_list = result['annotation']['surfaceForm']
    if isinstance(surface_form_list, dict):
        # for short text with a single detected entity, DBPedia Spotlight 
        # just returns that one entity's dict rather than a list containing 
        # it, so we need to put it in a list ourselves
        surface_form_list = [surface_form_list]
    for entity_result in surface_form_list:    
        surface_form = entity_result['@name'].lower()
        
        # handle multiple mentions of the same entity
        try:
            candidates = surface_form_to_candidates[surface_form]
        except:
            candidates = {} # candidate title -> candidate data
            
        # skip entities with no candidates, which will not have the 'resource' key
        if not 'resource' in entity_result:
            continue
        
        # store prior and context score in case caller needs it
        # (in particular, RESLVE hybrid algorithm needs these scores)
        candidates_to_prior_and_context = {}
        prior_and_context_scores[surface_form] = candidates_to_prior_and_context
        
        result_res_list = entity_result['resource']
        if isinstance(result_res_list, dict):
            # for n.e. with a single candidate, DBPedia Spotlight just returns 
            # that one candidate's dict rather than a list containing it, so we 
            # need to put it in a list ourselves
            result_res_list = [result_res_list]
        for res in result_res_list:
            res_title = res['@label'].replace(" ", "_")
            
            # cache the prior and context scores
            candidates_to_prior_and_context[res_title] = (res['@priorScore'], 
                                                          res['@contextualScore'])
            
            if res_title in candidates:
                # already mapped entity to this candidate (must be the second 
                # mention of the same entity, and both mentions share this candidate)
                continue
            
            res_dbpedia_uri = "http://dbpedia.org/resource/"+res_title
            res_score = res['@finalScore']

            cand_meaning = CandidateMeaning(res_title, res_dbpedia_uri, 
                                            (SERVICE_DbpediaSpotlight, res_score))
            candidates[res_title] = cand_meaning
        
        if len(candidates)>0: # ignore entities that have no candidates
            surface_form_to_candidates[surface_form] = candidates
    return surface_form_to_candidates

def query_wikipedia_miner_for_candidates(text):   
    ''' Queries Wikipedia Miner's Search service 
    service and returns the server's JSON response '''

    request_uri = WIKIPEDIA_MINER_SEARCH_SERVICE_URI + "query=" + urllib.quote(text)
    request_uri += "&complex=true"
    request_uri += "&minPriorProbability=0"
    request_uri += "&responseFormat=json"
    
    request = Request(request_uri)
    try:
        print "Querying Wikipedia Miner for named entities and candidate resources..."
        response = urlopen(request)
    except HTTPError, e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        return
    except URLError, e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
        return
    result = json.loads(response.read())
    return result

def query_dbpedia_spotlight_for_candidates(text):
    ''' Queries DBPedia Spotlight's candidates service 
    service and returns the server's JSON response '''
    
    request_uri = DBPEDIA_SPOTLIGHT_URI + urllib.quote(text)
    request_uri += "&confidence=0"
    request_uri += "&support=0"
    
    request = Request(request_uri)
    request.add_header("Accept", "application/json")
    try:
        print "Querying DBPedia Spotlight for named entities and candidate resources..."
        response = urlopen(request)
    except HTTPError, e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError, e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    result = response.read()
    result = json.loads(result)
    return result

class DetectedEntity:
    """ Represents a named entity detected in a short text. """
    def __init__(self, surface_form,
                 shorttext_id, shorttext_str,
                 username, social_web_platform):
        """
        @param surface_form: the surface form of the named entity this object represents
        @param shorttext_id: the ID of the short text that contains this entity
        @param shorttext_str: the string of the short text that contains this entity
        @param username: the username who authored the short text containing this entity
        @param social_web_platform: the site on which the short text containing this entity was posted
        """
        self.surface_form = surface_form
        self.shorttext_id = shorttext_id
        self.shorttext_str = shorttext_str
        self.username = username
        self.social_web_platform = social_web_platform
        
        # Initialize the baseline candidate rankings, which each be a mapping 
        # from a candidate resource's title to its CandidateMeaning object
        self.wikipedia_miner_ranking = {}
        self.dbpedia_spotlight_ranking = {}
    
    def set_wikipedia_miner_ranking(self, wikipedia_miner_ranking):
        """ @param wikipedia_miner_ranking: a ranking of candidate 
        meanings according to Wikipedia Miner, which should be a dict 
        of candidate resource title to CandidateMeaning object """
        self.wikipedia_miner_ranking = wikipedia_miner_ranking
        
    def set_dbpedia_spotlight_ranking(self, dbpedia_spotlight_ranking):
        """ @param dbpedia_spotlight_ranking: a ranking of candidate 
        meanings according to DBPedia Spotlight, which should be a dict 
        of candidate resource title to CandidateMeaning object  """
        self.dbpedia_spotlight_ranking = dbpedia_spotlight_ranking

class CandidateMeaning:
    """ Represents a candidate topic to which an ambiguous named entity may refer. """
        
    def __init__(self, title, dbpedia_URI, service_score):
        """
        @param title: The title of this candidate's Wikipedia/DBPedia page (same thing) 
        @param dbpedia_URI: The URI of this candidate's DBPedia resource page
        @param service_score: A tuple of (service, float_score) where service is an
        identifier of the NER service that calculated and returned the float score.
        """
        self.title = title
        self.dbpedia_URI = dbpedia_URI
        self.service_score = service_score
