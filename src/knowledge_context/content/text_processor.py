# -*- coding: utf-8 -*-
""" 
Utility methods to process and format text. 
"""

from nltk.corpus import stopwords, wordnet
from nltk.tokenize.punkt import PunktSentenceTokenizer
from nltk.tokenize.regexp import WordPunctTokenizer
import nltk
import re
import string

def format_doc_for_sim_scoring(raw_doc):
    """ Tokenizes and filters/formats the words in the given document to be used during 
    similarity measurement. This method should be used both when a doc goes into the  
    corpus and when a doc is being compared to another doc for similarity. 
    @return: a list of tokens """
    stopset = set(stopwords.words('english'))
    stemmer = nltk.PorterStemmer()
    tokens = WordPunctTokenizer().tokenize(raw_doc)
    non_punct = [''.join(ch for ch in token if not ch in string.punctuation) 
                    for token in tokens] # remove tokens that are purely punctuation
    clean_tokens = [token.lower() for token in non_punct 
                    if token.lower() not in stopset and len(token) > 2]
    stemmed_tokens = [stemmer.stem(word) for word in clean_tokens]
    return ' '.join(stemmed_tokens).decode('latin-1')

def format_text_for_NER(raw_text, social_web_platform=None):
    """ Prepares the given text for named entity extraction. Minimal 
    processing performed in order to remove line breaks, links, etc
    rather than more substantial formatting like porting or stemming that
    would interfere with a NER toolkit's ability to recognize entities. """
    
    ''' remove line breaks '''
    cleaned_text = raw_text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') 
    
    ''' remove html '''
    cleaned_text = nltk.clean_html(cleaned_text)
    
    ''' remove links (www.* or http*) '''
    cleaned_text = re.sub('((www\.[\s]+)|(https?://[^\s]+))','', cleaned_text)
    
    ''' replace double quotes with single quotes to avoid a Wikipedia Miner error '''
    cleaned_text = cleaned_text.replace("\"", "\'")

    ''' remove non-printable characters '''
    cleaned_text = filter(lambda x: x in string.printable, cleaned_text) 
    
    ''' clean any social web platform specific text '''
    if social_web_platform != None:
        cleaned_text = social_web_platform.clean_text(cleaned_text)
    
    ''' remove misc. remnant strings we don't care about '''
    words_manually_filter = []
    cleaned_text = ' '.join([word for word in cleaned_text.split() 
                             if not word in words_manually_filter])
    
    return cleaned_text

def get_nouns(raw_text, site):
    """ Returns a list of all the nouns or noun phrases found in the given text. """
    nouns = []
    try:
        cleaned_text = format_text_for_NER(raw_text, site)
        text_tokens = WordPunctTokenizer().tokenize(cleaned_text)
        for token_and_POS in nltk.pos_tag(text_tokens):
            try:
                POS = token_and_POS[1]
                if 'NN'==POS or 'NNS'==POS or 'NNP'==POS or 'NNPS'==POS or 'NP'==POS:
                    nouns.append(token_and_POS[0])
            except:
                continue
    except: 
        return nouns
    return nouns

def get_sentences(text):
    """ Returns a list of the sentences in the given text """
    sentences = PunktSentenceTokenizer().tokenize(text)
    return sentences

def is_english(raw_text, site):
    """ Returns true if the given text contains 
    more English words than non-English words. 
    (Not requiring _all_ words to be English in order to allow for some 
    misspellings, slang, etc that wouldn't be recognized as English). """
    num_english = 0
    num_nonenglish = 0
    cleaned_text1 = format_text_for_NER(raw_text, site)
    cleaned_text2 = format_doc_for_sim_scoring(cleaned_text1)
    for word in cleaned_text2.split():
        if wordnet.synsets(word):
            num_english = num_english+1
        else:
            num_nonenglish = num_nonenglish+1
    prop_nonenglish = float(num_nonenglish)/float(num_english+num_nonenglish)
    return (prop_nonenglish<.75)