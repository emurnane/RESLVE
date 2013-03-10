# -*- coding: utf-8 -*-
import csv_util
def run():
    username_rows = csv_util.query_csv_for_rows('labeled_data/user_identity.csv')
    
    total_flickr = 0
    total_twitter = 0
    total_youtube = 0
    
    exists_flickrs = 0
    exists_twitters = 0
    exists_youtubes = 0
    
    FP_Flickr = 0
    FP_Twitter = 0
    FP_Youtube = 0    
    
    TP_Flickr = 0
    TP_Twitter = 0
    TP_Youtube = 0   
    
    for row in username_rows:
        #username = row[0]
        
        flickr_label = row[1]
        twitter_label = row[2]
        youtube_label = row[3]
        
        exists_wikipedia = row[4]
        
        exists_flickr = row[5]
        exists_twitter = row[6]
        exists_youtube = row[7]
        
        if exists_flickr=='TRUE' and exists_wikipedia=='TRUE':
            exists_flickrs+=1
        if exists_twitter=='TRUE' and exists_wikipedia=='TRUE':
            exists_twitters+=1
        if exists_youtube=='TRUE' and exists_wikipedia=='TRUE':
            exists_youtubes+=1
        
        if flickr_label!='':
            total_flickr+=1
        if twitter_label!='':
            total_twitter+=1
        if youtube_label!='':
            total_youtube+=1        
        
        if flickr_label=='TP':
            TP_Flickr+=1
        if twitter_label=='TP':
            TP_Twitter+=1                                            
        if youtube_label=='TP':
            TP_Youtube+=1                                                   
        
        if flickr_label=='FP':
            FP_Flickr+=1
        if twitter_label=='FP':
            FP_Twitter+=1                                            
        if youtube_label=='FP':
            FP_Youtube+=1   
            
    print "Table 3"
    print "Initial Sample Twitter: "+str(total_twitter)
    print "Reused: "+str(exists_twitters)+" "+str(100*float(exists_twitters)/total_twitter)
    print " "
    
    print "Initial Sample YouTube: "+str(total_youtube)
    print "Reused: "+str(exists_youtubes)+" "+str(100*float(exists_youtubes)/total_youtube)
    print " "
    
    print "Initial Sample Flickr: "+str(total_flickr)
    print "Reused: "+str(exists_flickrs)+" "+str(100*float(exists_flickrs)/total_flickr)
    print  " "
    
    print "Twitter Bridged: "+str(TP_Twitter)+" "+str(100*float(TP_Twitter)/(TP_Twitter+FP_Twitter))
    print "Youtube Bridged: "+str(TP_Youtube)+" "+str(100*float(TP_Youtube)/(TP_Youtube+FP_Youtube))
    print "Flickr Bridged: "+str(TP_Flickr)+" "+str(100*float(TP_Flickr)/(TP_Flickr+FP_Flickr))

if __name__=='__main__':
    run()