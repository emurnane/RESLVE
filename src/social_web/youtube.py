# -*- coding: utf-8 -*-
"""
Contains utility functions used to access YouTube through
YouTube Python developer API.

Installation instructions:
The YouTube Python API requires that you install the latest 
version of the Google Data Library:
https://code.google.com/p/gdata-python-client/downloads/list 
(2.0.17 last version tested with this code)
Download the library and unpack/unzip it and run "setup.py install" 
from the main directory to install the library.

@author: Sean Allen
"""

from social_web.platform_api import Social_Web_Platform
import gdata.youtube.service
import re

class YouTube_Platform(Social_Web_Platform):
    def __init__(self):
        Social_Web_Platform.__init__(self, "youtube")
        
    def __init_authenticated_account__(self):
        # YouTube developer key used to access API:
        self.developer_key = "AI39si4ki5VuTuHHb9vio1-IlNjt-AOPiiLCnWDI8U00AHvWlUcm8m2oVfRCkWd7FC54wY6oUb7_Mqml3ntQd8i2yUiO9Ou4_g"
        self.client_id = "MapHub"

    def get_client(self):
        """
        get_client - Returns a YouTube service object initialized with
        our developer key so we can send API queries to pull down data from the site.
        
        @return gdata.youtube.service.YouTubeService
        """
        service = gdata.youtube.service.YouTubeService()
        service.developer_key = self.developer_key
        service.client_id = self.client_id
        service.ssl = True
        return service
        
    def clean_text(self, text):
        """ Filter the following YouTube-specific components from the given string:
            - Remove copyright notice
            - Remove video quality """
            
        cleaned_youtube_shorttext = []
        
        # For each word in the user's short text
        for word in text.split():
            try:
                
                # Remove copyright so it does not show up as an entity
                if(word.lower() == "copyright"):
                    continue
                
                # Remove video quality so it does not show up as an entity
                if(re.match("^\W*1080[pi]?\W*$", word.lower()) != None or 
                   re.match("^\W*720[pi]?\W*$", word.lower()) != None or 
                   re.match("^\W*480[pi]?\W*$", word.lower()) != None):
                    continue
                
            except:
                continue
            cleaned_youtube_shorttext.append(word)
            
        cleaned_text = ' '.join(cleaned_youtube_shorttext)
        return cleaned_text

    def user_lookup(self, usernames, desired_num_usernames, minimum_number_of_videos):
        """
        user_lookup - Given a list of usernames, returns the first
        desired_num_usernames that exist on YouTube and have posted
        at least minimum_number_of_videos of videos on the site.
        
        @param list usernames
        @param int desired_num_usernames
        @param int minimum_number_of_videos
        @return list of usernames
        """
        
        # Check input
        existingUsernames = []
        if desired_num_usernames <= 0 or minimum_number_of_videos <= 0:
            return existingUsernames
        
        print "Querying to test whether usernames exist or don't exist on YouTube..."
        
        progress_count = 1
        for username in usernames:
            
            # Break out of loop when we have found the desired number of usernames
            if(desired_num_usernames <= 0):
                break
            
            # Build search query to find videos by this user
            searchQuery = gdata.youtube.service.YouTubeVideoQuery()
            searchQuery.time = "all_time"
            searchQuery.author = username
            
            # Cannot retrieve all min # of videos at once if its set to a large number, so we'll set the 
            # start index into the retrieved list to be one minus the number that we want, so if the user 
            # has posted at least this amount they'll have one video in the response list
            searchQuery.max_results = minimum_number_of_videos
            if(minimum_number_of_videos > 1):
                searchQuery.start_index = minimum_number_of_videos - 1
            
            # Query YouTube for video feed of the user's videos, add to return value if they have posted
            # the minimum amount
            videoFeed = self.get_client().YouTubeQuery(searchQuery)
            if(videoFeed.entry != None):
                if(len(videoFeed.entry) > 0):
                    existingUsernames.append(username)
                    desired_num_usernames -= 1
            
            # Display progress on command line
            if progress_count % 50 == 0:
                print "Number usernames analyzed so far: " + str(progress_count)
            progress_count = progress_count+1
        
        return existingUsernames
    
    def get_user_video_text(self, username):
        """
        get_user_video_text - Returns the title, description, and tags for every
        video the user with the given username has posted on YouTube.
        
        @param string username
        @return A map. keyed as video_id_[title||description||tags] => "title||description|||tags" string
        """
        
        # Check input
        if username == None:
            return {}
        
        # Fetch videos for user, ten at a time
        userVideos = {}
        startIndex = 1
        numberOfVideosAtATime = 10
        limitNumberOfVideos = 500
        while True:
            
            # Print status
            print "Fetching videos for user..."
            
            # Build query used to fetch the next ten videos for the user
            searchQuery = gdata.youtube.service.YouTubeVideoQuery()
            searchQuery.time = "all_time"
            searchQuery.author = username
            searchQuery.orderby = "published"
            searchQuery.max_results = numberOfVideosAtATime
            searchQuery.start_index = startIndex
            startIndex += numberOfVideosAtATime
            
            # Get the next ten videos for the user from YouTube
            videoFeed = self.get_client().YouTubeQuery(searchQuery)
            if videoFeed.entry == None:
                break
            
            # Add text information for all of the user's videos to our dataset
            for video in videoFeed.entry:
                
                # Get video id from video url, do not add to list if we cannot determine the id
                if video.media.player.url == None:
                    continue
                url = video.media.player.url.decode("utf-8")
                videoIDIndex = url.find("?v=")
                if videoIDIndex == -1:
                    continue
                videoIDIndex = videoIDIndex + 3
                endOfVideoIDIndex = url.find("&")
                videoID = None
                if endOfVideoIDIndex == -1:
                    videoID = url[videoIDIndex:]
                else:
                    videoID = url[videoIDIndex:endOfVideoIDIndex]
                
                # Get title, description, and tags, these will be the "short texts" for this video
                if video.media.title.text != None:
                    userVideos[videoID + "_title"] = video.media.title.text.decode("utf-8");
                if video.media.description.text != None:
                    userVideos[videoID + "_description"] = video.media.description.text.decode("utf-8");        
                if video.media.category[0].text != None:
                    userVideos[videoID + "_tags"] = video.media.category[0].text.decode("utf-8")
            
            # Have fetched all of the user's videos or have reached limit that we want to fetch, so return
            if len(videoFeed.entry) < numberOfVideosAtATime or startIndex >= limitNumberOfVideos:
                break
                
        return userVideos
