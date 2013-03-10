# -*- coding: utf-8 -*-
"""
Module containing functions to query Wikipedia API for various 
pieces of information along with functions to parse results.
"""
from xml.dom.minidom import parseString
import re
import urllib2
import xml.dom.minidom

ACTIVE_WIKIPEDIA_MIN = 100

# Could write these caches to file (currently not doing so). 
id_to_title_cache = {}
title_to_id_cache = {}
article_to_category_titles_cache = {}
title_to_page_text_cache = {} 


#################### 
# User and contribution related functions

def query_username_exists(username):
    """ Returns true if the given username is 
    registered on Wikipedia, false otherwise. """
    query = 'list=users&ususers='+username+'&usprop=editcount|registration&format=xml'
    exists_xml = __query_wiki__(query)
    dom = xml.dom.minidom.parseString(exists_xml)
    elmts = dom.getElementsByTagName('user')
    return (not elmts[0].hasAttribute('missing'))

def query_editors_of_recentchanges(desired_num_editors_to_fetch, recent_editors, active_users_only=True):
    """ Fetch the most recently edited pages on 
    Wikipedia and returns a set of unique usernames
    for the users who made those edits. 
    @param recent_editors: editors already cached 
    @param active_users_only: True if only want to return editors who have 
    made non-trivial edits on a minimum number of Wikipedia pages """
    
    print 'Querying Wikipedia for editors who recently made changes...'
    
    # only list certain types of changes
    rctype = ('&rctype='
    +'edit'  # user responsible for the edit and tags if they are an IP
    +'|new') # page creations)
    
    # only show items that meet certain criteria
    rcshow = ('&rcshow='
    +'!minor' # don't list minor edits
    +'|!bot' # don't list bot edits
    +'!anon') # only list edits by registered users
    
    # list additional pieces of info
    rcprop = ('&rcprop='
    +'user'  # user responsible for the edit and tags if they are an IP
    +'|userid' # user id responsible for the edit
    +'|flags' # flags for the edit
    +'|title' # page title of the edit
    +'|ids') # page ID, recent changes ID, and new and old revision ID
    
    # list newest changes first
    rcdir = ('&rcdir=older')
    
    count = 1
    rcstart = ''
    while len(recent_editors) < desired_num_editors_to_fetch:
        try:
            # can request up to 5000 but just doing 500 
            # unless even more usernames than that requested
            num_left_to_fetch = desired_num_editors_to_fetch - len(recent_editors)
            rclimit_val = max(500, num_left_to_fetch)
            rclimit = '&rclimit='+str(min(5000, rclimit_val))
            
            # query wiki for recent edits
            params = rclimit+rctype+rcshow+rcprop+rcdir+rcstart
            query = 'list=recentchanges'+params+'&format=xml'
            recent_edits_xml = __query_wiki__(query)
            
            # parse the results to get the users who made these edits
            users = __parse_wiki_xml__(recent_edits_xml, 'rc', 'user')
            for editor in users:
                
                if len(recent_editors) >= desired_num_editors_to_fetch:
                    break # fetched enough new active editors
                
                # just output some progress..
                if count%5==0:
                    print "Querying for recent editors... Encountered so far: "+str(count)+\
                    ". Mapped so far: "+str(len(recent_editors))
                count = count+1
                
                try:
                    if editor in recent_editors:
                        continue # already mapped this user
                    
                    if (str(editor).replace('.', '')).isdigit() :
                        continue # ignore IP addresses
                    
                    # get map of pages user edited -> number of times edited page
                    edits_map = query_usercontribs(editor, False)
                    
                    if active_users_only and (len(edits_map.keys())<ACTIVE_WIKIPEDIA_MIN):
                        # ignore editors that haven't made non-trivial 
                        # edits on the minimum number of pages
                        continue
                    
                    recent_editors.append(editor)
                except:
                    continue # ignore problematic editors
            
            query_continue = __wiki_xml_has_tag__(recent_edits_xml, 'query-continue')  
            if not query_continue:
                break
            next_changes = __parse_wiki_xml__(recent_edits_xml, 'recentchanges', 'rcstart')
            rcstart = '&rcstart='+next_changes[0]
        except Exception as e:
            print "Unexpected exception while querying for recent wikipedia edits ",e
            break

    return recent_editors

def query_username_SpecialRandom():
    """ Using a Special:Random/User query, returns a random 
    Wikipedia username or None if an unexpected error occurs. """
    try:
        rand_user_req_url = 'http://en.wikipedia.org/wiki/Special:Random/User'
        req = urllib2.Request(rand_user_req_url, headers={'User-Agent' : "Browser"})
        user_url_str = str(urllib2.urlopen(req).geturl())
        user_namespace = 'User:'
        pos = user_url_str.find(user_namespace)
        if pos==-1:
            return None
        
        username = user_url_str[pos+len(user_namespace):]
        extra_path = '/'
        extra_pos = username.find(extra_path)
        if extra_pos!=-1:
            username = username[0:extra_pos]
        return username
    except:
        return None

def query_usercontribs(username, fetch_all_contribs):
    """ Returns a mapping from page id -> number of times given user has edited that page.
    @param fetch_all_contribs: True if we want to fetch and return all pages edited by a 
    user, False if we only want to return ACTIVE_WIKIPEDIA_MIN number of edited pages. """
    page_to_numedits = {}
    
    # only consider editors who have made non trivial edits
    ucshow = '&ucshow=!minor' # ignore minor edits
    # and for now, only include pages in default namespace 
    # to filter out edits like file uploads or user talk
    # see http://wiki.case.edu/api.php?action=query&meta=siteinfo&siprop=general|namespaces
    ucnamespace = '&ucnamespace=0'
    # ignore revert edits to fix vandalism, typo correction
    # uctag = ! 'rv' 
    
    ucstart = ''
    while True:
        if not fetch_all_contribs and len(page_to_numedits)>=ACTIVE_WIKIPEDIA_MIN:
            # not fetching all user's edited pages so just 
            # fetch the minimum required to be considered active
            return page_to_numedits
        
        edits_query = 'list=usercontribs&ucuser='+username+'&uclimit=500'+ucnamespace+ucshow+'&format=xml'+ucstart
        user_edits_xml = __query_wiki__(edits_query)
        edited_pages = __parse_wiki_xml__(user_edits_xml, 'item', 'pageid', True)
        for page in edited_pages:
            try:
                if page in page_to_numedits.keys():
                    numedits = page_to_numedits[page]
                else:
                    numedits = 0
                page_to_numedits[page] = numedits+1
            except:
                continue
        
        query_continue = __wiki_xml_has_tag__(user_edits_xml, 'query-continue')  
        if not query_continue:
            break
        next_contribs = __parse_wiki_xml__(user_edits_xml, 'usercontribs', 'ucstart')
        ucstart = '&ucstart='+next_contribs[0]
    
    return page_to_numedits

def query_total_edits_siteinfo():
    """ Returns the total number of edits made on Wikipedia """
    stats_query = 'meta=siteinfo&siprop=statistics&format=xml'
    stats_xml = __query_wiki__(stats_query)
    edit_stat = __parse_wiki_xml__(stats_xml, 'statistics', 'edits')
    return edit_stat


#################### 
# Functions related to Wikipedia pages

__page_url_prefix__ = 'http://en.wikipedia.org/wiki/'
def get_wikipedia_page_url(page_title):
    """ Returns the full URL of the Wikipedia page with the given title """
    return __page_url_prefix__+str(page_title).replace(' ','_')

def get_page_title_from_url(page_url):
    """ Returns the page title of the Wikipedia page at the given URL """
    return page_url.replace(__page_url_prefix__, '').replace(' ','_')

def get_page_title(page_id):
    """ Returns the title of the Wikipedia page that has the given page id """
    if page_id in id_to_title_cache:
        # already retrieved and cached this page title previously
        return id_to_title_cache[page_id]
    try:
        info_query = 'prop=info&pageids='+str(page_id)+'&format=xml'
        page_info_xml = __query_wiki__(info_query)
        parsed_title = __parse_wiki_xml__(page_info_xml, 'page', 'title')
        title = parsed_title[0]
        id_to_title_cache[page_id] = title # add it to the cache
        return title
    except:
        return ''  
    
def get_page_id(page_title):
    """ Returns the ID of the Wikipedia page that has the given page title """
    if page_title in title_to_id_cache:
        # already retrieved and cached this page ID previously
        return title_to_id_cache[page_title] 
    try:
        info_query = 'prop=info&titles='+str(page_title).replace(' ', '_')+'&format=xml'
        page_info_xml = __query_wiki__(info_query)
        parsed_page_id = __parse_wiki_xml__(page_info_xml, 'page', 'pageid')
        page_id = parsed_page_id[0]
        title_to_id_cache[page_title] = page_id # add it to the cache
        return page_id
    except:
        return ''  
    
def query_page_revisions(page_id):
    """ Returns the total number of revisions ever made on the given page by anyone """
    total_num_edits = 0
    rvstart = ''
    while True:
        edits_query = 'prop=revisions&pageids='+str(page_id)+'&rvlimit=5000&format=xml'+str(rvstart)
        edits_xml = __query_wiki__(edits_query)
        edited_pages = __parse_wiki_xml__(edits_xml, 'rev', 'revid')
        total_num_edits = total_num_edits + len(edited_pages)
        
        query_continue = __wiki_xml_has_tag__(edits_xml, 'query-continue')  
        if not query_continue:
            break
        next_revisions = __parse_wiki_xml__(edits_xml, 'revisions', 'rvstartid')
        if len(next_revisions)==0:
            break
        rvstart = '&rvstartid='+next_revisions[0]
    
    return total_num_edits

def get_categories_of_res(res_title):
    """ Returns the IDs of the Wikipedia categories of the given Wikipedia resource. """
    res_title = res_title.replace(' ','_')
    if res_title in article_to_category_titles_cache:
        # already retrieved and cached this category previously
        return article_to_category_titles_cache[res_title] 
    clcontinue = ''
    while True:
        categories_query = 'titles='+res_title+'&prop=categories&clshow=!hidden&cllimit=max&format=xml'+clcontinue
        categories_xml = __query_wiki__(categories_query)
        categories = __parse_wiki_xml__(categories_xml, 'cl', 'title', True)
    
        # see if more categories
        query_continue = __wiki_xml_has_tag__(categories_xml, 'query-continue')  
        if not query_continue:
            break
        more_categories = __parse_wiki_xml__(categories_xml, 'categories', 'clcontinue')
        clcontinue = '&clcontinue='+more_categories[0]
    article_to_category_titles_cache[res_title] = categories # add it to the cache
    return categories


#################### 
# Functions related to text-based content of Wikipedia pages

def get_raw_page_text(page_title):
    """ Returns the unprocessed content on the Wikipedia page with the given title """
    try :
        if "#" in page_title:
            # ignore anchor tags (for example Microbrewery#Craft beer) and just get the main page title 
            page_title = page_title[:page_title.index("#")]
        if page_title in title_to_page_text_cache:
            # already retrieved and cached this page text previously
            return title_to_page_text_cache[page_title] # add it to the cache
        content_query = 'titles='+(str(page_title).replace(' ', '_'))+'&prop=revisions&rvprop=content&format=xml'
        content_xml = __query_wiki__(content_query)
        
        dom = parseString(content_xml)
        content = dom.getElementsByTagName('rev')[0].childNodes[0].data
        if "#REDIRECT" in content:
            # this is a direct page, so we need original page with the actual content
            orig_page_title = content[content.index('[[')+2:content.index(']]')]
            return get_raw_page_text(orig_page_title)
        
        return content
    
    except Exception as e:
        print "Problem retrieving page content of page "+str(page_title), e
        return ''

def clean_wikimarkup(content):
    """ Processes the given content in order to return cleaned 
    text with all wiki-specific headings and markup removed """
    
    # remove the pipes in inter-wiki links
    content = content.replace('|', ' ')
    
    # remove these sections. note the order in these lists
    # is important since some of these strings may be nested
    markups_to_remove = ["''", "'''", "[[", "]]", "=References=", 'Category:', '*#', '*', '[', ']', 
                         'ca:', 'de:', 'el:', 'es:', 'fr:', 'gl:', 'it:', 'he:', 'la:', 'ja:', 'no:', 
                         'pl:', 'pt:', 'fi:', 'sv:', 'uk:', 
                         'DEFAULTSORT:']
    chunks = [('{{About','}}'), ('{{Refimprove','}}'), ('{{Lead','}}'), ('{{Multiple issues','}}'), 
              ('{{cite','}}'), ('{{Citation','}}'), ('{{Reflist','}}'), ('{{DEFAULTSORT:','}}'), 
              ('==Bibliography==','='), # for now just take out the whole bibliography..
              ('File:','px') # images
              ]
    repeated_chunks = [('(pp.',')'), ('(p.',')')]
    content = __remove_markups__(content, markups_to_remove, chunks, repeated_chunks)
    
    # now remove any remaining braces
    content = __remove_markups__(content, ['{{', '}}', 'pp.', '==External links==', '==See also==', '=', '.jpg', '.png'], [], [])
    
    # remove digits like dates, numbers, pages, ISBN numbers, etc.
    content = ' '.join(word for word in content.split() 
                       if (not word.isdigit() and 
                           not word.replace('(', '').replace(')', '').isdigit()))
    
    # fix spaces before periods resulting from these removals
    content = content.replace(" . ", ". ")
    
    # use regex to remove some remaining digit strings
    content = re.sub(", \d+", "", content) # dates after cites, ie (Young, 2005) -> (Young)
    content = re.sub("(\d+)", "", content) # remove cites of just the date ie (2008)
    content = content.replace(" ()","").replace(" p. "," ").replace(", p.</ref>", ".</ref>")
    return content
def __remove_markups__(content, markups, chunks, repeated_chunks):
    for markup in markups:
        content = content.replace(markup,"")
    for (chunk_start,chunk_end) in chunks:
        content = __remove_chunk__(content, chunk_start, chunk_end)
    for (chunk_start,chunk_end) in repeated_chunks:
        # these may occur multiple times in the doc, 
        # so need to iterate to remove all occurrences
        while chunk_start in content:
            content = __remove_chunk__(content, chunk_start, chunk_end)
    return content
def __remove_chunk__(content, chunk_start, chunk_end):
    wikisection_start = content.find(chunk_start)
    after_chunkstart = wikisection_start+len(chunk_start)
    wikisection_end = after_chunkstart+content[after_chunkstart:].find(chunk_end)
    to_remove = content[wikisection_start:wikisection_end+len(chunk_end)]
    content = content.replace(to_remove, '')
    return content


#################### 
# Functions for querying Wikipedia and parsing the response 

def __query_wiki__(query) : 
    ''' Queries wikipedia to retrieve various data in xml format '''
    hosturl = 'http://en.wikipedia.org/'
    queryaction = 'w/api.php?action=query&'
    result = urllib2.urlopen(hosturl+queryaction+query).read()
    return result

def __parse_wiki_xml__(wiki_xml, tag_name, attribute, allow_duplicate_attr_vals=False) : 
    ''' Parses xml fetched from wikipedia to retrieve the 
    value of the given attribute within the given tag. '''
    try:
        dom = xml.dom.minidom.parseString(wiki_xml)
        elmts = dom.getElementsByTagName(tag_name)
    except:
        elmts = []

    attr_list = []
    for elmt in elmts : 
        try:
            if elmt.hasAttribute(attribute):
                attr = elmt.getAttribute(attribute)
                attr_list.append(attr)
        except:
            continue # ignore problematic elements
        
    if not allow_duplicate_attr_vals:
        attr_list = list(set(attr_list)) # remove duplicates
    return attr_list

def __wiki_xml_has_tag__(wiki_xml, tag_name):
    dom = xml.dom.minidom.parseString(wiki_xml)
    pages = dom.getElementsByTagName(tag_name)
    return len(pages) > 0
