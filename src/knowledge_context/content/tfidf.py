# -*- coding: utf-8 -*-
""" 
A utility class to handle computing tf-idf values for text documents. 
"""

from nltk.probability import FreqDist
import math

class TfIdf_Weight_Util:
    def __init__(self, corpus_docs):
        self.num_docs = 0
        self.term_to_num_docs = {}
        
        self.idf_cache = {}
        self.idf_default = 1.5
        
        for doc in corpus_docs:
            # store the total number of docs in the corpus
            self.num_docs += 1
            
            # map each term in the corpus to the number of docs that contain it
            terms = doc.split()
            unique_terms = set(terms)
            for term in unique_terms:
                if term in self.term_to_num_docs:
                    num_docs_with_term = self.term_to_num_docs[term]
                else:
                    num_docs_with_term = 0
                self.term_to_num_docs[term] = num_docs_with_term+1
                
    def compute_term_weights(self, doc):
        """ Computes tf-idf for each term in the given document """
        term_tfidfs = {}
        terms = doc.split()
        unique_terms = set(terms)
        for term in unique_terms:
            term_tf = self.__compute_tf__(term, terms)
            term_idf = self.__compute_idf__(term)
            term_tfidfs[term] = term_tf * term_idf
        return term_tfidfs
    
    def __compute_tf__(self, term, doc_terms):
        """ Computes the normalized frequency of term t in document d, which 
        is the number of times t occurs in d divided by the maximum number 
        of times any term occurs in d: tf(t,d) = f(t,d) / max{f(w,d)} """
        fdist = FreqDist(term.lower() for term in doc_terms)
        max_freq = doc_terms.count(fdist.max())
        if max_freq==0:
            return 0.0
        return float(doc_terms.count(term)) / max_freq
    
    def __compute_idf__(self, term):
        """ Computes the inverse document frequency of term t as
        the logarithm of the total number of documents in the corpus 
        divided by the number of documents containing t (docs where
        tf_t is not 0): idf(t) = log (N / df(t)) """
        
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        if not term in self.term_to_num_docs:
            return self.idf_default
        
        # A tf-idf calculation involves multiplying against a tf value less 
        # than 0, so we add 1 in order to return an idf value greater than 
        # 1 for consistent scoring. (Otherwise we'd be multiplying two values 
        # less than 1 and getting a value less than each of them).
        num_docs_with_term = self.term_to_num_docs[term]
        term_idf = 1.0 + math.log(float(self.num_docs)/num_docs_with_term)
        self.idf_cache[term] = term_idf
        return term_idf