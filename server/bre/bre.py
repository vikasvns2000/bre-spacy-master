
from server.nlp.spacy_nlu import NLU
import spacy
import csv
import json

nlu = NLU()
in_file_name = "D:/Ananth/Allstate/spacy/input/input.csv"
# Rule representation
rule_repr = []
# POS tags to ignore
POS_TO_IGNORE=['det', 'punct', 'adv', 'space']
META_TYPE = ['applicability', 'Note', 'Refer']

default_applicability = '$ALL'


# get nlp object
nlp = nlu.get_nlp()

def run_one_rule(one_rule):
    """
    Run bre extraction for one rule.
    """
    current_applicability = [default_applicability,]
    rule_appl_entities = []
    rule_repr = []
    i=0 # counter for number of sentences within a rule

    #get DOC object for full rule, clean up the data as well.
    doc_full = nlu.get_doc(nlp, one_rule, clean=True)
    # for each sentences in the rule, find out other attributes
    for sent in doc_full.sents:
        dict_sent = {}
        # get DOC object of one sentence
        doc = nlu.get_doc(nlp, str(sent), clean=False)
        # get root (or Action) of the sentence.
        root_token, root_text_tokens = nlu.find_root(doc)
        root_text = ' '.join(root_text_tokens)
        # skip this one if the root is PUNCT. such sentences will not have any meaninful info
        if root_token.pos_ == 'PUNCT':
            continue
        i += 1
        #dict_sent['rule_action'] = root_token.text if len(root_text.strip()) == 0 else root_text
        dict_sent['rule_action'] = '$' + (root_text + ' ' + root_token.text).strip()
        #dict_sent['rule_pos_'] = root_token.pos_
        # find out if this statement is done or continuing to next statement(s)
        # for example, of the statement has something like this: 
        # ' For Endorsement, ..... , when below conditions are met.',
        
        # get the actor for this rule
        actors = list(get_actors(doc, root_token))
        dict_sent['rule_actors'] = actors
        #dict_sent['rule_actors_1'] = nlu.find_objects(root_token)

        # get valid values for this rule
        dict_values, valid_value_tokens =  get_valid_values(doc, root_token, root_text_tokens)
        dict_sent['rule_valid_values'] = dict_values
        dict_sent['rule_valid_values_tokens'] = valid_value_tokens
        # see if the valid values absolute (can act on its own) or 
        # if they have clause associated with them
        clause_for_values = nlu.get_rel_clause(valid_value_tokens)
        if len(clause_for_values) > 0:
            # get the dict of tokens and store convert to dict of texts
            for key in clause_for_values:
                values_text = []
                values_text.extend([token.text for token in clause_for_values[key]])
                clause_for_values[key] = values_text
            dict_sent['rule_clause_for_values'] = clause_for_values
        # get applicablity for this rule
        applicability_tokens = get_applicability(root_token)
        if len(applicability_tokens) > 0:
            applicability_ents_form = get_entities_form(doc, applicability_tokens)
            #dict_sent['rule_applicability'] = [values.text for values in applicability_tokens]
            print('applicability ents form:', applicability_ents_form)
            dict_sent['rule_applicability'] = list(applicability_ents_form)
            current_applicability = list(applicability_ents_form)
        else:
            dict_sent['rule_applicability'] = list(current_applicability)

        #get conditions list
        conds = []
        conds_ents_form = []
        conds = get_cond_dict(doc, root_token)
        if len(conds) > 0:
            # get attributes of condition(s)  in entities form
            for cond in conds:
                try:
                    attrs_tokens = cond["attributes"]
                    attrs_ents_form = get_entities_form(doc, attrs_tokens)
                    cond["attributes"] = attrs_ents_form
                except KeyError: # if attributes are not present, ignore - move on to next cond.
                    pass
                conds_ents_form.append(cond)
            
            dict_sent['rule_conditions'] = conds_ents_form


        # then we need to find other statements as well.
        #if consider_next_statements():

        # if the root is a NOUN, mostly there is no VERB in the statement and 
        # hence the sentence will be considered as an Entity, so add it to previous 
        # statement, i.e. consider this as continuation of previous statement.
        if root_token.pos_ == 'NOUN':
            is_verb_present = nlu.find_verb_presence(doc)
            if not is_verb_present: # no verbs present
                # mostly this statement is part of previous statement 
                # to get a full meaning.
                print('consider this part of previous rule', doc)
                update_prv_statment(doc, rule_repr)
                continue # skip any further processing.

        
        # Check if this statement contains meta-details:
        # for example, the sentence ' .. This rule is applicable for ... ' 
        # is actually a meta-statement
        meta_type = get_meta_type(nlp, dict_sent)
        
        if meta_type:
            if meta_type == META_TYPE[0]: # applicability
                #then get all entities present in this statement
                # this will be the applicability for the rule 
                rule_appl_entities = doc.ents
                #print('entities from meta-statement', entities)


        #if not meta_type: # do not add if this is meta-statement
        # remove unserializable values (i.e SpaCy tokens)
        dict_sent.pop('rule_valid_values_tokens')
        rule_repr.append(dict_sent)
    
    # check if there is any rule-level applicablity setting
    # if so, apply this for all statements. ALso remove $ALL if mentioned previously
    if len(rule_appl_entities) > 0 :
        applicability = []
        for one_repr in rule_repr:
            applicability = one_repr['rule_applicability']
            if len(applicability) > 0 :
                try:
                    applicability.remove(default_applicability)
                except ValueError: # ignore if the list doesnt contain default applicability
                    pass
                applicability.extend(['$$' + ent.text for ent in rule_appl_entities])
                one_repr['rule_applicability'] = applicability

    #print(rule_repr)
    print(json.dumps(rule_repr))
    return rule_repr

def run():
    csv_out_file = open('out-json.csv', 'w', newline='\n') 
    csv_writer = csv.writer(csv_out_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    with open(in_file_name, mode='r', encoding="utf-8") as csv_file:
        
        # creating a csv reader object
        csvreader = csv.reader(csv_file)
        
        # extracting field names through first row
        fields = next(csvreader, None)
    
        # extracting each data row one by one
        for one_rule in csvreader:
            rule_repr = []
            rule_appl_entities = []
            default_applicability = '$ALL'
            current_applicability = [default_applicability,]
            rule_repr = run_one_rule(one_rule[0])
            csv_writer.writerow([one_rule, json.dumps(rule_repr) ])
        
        if csv_out_file:
            csv_out_file.close()
            del csv_out_file

def get_cond_dict(doc, root_token):
    """
    Get all condition tokens. Every condition is delimited by a 'None' object.
    If the length of conditons is greater than 2, then form condition, action 
    and attributes for the conditions: 
    Eg: " set xxxx to yyyy, if zzzz is greater than 20 chars"

    IF the length of conditions is 1, then form condition only:
    Eg: " Otherwise, set it to zero".
    """
    dict_cond = {}
    cond_list=[]
    # get all tokens present in condition(s)
    condition_tokens = nlu.find_advcl(root_token)
    print("from nlu:", condition_tokens)
    one_cond = []
    conds = []
    # form a list of list of condition tokens. 'None' will work
    # as delimiter object betweeen multiple conditions.
    for token in condition_tokens:
        if token is None:
            conds.append(one_cond)
            one_cond=[]
        else:
            one_cond.append(token)

    # iterate through all conditions and form conditions dictionary
    for cond in conds:
        n = len(cond)
        dict_cond={}
        attrs=[]
        print('conditions...', cond)
        if n > 2:
            dict_cond["condition"] = '$'+cond[0].text
            dict_cond["action"] = '$'+cond[n-1].text
            for token in cond[1:(n-1)]:
                if token.dep_.lower() != 'cc':
                    #attrs.append(token.text)
                    attrs.append(token)
            #dict_cond["attributes"] = ' '.join(attrs)
            dict_cond["attributes"] = attrs
            dict_cond["attr_new" + cond[n-1].text] = get_conditions_formatted(doc, cond[n-1])
            cond_list.append(dict_cond)
        if n <= 2 :
            dict_cond["condition"] = '$'+cond[0].text
            cond_list.append(dict_cond)
    return cond_list

def get_meta_type(nlp, dict_sent):
    """
    Find out if the sentence contains any meta-data. If so, identify the type of 
    meta-data.
    meta-data types:
    1) Applicablity
    2) Reference/Note
    """
    # find out if the sentence if contains info on applicablity
    actors = dict_sent['rule_actors']
    rule_valid_values = dict_sent['rule_valid_values_tokens'] # list of tokens
   
    # find out the word similarity with the word 'applicable'
    # if the word is similar to that, then we would consider that as applicablity meta-statement

    if 'rule' in actors: # if actors list contains word 'rule'
        doc = nlu.get_doc(nlp, u'applicable')
        for token in rule_valid_values:
            similarity_score = doc[0].similarity(token)
            print('similarity score:' , similarity_score)
            if similarity_score > 0.6:
                return META_TYPE[0] #applicability
    
    # find out if the sentence is a Note or Refer type of sentence
    action = dict_sent["rule_action"]
    action_text = action.strip('$').lower()
    if action_text == 'note':
        return META_TYPE[1] # Note
    if action_text == 'refer':
        return META_TYPE[2] # Refer
    
    return None


def get_actors(doc, root_token):
    actors_ent = set()
    actors_tokens = nlu.find_objects(root_token)
    # if there are no objects directly associated with root token, 
    # then check if there are noun phrases associated with 
    # adv clause modifiers
    if not actors_tokens:
        actors_tokens = nlu.get_np_advmod(doc)
    for actor in actors_tokens:
        # skip None objects, if any and determiners.
        #if actor and actor.pos_.lower() != 'det': 
        if actor and actor.pos_.lower() not in POS_TO_IGNORE: 
            ent = nlu.get_covered_entity(doc, actor)
            if ent:
                actors_ent.add('$$'+ ent.text.strip()) # if entity, prefix $$
            else:
                actors_ent.add(actor.text)
                actors_ent.add('(' + actor.pos_ + ')')
    return actors_ent

def get_entities_form(doc, tokens):
    """
    Find out if an token is falling under an entity, if so, get that value
    instead of individual token.
    Do not add duplicate entities.
    Eg: if the tokens are [Multiple, Record, Policy, Code], and if the covered entity
    is 'Multiple Record Policy Code', then add it only once and not 4 times. 
    (i.e. use a 'Set' :-) )
    """
    ent_texts = []
    ents = set()
    for token in tokens:
        ent = nlu.get_covered_entity(doc, token)
        if ent:
            if ent not in ents:
                ent_texts.append('$$' + ent.text)
                ents.add(ent)
        else:
            ent_texts.append(token.text)
    return ent_texts

def get_valid_values(doc, root_token, root_text_tokens):
    """
    Find valid values (or their negation).
        1. Find using prep object if the rule is in this format:
         ".... set xxxx to yyyy...." - here yyyy is the object we are interested int
        2. Find using attr or acomp or oprd if the rule is in this format:
        ".... cannot/should/mustn't be blanks/greater than 20 char/less than 10...
        3. Find using `dative` objects if the rule is in this format:
        `.... set xxxx to "A"` 

        Note: second case is applicable if root_token's lemma is 'be' (i.e. root_token
        is be or is or was etc..)
        #3 is a special case of 1 where the object is not linked using `prep` instead using
        `dative`.
        There are some special cases where TO-clause is used. Such values also 
        need to be extracted. Eg: "....  set to blanks"

    """
    values = []
    dict_values = {}
    values_text_form = []
    expression = None
    expr_uom = None
    
    # 1. get prep objects to the right of root
    values = nlu.find_right_prep_obj(root_token)
    
    # 2. find out dative objects, if any
    dative_objects = nlu.get_right_dative_pobj(root_token)
    values.extend(dative_objects)

    # 3. find out if there are any TO-clause for this root token
    to_clause_tokens = nlu.get_to_clause(root_token)
    values.extend(to_clause_tokens)

    print("checkin condtion for nlu.find_tokens_for_be..", root_token.lemma_)
    # 4. if root is `be` (in simple and combined form), i.e. 
    # simple form: `cannot be blanks' -> here `be` is the root
    # combined form: `cannot be left blanks` -> here `left` is the root 
    if root_token.lemma_ == 'be' or 'be' in root_text_tokens :
        print("calling nlu.find_tokens_for_be.. using right_side approach")
        # find expresssion from attr values - ignore negation text as they are already
        # considered as part of rule_action.
        attrs, cc, pobjs, _ ,cond_expr = nlu.get_attr_and_neg(root_token)
        expression, expr_uom = form_expr_from_attr(doc, get_entities_form(doc, attrs), cc, get_entities_form(doc,pobjs),[], cond_expr)
        # find associated token of `be` if expr couldnt be formed
        if not expression:
            values.extend(nlu.find_tokens_for_be(root_token))
            
        print("expression (attr & neg) is...  & UOM", expression, expr_uom)

        dict_cond_formatted = get_conditions_formatted(doc, root_token)
        print("expression (conditons formatted) is..", dict_cond_formatted)
        
    # get entities form of the values...
    values_filtered = [value for value in values if value.pos_.lower() not in POS_TO_IGNORE]
    values_ent_form = get_entities_form(doc, values_filtered)
    
    if len(values_ent_form) > 0:
        values_text_form.extend(values_ent_form)
    if expression:
        values_text_form.append(expression)

    dict_values["value"] = values_text_form
    if expr_uom:
        dict_values["value_uom"] = expr_uom
    else:
        dict_values["value_uom"] = "$None"

    return dict_values, values

def get_conditions_formatted(doc, cond_token):
    """
    Get the condition in a formatted structure:
    1) Left-hand side
    2) Right-hand side
    3) Operation
    """
    dict_subj = {}
    dict_cond_formatted = {}

    advcl_objects, advcl_subjects, dict_subj = nlu.get_advcl_elements(cond_token)
    #get left side values of the dictionary for conditions.
    dict_cond_formatted = get_left_side_values(doc, cond_token, dict_subj)

    # get right hand side of condition
    dict_cond_formatted["right_side"] = str(get_right_side_values(doc, cond_token))

    return dict_cond_formatted

def get_left_side_values(doc, cond_token, dict_subj):
    """
    Get left side values (i.e. subject & related objects)
    of a condition or sub-condition.

    """
    dict_cond_formatted = {}
    #for subject in advcl_subjects:
    for subject, value in dict_subj.items():
        advcl_pobjs = []
        adj_mods = []
        
        advcl_pobjs = value
        # get entity form of the subject
        subject_entity_form = get_entities_form(doc, [subject,])[0]
        # check if there is any adj modifier for the subject
        adj_mods = nlu.get_amod(subject)
        if len(adj_mods) > 0:
            adj_mod = adj_mods[0].text
            # add it to the subject if it not alreayd present
            if adj_mod not in subject_entity_form:
                subject_entity_form = subject_entity_form + '.' + adj_mod

        # if there is no prep objs associated, form the conditon with only the subject
        if len(advcl_pobjs) == 0:
            dict_cond_formatted["left_side"] = subject_entity_form
        if len(advcl_pobjs) > 0:
            # get the first pobj
            first_pobj_tokens = advcl_pobjs[0]
            n = len(first_pobj_tokens)
            if n > 0:
                first_pobj = first_pobj_tokens[n-1].text
                # make sure the pobj is not already part of the subject
                if first_pobj not in subject_entity_form:
                    dict_cond_formatted["left_side"] = '$$' + str(first_pobj_tokens[n-1]) + '.' + subject_entity_form
                else:
                    dict_cond_formatted["left_side"] = subject_entity_form
        # if there are more than one pobjs, then get the prep token of the pobj
        # most probably that prep token would act as a sub-condition/clause
        if len(advcl_pobjs) > 1:
            # get prep of the second pobj
            second_pobj_tokens = advcl_pobjs[1]
            n = len(second_pobj_tokens)
            if n > 0:
                prep_tokens = nlu.get_prep_of_pobj(second_pobj_tokens[n-1])
                #dict_cond_formatted["extra_pobj_" + second_pobj_tokens[n-1].text] = prep_token
                dict_cond_formatted["extra_pobj_" + second_pobj_tokens[n-1].text] = get_related_conds_of_prep(doc, prep_tokens[0])
                #dict_subj["extra_pobj"] = True
    return dict_cond_formatted

def get_related_conds_of_prep(doc, prep_token):
    """
    Get the prep objects associated with the prep token.
    Eg: in below  clause (advcl):
     " If the number of days between xxx and yyy is greater than 30 days then .."
     `between` is the prep_token and we need to get `xxx` and `yyy` along with `and`
    """
    related_conds = []
    related_tokens = []
    related_operands = []
    dict_related_conds = {}
    dict_related_conds["condition"] = '$' + prep_token.text
    related_tokens, related_conds = nlu.get_related_pobjs(prep_token)
    if len(related_tokens) > 0:
        related_operands.extend(get_entities_form(doc, related_tokens))    
        dict_related_conds["operands"] = related_operands
    if len(related_conds) > 0 :
        dict_related_conds["conds"] = [cond.text for cond in related_conds]
    return dict_related_conds

def get_right_side_values(doc, cond_token):
    """
    Get right hand side of condition. There are many types of 'dep' that need to be 
    considered to get this. We shall consider tokens associated to the right of the cond_token

    1) attr + negation, if any (Eg: `is not "s", is greater than 30 days`)
    2) dobj + acl (Eg: `has affinity reln associcated` )
    3) prep + pobj (Eg: `was added on a date...`, `associated with policy`)
        3.1) get relcl (relative clause) if present (Eg: `was added on a date that/which is greater than....`)
    """
    dict_right_side = {}
    expression = ''
    # get attr + negation
    attrs, cc, pobjs, neg_texts,cond_expr = nlu.get_attr_and_neg(cond_token)
    # get dobj + acl
    dobjs, acls = nlu.get_dobj_acl(cond_token)
    # get prep + pobj
    prep_dict = nlu.get_prep_and_pobj(cond_token)
    # get relcl if any

    dict_right_side["attr_negation"] = [get_entities_form(doc, attrs), cc, pobjs, neg_texts, cond_expr]
    # find expresssion from attr values
    expression, expr_uom = form_expr_from_attr(doc, get_entities_form(doc, attrs), cc, get_entities_form(doc,pobjs), neg_texts, cond_expr)
    dict_right_side["expression"] = expression
    if expr_uom:
        dict_right_side["expression_uom"] = expr_uom
    
    dict_right_side["dobj_acl"] = [get_entities_form(doc, dobjs), acls]
    dict_right_side["prep_pobj"] = form_expr_from_prep(doc, prep_dict, neg_texts)
    
    return dict_right_side

def form_expr_from_attr(doc, attrs, cc, pobjs, neg_texts, cond_exprs):
    """
    Form expression based on attr and related entities
    """
    neg_present = False
    expression = ''
    expr_uom = None
    expr_present = False
    cc_expr = []
    first_expr = True

    # Check for negation
    if len(neg_texts) > 0:
        expression = '$' + ' '.join(neg_texts) + '('
        neg_present = True
    # form required and/or conditions
    for i in range(len(cc)):
        cc_first_half = '$' + cc[i].text + '('
        cc_second_half = ')'
        cc_expr.append((cc_first_half, cc_second_half))
    i=0
    for cond_expr in cond_exprs:
        
        if i%2 == 0:
            # add first half of and/or condition if present
            try:
                expression += cc_expr[round(i/2)][0]
            except IndexError: # ignore if there no and/or condition
                pass
        # check if there are cond expr (eg: `less than 20`, `greater than`)
        if len(cond_expr) > 0:
            if cond_expr[0]:
                if not first_expr:
                    expression += ','
                expression += '$' + cond_expr[0].text
            if cond_expr[1]:
                expression += ' ' + cond_expr[1].text
                expression += '('
                expr_present = True
            if cond_expr[2]:
                # get entities form of this token
                ent_form_list = get_entities_form(doc,[cond_expr[2]])
                expression += ent_form_list[0]
                # if the cond_expr[2] is not None and if attr is present
                # then the attr element would be `uom`. For example in conditon
                # ` ... less than 30 days`, attr[0] would be `days` and 
                # cond_expr would be (less, than, 30). 
                # in such cases, consider attr as `uom` (days, years, characters etc..)
                if len(attrs) > i:
                    expr_uom = attrs[i]

        # if expr_uom was formed already, then attr was used. so skip any further
        # processing based on attr. Otherwise, continue
        if not expr_uom and len(attrs) > i:
            try:
                expression += ''.join([ pobjs[i], '.' ])
            except IndexError: # ignore if pobj is not present
                pass
            expression += attrs[i]

        # add closing paranthesis if expression was added.
        if expr_present: 
            expression += ')'
            expr_present = False

        if (i+1)%2 == 0:
            # add second half of and/or condition if present
            try:
                expression += cc_expr[round((i/2))][1]
            except IndexError: # ignore if there no and/or condition
                pass
        i += 1
        first_expr = False

    # add closing paranthesis if negation was added
    if neg_present: 
        expression += ')'
        neg_present = False
    

    return expression, expr_uom

def form_expr_from_prep(doc, prep_dict, neg_texts):
    """
    Form expression from prep and pobj.
    """
    expression = ''
    expressions = []
    final_expression = ''
    expr_uom = None
    neg_present = False


    for prep_token, value in prep_dict.items():
        cc_expr = []
        # value is a list of list. 
        # First one has pobjs, second one ccs and the 3rd nummods
        pobjs = value[0] # first list is pobjs
        ccs = value[1] # second list is ccs
        nummods = value[2] # third list is nummods

        # form required and/or conditions
        for i in range(len(ccs)):
            cc_first_half = '$' + ccs[i].text + '('
            cc_second_half = ')'
            cc_expr.append((cc_first_half, cc_second_half))
        i=0
        for one_pobj in pobjs:
        
            if i%2 == 0:
                # add first half of and/or condition if present
                try:
                    expression += cc_expr[round(i/2)][0]
                except IndexError: # ignore if there no and/or condition
                    pass
            #add prep token to the expression
            expression += '$' + prep_token.text + '('
            #find the entities form of the pobj token
            ent_form_list = get_entities_form(doc,[one_pobj])

            if nummods[i]:
                expression += nummods[i].text + ')'
                expr_uom = ent_form_list[0]
            else:
                expression += ent_form_list[0] + ')'

            if (i+1)%2 == 0:
                # add second half of and/or condition if present
                try:
                    expression += cc_expr[round((i/2))][1]
                except IndexError: # ignore if there no and/or condition
                    pass

            i += 1
        expressions.append(expression)
    
    # Check for negation
    if len(neg_texts) > 0:
        final_expression = '$' + ' '.join(neg_texts) + '('
        neg_present = True

    # iterate through all expression and form the final expression
    if len(expressions) > 1:
        final_expression = '$and(' # IMP: this has to be changed. will it be and always?
        for expr in expressions:
            final_expression += expr + ','
        final_expression.strip(',') #strip extra comma, if present
        final_expression = ')'
    elif len(expressions) > 0:
        final_expression = expressions[0]
    
    # add matching paranthesis for negation
    if neg_present:
        final_expression += ')'

    return final_expression, expr_uom

def get_applicability(root_token):
    values = []
    values = nlu.find_left_prep_obj(root_token)
    return [value for value in values if value.pos_.lower() not in POS_TO_IGNORE]

def update_prv_statment(doc, rule_repr):
    """
    Call this function to update previous statement with corrected 'valid_values'.
    For example in rule like this:
    
    `For New Business, Driver age is derived based on the below two attributes.
         Driver birth date.
         Effective date. `
    
    there would be 3 sentences: 1) 'For New...' 2) 'Driver birth..' 3) 'Effective date'
    For sentences 2 & 3, find out the entities and consider them as valid_values
    for sentence 1
    """
    n = len(rule_repr)
    if n < 1:
        return
    old_values_dict = rule_repr[n-1]['rule_valid_values']
    old_values = old_values_dict["value"]
    # check the old values. If they are not entities, delete them
    for value in old_values:
        if value.find("$$") == -1:
            old_values.remove(value)
    # get the entities
    ents = nlu.get_ents(doc)
    old_values.extend(["$$" + ent[0] for ent in ents])
    old_values_dict["value"] = old_values

if __name__ == '__main__':
    run()
