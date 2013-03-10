# -*- coding: utf-8 -*-
"""
Interface used to represent a platform on the social web
"""

class Social_Web_Platform(object):
    def __init__(self, siteName):
        self.siteName = siteName
        self.active_posts_min = 100
        self.__init_authenticated_account__()

    def get_client(self):
        raise Exception("Interface method get_client() "+\
                        "must be implemented by subclasses") 
                
    def __init_authenticated_account__(self):
        raise Exception("Interface method __init_authenticated_account__() "+\
                        "must be implemented by subclasses")
    
    def clean_text(self, text):
        raise Exception("Interface method clean_text(text) "+\
                        "must be implemented by subclasses")
    
    def userlookup(self, usernames, num_lookups_desired, min_number_of_posts, **api_args):
        raise Exception("Interface method userlookup(...) "+\
                        "must be implemented by subclasses")
