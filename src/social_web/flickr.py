# -*- coding: utf-8 -*-
"""
Utility methods to access data through the Flickr API and parse results.
@author: Wenceslaus Lee
"""
from social_web.platform_api import Social_Web_Platform
import flickrapi

class Flickr_Platform(Social_Web_Platform):
    def __init__(self):
        Social_Web_Platform.__init__(self, "flickr")    
        
    def __init_authenticated_account__(self):
        # Flickr account is required to use the API. Account details:
        self.api_key = '30c858fad0c06cd85d0d481ceaea86e6'
        self.api_secret = 'f8e82fe09698b9ce'
        
    def get_client(self):
        # authentication handling
        flickr = flickrapi.FlickrAPI(self.api_key, self.api_secret)
        return flickr
        
    def clean_text(self, text):
        return text
    
    def userlookup(self, usernames, desired_num_usernames, min_number_of_pictures):
        """ Get existing users """
        existing_usernames = []
        if desired_num_usernames <= 0:
            return existing_usernames
        
        print "Querying to test whether usernames exist or don't exist on Flickr"
        
        progress_count = 0
        for username in usernames:
            if (desired_num_usernames <= 0):
                break
            client = self.get_client()
            userid = self.getIDByUsername(username, client)
            if userid != '-1':
                num = len(self.getPhotosIDByUserID(userid, client, self.api_key))
                if num > min_number_of_pictures:
                    existing_usernames.append(username)
                    desired_num_usernames -= 1
            progress_count += 1
            if progress_count % 50 == 0:
                print "Number usernames analyzed so far: " + str(progress_count)
        
        return existing_usernames
            
    def getIDByUsername(self, usernamestring, flickr):
        """ Get UserID by Username """
        try:
            users = flickr.people_findByUsername(username = usernamestring)
            user = users[0]
            return user.attrib['id']
        except flickrapi.exceptions.FlickrError:
            return '-1'
    
    def getTagsByPhotosID(self, photoid, flickr):
        """ Get Tags by UserID """
        photo = flickr.photos_getInfo(api_key = self.api_key, 
                                      photo_id = photoid, 
                                      api_secret = self.api_secret)
        tags = photo[0].find('tags')
        taglist = []
        for childtag in tags:
            taglist.append(childtag.attrib['raw'])
        return taglist
    
    def getPhotosIDByUserID(self, userid, flickr, key):
        """ Get PhotoID by UserID """
        listofphotosid = []
        photos = flickr.people_getPhotos(api_key = key, user_id = userid)
        for child in photos[0]:
            listofphotosid.append(child.attrib['id'])
        return listofphotosid
    
    def getDescriptionByPhotosID(self, photoid, flickr):
        """ Get Photo Descriptions by PhotoID """
        photo = flickr.photos_getInfo(api_key = self.api_key, 
                                      photo_id = photoid, 
                                      api_secret = self.api_secret)
        description = photo[0].find('description').text
        return description
    
    def getCommentsByPhotosID(self, listofphotosid, flickr):
        """ Get Photo Comments by PhotoID """
        listofcomments = []
        for child in listofphotosid:
            photo = flickr.photos_getInfo(api_key = self.api_key, 
                                          photo_id = child, 
                                          api_secret = self.api_secret)
            listofcomments.append(photo[0].find('comments').text) 
        return listofcomments
    
    def getTitlesByPhotosID(self, photoid, flickr):
        """ Get Photo Titles by PhotoID """
        photo = flickr.photos_getInfo(api_key = self.api_key, 
                                      photo_id = photoid, 
                                      api_secret = self.api_secret)
        title = photo[0].find('title').text
        return title
    
    def get_user_picture_text(self, username):
        if username == None:
            return {}
            
        userPictures = {}
        print "Fetching picture descriptions for user " + username
        
        client = self.get_client();
        userID = self.getIDByUsername(username,client)
        picturelist = self.getPhotosIDByUserID(userID, client, self.api_key)
        
        if picturelist == None:
            return userPictures
        
        for picture in picturelist:
            userPictures[picture] = self.getDescriptionByPhotosID(picture, client)
        
        return userPictures
    
    def get_user_picture_tag(self, username):
        if username == None:
            return {}
            
        userPictures = {}
        print "Fetching picture tags for user " + username
        
        client = self.get_client();
        userID = self.getIDByUsername(username,client)
        picturelist = self.getPhotosIDByUserID(userID, client, self.api_key)
        
        if picturelist == None:
            return userPictures
        
        for picture in picturelist:
            userPictures[picture] = self.getTagsByPhotosID(picture, client)
        
        return userPictures
    
    def get_user_picture_title(self, username):
        if username == None:
            return {}
            
        userPictures = {}
        print "Fetching picture titles for user " + username
        
        client = self.get_client();
        userID = self.getIDByUsername(username,client)
        picturelist = self.getPhotosIDByUserID(userID, client, self.api_key)
        
        if picturelist == None:
            return userPictures
        
        for picture in picturelist:
            userPictures[picture] = self.getTitlesByPhotosID(picture, client)
        
        return userPictures
