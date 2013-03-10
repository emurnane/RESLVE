# -*- coding: utf-8 -*-
import csv_util

def run():
    rows = csv_util.query_csv_for_rows('labeled_data/entities.csv')
    labeled_entities = set()
    resolved_entities = set()
    for row in rows:
        entity_id = row[0]+'_'+row[3] # (i.e., "surfaceform_shorttext")
        
        label = row[2]
        if label == 'Y':
            labeled_entities.add(entity_id)
            resolved_entities.add(entity_id)
        elif label=='N':
            labeled_entities.add(entity_id)
            
    print str(len(labeled_entities))+" annotated entities."
    print str(len(resolved_entities))+" unanimously annotated entities."

if __name__=='__main__':
    run()