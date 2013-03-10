# -*- coding: utf-8 -*-
"""
Implements the Social_Web_Platform interface for Twitter and provides
utility methods to access data through the Twitter API and parse results.
"""
from social_web.platform_api import Social_Web_Platform
import json
import oauth2 as oauth
import pickle
import simplejson
import string
import tweepy
import urllib
import urllib2
#import unicodedata
#import webbrowser

class Twitter_Platform(Social_Web_Platform):
    def __init__(self):
        Social_Web_Platform.__init__(self, "twitter")
    
    def __init_authenticated_account__(self):
        # Authenticated Twitter account is required to use the API. Account details:
        self.__consumer_key__ = 'Bn62IlcOcgxKGYBTn17SGQ'
        self.__consumer_secret__ = 'H6TwsebK36zImYUTNbUc0QHzMmHd9NbaooVMgdiw'
        self.__access_key__ = '555518563-4go92i8OBMTNI4uh4F4njF1GTQecY91GArJIhi9U'
        self.__access_secret__ = 'BypinoJNQEzNVK464rgsV2MwKaYhxYPuUdpo9nS3IV8'
        
    def clean_text(self, text):
        """ Handle the following Twitter-specific components from the given string:
            - Replace hash tags with just the word, ie #cars -> cars 
            - Remove RT string (which means retweet so we don't need to disambiguate it)
            - Remove @mentions """
            
        # hash tags
        no_hash = []
        for word in text.split():
            try:
                if word[0]=='#' and word[1] in string.ascii_letters:
                    word = word[1:] # remove the hash
            except:
                continue
            no_hash.append(word)
        cleaned_text = ' '.join(no_hash)
        
        # retweets and @mentions
        cleaned_text = ' '.join([word for word in cleaned_text.split() if 
                                 word.lower()!='rt' and 
                                 word[0]!='@'])
        return cleaned_text
        
    def userlookup(self, all_screennames, num_lookups_desired, active_posts_min,
                   existing_key, nonexisting_key, rate_limit_key):
        """ Given a list of usernames, performs batch lookups to Twitter API
        to fetch extended user info for those accounts. Maps usernames to indicate 
        whether they do or do not exist on Twitter. Also includes a key-value 
        pair to indicate whether or not the rate limit has been reached, like this:
        { exist : [userinfo, userinfo, ...]
          don't exist : [username, username, ...]
          rate limit reached: True or False } """
        print 'Looking up '+str(len(all_screennames))+' usernames on Twitter...'
        
        existing_userinfos = []
        nonexisting_usernames = []
        rate_limit_reached = False
        userlookups = {existing_key:existing_userinfos, nonexisting_key:nonexisting_usernames, 
                       rate_limit_key:rate_limit_reached}
        
        # authenticate so we can make more requests to Twitter API
        client = self.__get_client__()
        
        # users/lookup API takes up to 100 screennames, so may 
        # need to do multiple lookups depending on how large 
        # screennames list is
        start = 0
        end = min(start+100, len(all_screennames))
        progress_count = 1
        while start < end:
            
            if len(existing_userinfos) >= num_lookups_desired:
                # if fetched desired number of usernames, no need 
                # to keep querying twitter until hit rate limit
                break  
            
            if progress_count%50==0:
                print "Querying to test whether usernames exist or don't exist on Twitter... "+\
                "Number usernames analyzed so far: "+str(progress_count)
            progress_count = progress_count+1
            
            onehundred_users = all_screennames[start:end]
            onehundred_list = ','.join(onehundred_users)
            lookup_query = 'https://api.twitter.com/1/users/lookup.json?screen_name='+onehundred_list
            try :
                #response, content = client.request(lookup_query, 'GET')
                content = client.request(lookup_query, 'GET')[1]
                existing_userinfos.extend(json.loads(content)) # these usernames exist
            except Exception as e:
                if 'HTTP Error 400: Bad Request' in str(e):
                    # This is the status code returned during rate limiting.
                    # https://dev.twitter.com/docs/error-codes-responses
                    #print "Twitter rate limit reached when looking up extended user infos. Exiting."
                    rate_limit_reached = True
                    break
    
            start = start+100
            end = min(start+100, len(all_screennames))
            
            # remove any usernames that we already determined do not exist on given site
            existing_usernames = [eui['screen_name'].lower() for eui in existing_userinfos]
            usernames_with_no_userinfo = [u for u in onehundred_users if u not in existing_usernames]
            nonexisting_usernames.extend(usernames_with_no_userinfo)
            
        userlookups[rate_limit_key] = rate_limit_reached
        return userlookups
    
    def get_userinfos(self, usernames):
        """ Queries Twitter to return extended user info 
        for each of the given usernames """
        userinfos = {} # username -> extended user info
        start = 0
        end = min(start+100, len(usernames))
        while start < end:
            onehundred_users = usernames[start:end]
            onehundred_list = ','.join(onehundred_users)
            lookup_query = 'https://api.twitter.com/1/users/lookup.json?screen_name='+onehundred_list
            try :
                response = urllib2.urlopen(lookup_query).read()
                userinfo_list = json.loads(response)
                for userinfo in userinfo_list:
                    userinfos[userinfo["screen_name"]] = userinfo
            except Exception as e1:
                error_msg = str(e1)
                if 'HTTP Error 400: Bad Request' in error_msg:
                    # This is the status code returned during rate limiting.
                    # https://dev.twitter.com/docs/error-codes-responses
                    print "Rate limit reached. Exiting."
                    break
                if 'HTTP Error 404: Not Found' in error_msg:
                    # The resource requested, such as a user, does not exist.
                    # https://dev.twitter.com/docs/error-codes-responses
                    print "No user resource found. Skipping "+str(onehundred_list)
                else:
                    print "Unexpected exception while looking up user information. "
                    print e1
            start = start+100
            end = min(start+100, len(usernames))       
        return userinfos
    
    def fetch_user_tweets_Tweepy(self, api, screenname, 
                                 tweets_key, rate_limit_key, 
                                 num_tweets_to_fetch, 
                                 fetch_full_tweet_obj=False):
        """ Uses the Tweepy API to fetch tweets posted by the given user """
        user_tweets = []
        rate_limit_reached = False
        try:
            # Fetching tweets for user with username "screenname"
            tweepy_user_tweets = api.user_timeline(screenname, count=num_tweets_to_fetch)
            for tut in tweepy_user_tweets:
                try:
                    if fetch_full_tweet_obj:
                        user_tweets.append(tut)
                    else:
                        # just return the tweet text if tweet object not requested
                        user_tweets.append(tut.text.replace('\r', ' ').encode('utf-8'))
                except Exception as e1:
                    print "Problem with tweet "
                    print e1
        except Exception as e2:
            if 'Rate limit exceeded' in str(e2):
                print "Twitter rate limit reached when querying twitter for tweets. Exiting."
                rate_limit_reached = True
            
        tweets_response = {}
        tweets_response[tweets_key] = user_tweets
        tweets_response[rate_limit_key] = rate_limit_reached
        return tweets_response
    
    def fetch_tweets_StreamAPI(self):
        """ Uses the stream API to fetch and cache tweets of 
        any Twitter user accounts we have stored in a cache file
        http://api.twitter.com/1/statuses/user_timeline.json?screen_name=noradio&count=5 """
    
        print "Fetching tweets..."
        try:
            tweets_file = open('tweets.pkl', 'rb')
            tweets = pickle.load(tweets_file)
        except:
            tweets = {}
        
        api = self.__get_api_for_tweepy__()
        
        twitter_users_file = open('twitter_accounts.pkl', 'rb')
        twitter_users = pickle.load(twitter_users_file)
        for twitter_user in twitter_users:
            screenname = twitter_user['screen_name']
            if screenname in tweets:
                # Already fetched tweets for that user
                continue
            user_tweets = self.fetch_user_tweets_Tweepy(api, screenname, 200)
            
            # Store a mapping from twitter username->tweets
            tweets[screenname] = user_tweets
        
        updated_tweets_file = open('tweets.pkl', 'wb')
        pickle.dump(tweets, updated_tweets_file)
        updated_tweets_file.close()
    
        print "Done fetching tweets."
        print "Current size of tweet store: "+str(len(tweets))
    
    def fetch_tweets_SearchAPI(self, query):
        """ Searches Twitter using the given query and 
        returns an array of the resulting tweets """
        search_host = 'http://search.twitter.com/'
        json_query_action = 'search.json?lang=en&rpp=100&q='
        #xml_query_action = 'search.atom?lang=en&rpp=100&q='
        search_url = search_host+json_query_action
        
        query = urllib.quote(query)
        response = urllib2.urlopen(search_url+query).read()
        response = simplejson.loads(response.decode('utf-8'))
        search_results = response['results']
        return search_results 
    
    def get_user_short_texts(self, username):
        """ Fetches the given number of tweets posted by the given username
        and returns a mapping of tweet id -> tweet text wrapped in a 
        mapping that indicates whether the rate limit has been reached """
        
        api = self.__get_api_for_tweepy__()
        tweets_key = 'tweets_key'
        rate_limit_key = self.get_rate_limit_key()
        
        tweets_response = self.fetch_user_tweets_Tweepy(api, username,
                                                        tweets_key, rate_limit_key,
                                                        self.active_posts_min,
                                                        fetch_full_tweet_obj=True)
        user_tweets = tweets_response[tweets_key]
        
        tweet_mapping = {}
        for tweepy_user_tweet in user_tweets:
            tweet_mapping[tweepy_user_tweet.id] = tweepy_user_tweet.text.replace('\r', ' ').encode('utf-8')
            
        shorttext_response = {}
        shorttext_response[self.get_shorttext_response_key()] = tweet_mapping
        shorttext_response[rate_limit_key] = tweets_response[rate_limit_key]
        return shorttext_response
    
    def get_en_lang_users(self, usernames):
        """ Returns users from given list who have specified
        English as their language on their Twitter account"""
        en_lang_users = []
        userinfos = self.get_userinfos(usernames)
        for username in userinfos:
            userinfo = userinfos[username]
            if "en"==userinfo["lang"]:
                en_lang_users.append(username)
        return en_lang_users   
    
    def get_statuses_count(self, usernames):
        """ Returns a mapping of each username to the 
        number of tweets that user has posted """
        num_shorttexts = {} # username -> num tweets
        userinfos = self.get_userinfos(usernames)
        for username in userinfos:
            userinfo = userinfos[username]
            num_tweets = userinfo["statuses_count"]
            num_shorttexts[username] = num_tweets
        return num_shorttexts
    
    def get_shorttext_length_limit(self):
        return 140 # tweets are 140 characters or less
    
    def has_enough_tweets(self, user_info, min_tweetcount):
        """ Returns true if given user has made at least  
        the given minimum number of tweets, false otherwise """
        try:
            tweet_count = user_info['statuses_count']
            if tweet_count!=None and tweet_count>min_tweetcount:
                return True
            else:
                return False
        except:
            return False
        
    def has_bio(self, user_info):
        """ Returns true if given user has a Twitter bio, false otherwise """
        try:
            description = user_info['description']
            if description!=None and description.strip()!='':
                return True
            else:
                return False
        except Exception as e:
            print "Bio of user caused error."
            print e
            return False
    
    def fetching_existence_status(self, usernames, desired_num_usernames):
        """ Returns a map of the usernames that exist and meet the minimum 
        contribution requirement, the usernames that do not exist or do not meet
        the minimum contribution requirement, and the rate limit status, like this:
        { exist and active : [username, username, ...]
          don't exist or not active : [username, username, ...]
          rate limit reached : True or False }
        
        @param usernames: The usernames on which to search for Twitter accounts
        @param min_num_texts:  The minimum number of tweets the Twitter account
        must have written in order to be considered a valid matching account
        """

        # lookup extended user info
        existing_key = self.get_existing_response_key()
        nonexisting_key = self.get_nonexisting_response_key()
        rate_limit_key = self.get_rate_limit_key()
        lookups = self.userlookup(usernames, desired_num_usernames, 
                                              existing_key, nonexisting_key, rate_limit_key)
        
        # extended user info for accounts that exist on Twitter
        existing_userinfos = lookups[existing_key]
        # usernames of accounts that do not exist on Twitter
        nonexisting_usernames = lookups[nonexisting_key]
        
        # filter out those with enough tweets
        existing_and_active = []
        for account in existing_userinfos:
            try:
                num_tweets = account['statuses_count']
                account_name = account['screen_name'].lower()
                
                # if active, add to the existing and active list, 
                # otherwise add to the other list that indicates
                # a username is nonexistent or nonactive
                if num_tweets >= self.active_posts_min:
                    existing_and_active.append(account_name)
                else: 
                    # otherwise, move out of the existing + active
                    # list and into the nonexisting + nonactive list
                    nonexisting_usernames.append(account_name)
            except:
                # just ignore this username if its problematic
                nonexisting_usernames.append(account_name)
                continue 
            
        match_response = {existing_key:existing_and_active, 
                          nonexisting_key:nonexisting_usernames, 
                          rate_limit_key:lookups[rate_limit_key]}
        return match_response
    
    def get_existing_response_key(self):
        return 'EXISTING_USERNAMES_KEY_'+str(self.siteName)
    
    def get_nonexisting_response_key(self):
        return 'NONEXISTING_USERNAMES_KEY_'+str(self.siteName)
    
    def get_shorttext_response_key(self):
        return 'SHORTTEXT_RESPONSE_KEY_'+str(self.siteName)

    def get_rate_limit_key(self):
        ''' Returns the key that maps to whether or not rate 
        limit has been reached while querying this site. '''
        return 'RATE_LIMIT_KEY_'+str(self.siteName)
    
    # Authentication handling so we can make more requests to Twitter API:
    def get_client(self):
        consumer = oauth.Consumer(self.__consumer_key__, self.__consumer_secret__)
        token = oauth.Token(key=self.__access_key__, secret=self.__access_secret__)
        client = oauth.Client(consumer, token)
        return client
    def __get_api_for_tweepy__(self):
        ''' Provides authorized access to the Twitter API '''
        
    #    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    #    
    #    # Open authorization URL in browser
    #    webbrowser.open(auth.get_authorization_url())
    #
    #    # Ask user for verifier pin
    #    pin = raw_input('Verification pin number from twitter.com: ').strip()
    #
    #    # Get access token
    #    token = auth.get_access_token(verifier=pin)
    #
    #    # Give user the access token
    #    print 'Access token:'
    #    print '  Key: %s' % token.key
    #    print '  Secret: %s' % token.secret
        
        auth = tweepy.OAuthHandler(self.__consumer_key__, self.__consumer_secret__)
        auth.set_access_token(self.__access_key__, self.__access_secret__)
        api = tweepy.API(auth)
        return api