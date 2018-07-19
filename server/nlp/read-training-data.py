import spacy, csv
all_rules = open("D:/Ananth/Allstate/spacy/training/custom-sentdetec-model - Copy.train").read()
all_rules_splitted = all_rules.split("\n")
print(len(all_rules_splitted))
nlp = spacy.load("D:/Ananth/Allstate/spacy/models/en_core_web_sm-2.0.0/en_core_web_sm/en_core_web_sm-2.0.0")
entities = set()
pos_dict = {}
accepted_pos = ['PROPN', 'NOUN', 'DET', 'PUNCT', 'CCONJ']
delimiter_pos = ['DET', 'PUNCT','CCONJ']
def get_entities(np):
    entities = []
    entity = ''
    for token in np:
        if token.pos_ in accepted_pos:
            if (token.pos_ in delimiter_pos and token.text !='-'):
                if entity != '':
                    entities.append(entity.strip())
                    entity = ''
                else:
                    continue
            else:
                if token.text != '-':
                    entity = entity + token.text
                    entity = entity + ' '
                else:
                    entity = entity.strip() + token.text
    if entity != '':
        entities.append(entity.strip())    
    return entities



with open('out.csv', 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for one_rule in all_rules_splitted:
        doc = nlp(one_rule)
        for np in doc.noun_chunks:
            postag = ''
            for token in np:
                postag = postag + token.pos_ + ' '
               
           #print(postag)
            pos_dict[np.text] = postag.strip()
            #pos_dict[np.text+'_modified'] = get_entities(np)
            #entities.add(np.text)
            for entity in get_entities(np):
                entities.add(entity)
            
    #print('ent', entities)
    for one_row in entities:
        #csv_writer.writerow([one_row,str(pos_dict.get(one_row)),pos_dict.get(one_row+'_modified') ])
        csv_writer.writerow([one_row])


print('length of entities', len(entities))

