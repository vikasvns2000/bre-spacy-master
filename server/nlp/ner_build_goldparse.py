import random, re
import datetime

class BuildGoldParse:

    def get_gold_parse(self,file_name, entities_name):
        all_data = None
        revision_texts = []
        indexes = []
        matches_dict = {}

        entities = None
        with open(entities_name, encoding="utf-8") as entities_data:
            all_data = entities_data.read()
            entities = all_data.split('\n')
    
        if entities: 
            with open(file_name, encoding="utf-8") as file_data:
                all_data = file_data.read()
                all_data_splitted = all_data.split('\n')
                # for one_rule in all_data_splitted:
                #     match_spans, match_entities = mark_entities(one_rule, entities)
                #     #clean overlapping entities
                #     match_spans, match_entities = clean_overlapping_spans(match_spans, match_entities)
                #     print('cleaned list',  match_spans, match_entities)
                for one_entity in entities:
                    self.mark_entities(one_entity, all_data_splitted, matches_dict)
                #print('***final list***\n', matches_dict)
                self.clean_overlapping_spans(matches_dict)
                print('after clearning..\n', len(matches_dict) )
        return matches_dict

        
    def mark_entities(self, one_entity, rules, matches_dict):
        """
        Match for exact words(use \b to indicate that)
        and do not ignore case for 2-char words which would be 
        mostly US states. so, 'IN' is in entity where 'in' is not.
        """
        matches = None
        p1 = re.compile('\\b' + re.escape(one_entity) + '\\b')
        p2 = re.compile('\\b' + re.escape(one_entity) + '\\b', re.I)
        for one_rule in rules:
            one_match_set = [] #this will be a list of tuples: [('product type, 0,12),('type',8,12)]
            to_update = []
            if len(one_rule) == 0:
                continue
            if len(one_entity) <= 2:
                #matches = re.finditer(p1, one_rule)
                matches = p1.finditer(one_rule)
            else:
                #matches = re.finditer(p2, one_rule)
                matches = p2.finditer(one_rule)
            if matches:
                #print('matches..', matches)
                for match in matches:
                    match_span = match.span()
                    # do a slice of one_text and get the matched text.
                    match_text = one_rule[match_span[0] : match_span[1]]
                    #print (one_rule, [match_text], match_span)
                    one_match_set.append((match_text,match_span[0], match_span[1]))
                #update the dictionary with values matches this entity
                to_update = matches_dict.get(one_rule) if matches_dict.get(one_rule) else []
                to_update.extend(one_match_set)
                matches_dict[one_rule] = to_update
        

    def clean_overlapping_spans(self, matches_dict):
        """
        the dictionary contains values as list of tuples: [(),(),()]
        in every tuple, first element is the matched text in rule(i.e 'key'
        in below iteration) and second element is the start position and 
        third element is the end position.
        So, iterate over the 'value' and look if any element has overlapping 
        span and if so delete that tuple from the list and finally update the 
        dictionary with updated array of tuples.
        1) Delete embedded entities
        2) Merge overlaping entities
        """
        for key, value in matches_dict.items():
            #copy 'value' to a new variable
            # use this variable to delete items and leave 
            # original list untouched for proper iteration.
            new_value = value[:]
            for one_tuple in value:
                for same_tuple in value:
                    if one_tuple != same_tuple:
                        # delete embedded entities
                        if same_tuple[1] >= one_tuple[1] and same_tuple[2] <= one_tuple[2]:
                            #print('span to be deleted:', same_tuple)
                            # same value could be marked for deletion twice because of looping.
                            # and hence value error excepton will be thrown.
                            # so ignore such exceptions.
                            try:
                                new_value.remove(same_tuple)
                            except ValueError:
                                pass
                            continue
                        # merge overlapping entities
                        if (same_tuple[1] >= one_tuple[1] and same_tuple[1] <= one_tuple[2]) or\
                        (same_tuple[2] >= one_tuple[1] and same_tuple[2] <= one_tuple[2]) :
                        # make sure the entities to be merged are present in modified 'value'
                            if same_tuple in new_value and one_tuple in new_value:
                                #get lowest start position
                                new_start = min(same_tuple[1], one_tuple[1] )
                                # highest end position
                                new_end = max(same_tuple[2], one_tuple[2])
                                # delete both entities and form the new entity
                                new_entity = key[new_start:new_end]
                                new_value.remove(same_tuple)
                                new_value.remove(one_tuple)
                                new_value.append((new_entity, new_start, new_end))

            #update the dictionary back with updated value
            matches_dict[key] = new_value

    def build(self, training_file, entities_file):

        start_time = datetime.datetime.now()
        #self.get_gold_parse('D:/Ananth/Allstate/spacy/training/custom-sentdetec-model - Copy.train',\
        #'D:/Ananth/Allstate/spacy/source/out - Copy.csv')
        matches_dict = self.get_gold_parse(training_file, entities_file)
        end_time = datetime.datetime.now()
        with open("dict.txt", mode='w', newline='\n') as out_file:
            for key, value in matches_dict.items():
                out_file.write(str((key, value))+'\n')

        print('time taken', end_time-start_time)
        return matches_dict