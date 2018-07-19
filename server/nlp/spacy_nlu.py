import spacy
import os
import re
from spacy.symbols import nsubj, nsubjpass, VERB, advcl, prep, pobj, conj, dobj, iobj, auxpass, ADV
from spacy.symbols import punct, attr, acomp, aux, neg, advmod, amod, csubj, csubjpass, mark, oprd, xcomp
from spacy.symbols import npadvmod, acl, quantmod


# regex for to introduce a 'space' when needed
# . followed by If or Else, Set etc.. will introduce a space between . and If or Else
# This is to enable sentence detection properly.
regex_insert_space = re.compile('\.(If|Else|Otherwise|For|Set|No|This|Or|Email)', re.IGNORECASE)
regex_hyphen_sentence = re.compile('-\s+(If\s|When\s)', re.IGNORECASE)
nlp = None
SYMBOLS_FOR_LEMMA_BE = [acomp, oprd, attr]
SYMBOLS_FOR_SUBJECTS = [nsubj, nsubjpass, csubj, csubjpass]
SYMBOLS_FOR_OBJECTS = [dobj, iobj]
SYMBOLS_FOR_MODIFIERS = [acl, amod]
class NLU:

    def find_attributes(self, nlp, str):

        doc = nlp(str)
        #doc = merge_noun_chunks(doc)
        print('')
        root_token, root_text = self.find_root(doc)
        self.find_subject(doc)
        objects = self.find_objects(root_token)
        if len(objects) >  0:
            print('\nObjects of:', root_token)
            print('\t',end='')
            for one_object in objects:
                if one_object is None:
                    print('')
                    print('\t',end='')
                else:
                    print(one_object, end=' ')
            #print('\n')
        conditions = self.find_advcl(root_token)
        if len(conditions) > 0:
            print('\nConditions of:', root_token)
            for condition in conditions:
                if condition is None:
                    print('')
                else:
                    print('\t', condition)
        prep_objs = self.find_prep_obj(root_token)
        if len(prep_objs) >  0:
            print('\nPrep objects of', root_token)
            print('\t',end='')
            for one_object in prep_objs:
                if one_object is None:
                    print('\n','*--------*')
                    print('\t',end='')
                else:
                    print(one_object, end='|')
            print('\n')
        
        left_objs = self.find_left_prep_obj(root_token)
        right_objs = self.find_right_prep_obj(root_token)

        print('left prep objects:', [(obj, obj.ent_type_) for obj in left_objs ] )
        print('right prep objects:', [(obj, obj.ent_type_ ) for obj in right_objs ] )
        # print noun chunks
        print('Noun chunks:', [chunks for chunks in doc.noun_chunks])
        print('*----------------------------------------------------------------------------------*')
        self.get_ents(doc)

    def find_root(self, doc):
            for token in doc:
                    #print(token.text, token.dep_, token.head.text, token.head.pos_,[child for child in token.children])
                    #cond_token = neg_token = None
                    root_text = []
                    if token.dep_=='ROOT':
                        root_text = self.get_root_text(token)
                        print('Root element : ', root_text, token.text) 
                        #return token, ' '.join(root_text)
                        return token, root_text
    
    def get_root_text(self, root_token):
        """
        Find root text from root token.
        Eg: " ... cannot be set to blanks ..." --> root is `be` and root text is `cannot be`
        Eg: " ... is set to blanks ..." --> root is `is` and root text is empty
        Eg: " .. cannot be greater than 20 chars .." --> root is `be` and `cannot be greater than` is the root text
        """
        cond_token = neg_token = None
        root_text = []

        # identify if there are any cond token ie. can, is, are, should etc..
        # but add only `aux` to root text.
        for child in root_token.children:
            if child.dep == aux:
                cond_token = child
                root_text.append(cond_token.lemma_)
            # if both aux and auxpass are present, consider aux as child
            if child.dep == auxpass and cond_token is None:
                cond_token = child

        # Check if there is any negation 
        if cond_token: # (eg: cannot be greater than)
            for child in root_token.children:
                # and (child.i > cond.i):
                #if (child.dep == neg or child.dep == auxpass or child.dep == advmod) and child.i > cond_token.i:
                if (child.dep == neg or child.dep == auxpass or child.dep == advmod) and child.i > cond_token.i: 
                #if (child.dep == neg or child.dep == advmod) and child.i > cond_token.i: 
                    neg_token = child
                    root_text.append(neg_token.lemma_)
        else: # (eg: This rule is not applicable for..)
            if root_token.lemma_ == 'be':
                for child in root_token.rights:
                    # and (child.i > cond.i):
                    if child.dep == neg or child.dep == auxpass or child.dep == advmod : 
                        neg_token = child
                        root_text.append(neg_token.lemma_)
        return root_text
        
    def find_subject(self, doc):
            for token in doc:
                    if( (token.dep == nsubj or token.dep == nsubjpass)   and token.head.pos == VERB):
                            #if(possible_subject.head.lemma_ == 'be'):
                            print('** =>', token.head,'(',token.text, [child for child in token.children], ')')
                            #print('!! =>', [child for child in token.head.rights])
                            #print('** =>', possible_subject.head)


    def find_objects(self, root_token, delimiter=True):
        """ 
        Find all objects associated with the root
        We take direct objects, indirect, conjunction objects and subjects, along with passive subjects.
        do this in recursion to make sure we get all required objects (i.e. all children of children on root)
        Add a delimiter after a child token's recursion is complete so that we know how to group
        if there are more than one objects...
        """
        objects = []
        for child in root_token.children:
            if child.dep == dobj or child.dep == iobj or child.dep == conj or\
            child.dep == nsubj or child.dep == csubj or child.dep == csubjpass or\
            child.dep == nsubjpass:
                #print('objects for (' , root_token.text, ') is: ', child.text,'(doc:', child.i,')')
                objects.extend(self.get_phrase(child))
                #objects.append(child)
                #add token delimiter - a None object
                if delimiter:
                    objects.append(None)
                objects.extend(self.find_objects(child))
                
            # if root_token.lemma_ == 'be' and (child.dep == attr or child.dep == acomp) :
            #     #print('objects for (' , root_token.text, ') is: ', child.text)
            #     objects.extend(self.get_phrase(child))
            #     #objects.append(child)
            #     #add token delimiter - a None object
            #     if delimiter:
            #         objects.append(None)
            #     objects.extend(self.find_objects(child))
            
        return objects

    def get_compound_tokens_old(self, token):
        """
        Find all compound tokens of a given token. Eg: in : "Affinity Card Number", 
        'Affinity' & 'Card' are "compounds" of 'Number' token.
        Note:
        We found that SpaCy's dep parser might have 2 variations of compound elements:
        1. root --> child1, child2, child3
        2. root --> child2 --> child2 --> child3
        so recursion is necessary for 2nd case.
        """
        objects =  []
        for child in token.children:
            if child.dep_ == 'compound' or child.dep == amod:
                objects.extend(self.get_phrase(child))
                #objects.append(child)
        return objects

    def get_phrase(self, token):
        """
        Check if the token falls within any noun_phrase. For example, in below sentence:
            The Start Date cannot be left blank.
        the token 'Date' falls within noun_phrase 'The Start Date'
        if there is no matching phrase, return the original token
        """
        objects = []
        noun_chunks = token.doc.noun_chunks
        for np in noun_chunks:
            if token.i >= np.start and token.i < np.end:
                objects.extend([one_token for one_token in np] )
                return objects
        return [token]

    def find_advcl(self, root_token):
        """
        advcl are dependencies for conditions. Mostly they are sub-sentences or clauses that would 
        start with "if, else, otherwise or when"
        Eg: " set xxxx to yyyy, if zzzz is greater than 20 chars" - in this rule ' if zzzz ...' is 
        advcl that we need.
        
        Also consider these scenario below:
        Eg: 1) " Otherwise, set it to zero" 2) " Else, set last name to blanks"
        these would be simple advmod (adverbial modifiers) but not advcls though.
        """

        objects = []
        for child in root_token.children:
            if child.dep == advcl:
                #print('advcl of ', root_token, 'is: ', child, [child for child in child.children if child.dep != conj ])
                for child_2 in child.children:
                    if child_2.dep != conj:
                        #objects.extend(self.get_phrase(child_2))
                        objects.extend(self.get_phrase(child_2))
                        objects.extend(self.find_prep_obj(child_2))

                        #objects.append(child_2)
                objects.append(child)
                # Add delimiter
                objects.append(None)
                #Check if the child has any conj as children, if so, consider that as well
                for child_2 in child.children:
                    if child_2.dep == conj:
                        #print('advcl of (', root_token, ') is: ', child_2, [child for child in child_2.children])
                        #objects.extend(get_compound_tokens(child_2))
                        #objects.append(child_2)
                        
                        # Find the clause (i.e If or When) for this conjucate)
                        objects.extend([child_3 for child_3 in child_2.children if child_3.dep == advmod or child_3.dep == mark])
                        # find objects of this child and prep objects of these objects
                        objs = self.find_objects(child_2, delimiter=False)
                        
                        for obj in objs:
                            objects.extend(self.find_prep_obj(obj))
                            objects.append(obj)
                        objects.extend(self.find_prep_obj(child_2))

                        #objects.append(child_2)
                        objects.extend(self.get_phrase(child_2))
                        # Add delimiter
                        objects.append(None)
            if (child.dep == advmod or child.pos == ADV) and\
                (child.lemma_ != 'not' and child.lemma_ != 'then'):
                objects.append(child)
                # Add delimiter
                objects.append(None)        
        return objects
    
    def get_advcl_elements(self, advcl_root):
        """
        for very advcl, find below elements:
            1) subject
            2) operation
            3) operand(s)
        """
        dict_subj = {}
        advcl_pobjs = []

        #find subjects & objects of the clause
        advcl_objects = [token for token in advcl_root.children if token.dep in SYMBOLS_FOR_OBJECTS]
        advcl_subjects = [token for token in advcl_root.children if token.dep in SYMBOLS_FOR_SUBJECTS]

        # for every subject, find any 
        pobjs = []
        for subject in advcl_subjects:
            if subject.lemma_.lower() == 'it': # it is a special case to be handled.
                dict_subj[subject] = self.get_attr(advcl_root)
            else:
                advcl_pobjs_raw = self.find_prep_obj(subject, delimiter=True) # get the prep obj associated
                advcl_pobjs = self.get_list_of_lists(advcl_pobjs_raw) # get list of list from list of tokens
                dict_subj[subject] = advcl_pobjs

        return advcl_objects, advcl_subjects, dict_subj

    def get_dobj_acl(self, root_token):
        """
        Get dobj and associated acl.
        
        Eg: in sentence `... has affinity reln associated...`, `has` is the root token
        and `reln` is the dobj and `associated` is the acl
        
        Note: Looks like such dobj can be associated with `amod` sometimes
        Eg: in sentence `.... has valid value...` , `has` is the root token
        and `value` is the dobj and `valid` is the modifier (amod)
        So, along with `acl`, consider `amod` as well.
        """
        objects = []
        acls = []
        
        objects = [token for token in root_token.children if token.dep in SYMBOLS_FOR_OBJECTS]
        # get associated acl
        for obj in objects:
            acl_token = None
            for child in obj.rights:
                #if child.dep == acl:
                if child.dep in SYMBOLS_FOR_MODIFIERS:
                    acl_token = child
                    break
            acls.append(acl_token)
        
        return objects, acls
        
    def get_attr(self, root_token):
        """
        get all attr (attributes) token for the root token
        """
        objects = []
        objects.extend([child for child in root_token.children])
        objects.append(root_token.text + "-----")
        return objects

    def get_attr_and_neg(self, root_token):
        """
        Get attrs associated with the root token and negations if any
        Eg: in clause ` .. is greater than 30 days..`, `is` is the root
        token and `days` is the attr and in clause `... is not "s" ..`
        `is` is the root token and `s` is the attr and `not` is the negation
        
        In some cases, SpaCy's dependency parsing marks the clause with a different
        dep. Eg: in ` ... is greater than 10` the deps are marked as [`acomp`, `prep`, `pobj`].
        So if there is no `attr` associated to the root, then check `acomp`.

        Note: We have to consider only right side tokens of the root, but considering common functions
        that might call this function, we consider all children 
        """
        attrs = []
        cc = []
        pobjs_of_attr = []
        cond_expression = ()
        cond_expressions = []
        
        attrs, cc = self.get_related_tokens(root_token, attr)
        print('attrs in get_attr_neg', attrs)
        for one_attr in attrs:
            pobjs_raw = self.find_prep_obj(one_attr, delimiter=True) # get the prep obj associated
            pobjs = self.get_list_of_lists(pobjs_raw) # get list of list from list of tokens
            if len(pobjs) > 0:
                first_pobj_list = pobjs[0]
                if len(first_pobj_list) > 0:
                    pobjs_of_attr.append(first_pobj_list[0])
            #get condition expression for each attr
            cond_expression = self.get_cond_expr_tokens(one_attr)
            cond_expressions.append(cond_expression)
            #cond_expression.append(self.get_phrase(one_attr))
        if len(attrs) == 0:
            result_acomp = self.get_cond_acomp(root_token)
            cond_expressions.extend(result_acomp[0])
            attrs.extend(result_acomp[1])
            cc.extend(result_acomp[2])

        # get negation if any
        root_text = self.get_root_text(root_token)
        
        return attrs, cc, pobjs_of_attr, root_text, cond_expressions

    def get_prep_of_pobj(self, pobj_token):
        """
        get the prep token for corresponding pobj
        """
        tokens = [ancs for ancs in pobj_token.ancestors if ancs.dep == prep]
        if len(tokens) == 0:
            return None
        else:
            return tokens
    
    def get_prep_and_pobj(self, root_token):
        """
        Get prep and pobj of the root
        Eg: in sentence `... is associated with policy ...` , root_token is `associated`
        , `with` is the prep and `policy` is the pobj.
        """
        dict_preps = {}
        prep_pobjs = []
        nummods = []
        cc = []

        for child in root_token.children:
            if child.dep == prep:
                prep_pobjs = []
                cc = []
                prep_pobjs, cc = self.get_related_tokens(child, pobj)
                # find if there is nummod associated with the pobj
                for prep_obj in prep_pobjs:
                    _ , _ , nummod_obj = self.get_cond_expr_tokens(prep_obj)
                    nummods.append(nummod_obj)
                
                dict_preps[child] = [prep_pobjs, cc, nummods]
        
        return dict_preps
    
    def get_related_pobjs(self, prep_token):
        """
        Get the prep objects associated with the prep token.
        Eg: in below clause (advcl):
        " If the number of days between xxx and yyy is greater than 30 days then .."
        `between` is the prep_token and we need to get `xxx` and `yyy` along with `and`
        """

        return self.get_related_tokens(prep_token, pobj)

    def get_related_tokens(self, root_token, dep_type):
        """
        Get related token of dep = `type` and conjunctions, if any.
        """
        related_conds = []
        related_tokens = []
        if not dep_type:
            return related_tokens, related_conds

        for child in root_token.children:
            if child.dep == dep_type:
                related_tokens.append(child)
            # If there is conjugate, get the conjugate present between root_token and conjugated token
                for child_2 in child.children:
                    if child_2.dep == conj:
                        related_tokens.append(child_2)
                        # find the conjugate cond (i.e. `and`/`or`)
                        for possible_cc in child.rights:
                            if possible_cc.dep_.lower() == 'cc' and possible_cc.i <= child_2.i:
                                related_conds.append(possible_cc)
        
        return related_tokens, related_conds

    def get_cond_expr_tokens(self, attr_token):
        """
        Get condition expression associated with the token
        1) Eg: in sentence `... greater than 20 characters...` `characters` is the 
        attr_token and `greater than 20` is the expression that we need.
        2) Eg: in sentence `... less than 20...`, here `20` will be the attr_token
        and `less than` is the expression that we need.
        """
        expression = ''
        child_amod = None
        child_quantmod = None
        child_nummod = None

        children = [child for child in attr_token.lefts] # consider only left children
        
        # find out if attr_token has nummod, if so, then amod and quantmod
        # will be relative to the nummod token - so modify children list
        # otherwise they are relative to attr_token - so leave the children list as is.
        # 
        # Refer Eg #1 & #2 above

        for child in children:
            # get nummod
            if child.dep_ == 'nummod':
                child_nummod = child
        if child_nummod:
            children = [child for child in child_nummod.lefts] # consider only left children

        for child in children:
            # get amod
            if child.dep == amod:
                child_amod = child
            # get quantmod
            if child.dep == quantmod:
                child_quantmod = child
            
        #expression = ' '.join[child_amod.text, child_quantmod.text, child_nummod.text] 
        return (child_amod, child_quantmod, child_nummod)

    def get_cond_acomp(self, root_token, self_called=False):
        """
        Get tokens for cond expression based on `acomp`
        
        Eg: in ` ... is greater than 10` the deps are marked as [`acomp`, `prep`, `pobj`].
        
        Also, consider conjugated conditions:
        eg: `... is greater than 1800 and lesser than 2000`. Here we found that SpaCy marks
        the dep differently for conjugated conditions (i.e after `and` clause ). So a hybrid approach
        has been used making this function complicated (and un-readable!!)
        """
        cond_exprs = []
        cond_uoms = []
        ccs = []
        
        nummod_token = None
        child_acomp = None
        child_prep = None
        child_pobj = None
        

        children = [child for child in root_token.rights] # consider rights only
        
        for child in children:
            # if called in recursion, dep will be `conj`
            if self_called:
                if child.dep == conj:
                    child_acomp = child
                if child.dep_ == 'cc':
                    ccs.append(child)
            # if called from external function, dep will be `acomp`
            else: 
                if child.dep == acomp:
                    child_acomp = child
                    break

        if child_acomp:
            for child_2 in child_acomp.rights:
                if child_2.dep == prep:
                    child_prep = child_2
        
        if child_prep:
            for child_3 in child_prep.rights:
                if child_3.dep == pobj:
                    child_pobj = child_3
                    # check if this pobj has a `nummod` child. If yes, then the pobj will be uom
                    # and num mode will become pobj
                    # eg: in condition `... greater than 10 years and less than 20 years`
                    # `years` will be original pobj and `10` will be the nummod
                    nummod_token = self.get_nummod(child_pobj)
        
        if nummod_token:
            cond_exprs.append( (child_acomp, child_prep, nummod_token) )
            cond_uoms.append(child_pobj)
        else:
            cond_exprs.append( (child_acomp, child_prep, child_pobj) )
        
        # call recursively to identify any conjugated conditions:
        # eg: `... greater than 2000 and lesser than 3000`. 
        if child_pobj:
            
            returned_tuple = self.get_cond_acomp(child_pobj, self_called=True)
            # Sometimes SpaCy marks such conjugated dependencies different from previous condition
            # i.e. in sentence `... greater than 2000 and lesser than 3000`, first conditon (greater)
            # will be marked as [acomp, prep, pobj] whereas the second contion (lesser) will be 
            # marked as [amod, quantmod, nummod]. So try both methods to get required conditions.
            temp_exprs = returned_tuple[0][0]
            print('temp_exprs is: ', temp_exprs)
            if len(temp_exprs) > 0 and not temp_exprs[2]: # if pobj returned is None, call a different method to get the values.
                if temp_exprs[0]: # should be present, but just in case..
                    cond_expr = self.get_cond_expr_tokens(temp_exprs[0])
                    # if cond_expr has nummod, i.e. then uom can be formed.
                    if cond_expr[2]:
                        cond_uoms.append(temp_exprs[0])
                        cond_exprs.append(cond_expr)
                    else:
                        cond_exprs.append( (cond_expr[0], cond_expr[1], temp_exprs[0]) )
                ccs.extend(returned_tuple[2])

            else: # 
                cond_exprs.extend(returned_tuple[0])
                cond_uoms.extend(returned_tuple[1])
                ccs.extend(returned_tuple[2])

        return cond_exprs, cond_uoms, ccs

    def get_nummod(self, root_token):
        """
        Return nummod dep associated with the token
        """
        for child in root_token.lefts: # nummod will be present in left of root_token
            if child.dep_ == 'nummod':
                return child
        
        return None

    def get_np_advmod(self, doc):
        """
        find if there are any noun phrases that are associated with adv clause modifiers.
        Eg: in sentence " ... doesnt have affinity associated then xxx and yyy are set ... "
        here, xxx and yyy are the items we need.
        
        Note: this is a hack to be used when the root token in not directly linked to these nps.
        Also we found that spacy was able to link the root token to the np directly if there is 
        a comma (,) in the adv clause like this:
            " ... doesnt have affinity associated, then xxx and yyy are set ... "
        """
        objects = []
        for token in doc:
            if token.dep == npadvmod:
                objects.extend(self.get_phrase(token))
                objects.extend(self.find_objects(token))

        return objects
    def get_amod(self, root_token):
        """
        Get any amod (adjectival modifiers) for the root token

        """
        adv_mods, _ = self.get_related_tokens(root_token, amod)

        return adv_mods

    def get_rel_clause(self, objs):
        """
        Find if the the object has any relative clause. For example,
        in sentence: `.... set with/to values that are already present ...`
        here, the token `values` is the object of concern and `that are already present`
        are the the tokens that form relative clause.
        """
        dict_tokens = {}
        i = 0
        for obj in objs:
            tokens = []
            for child in obj.rights: # consider only right tokens
                if child.dep_.lower() == 'relcl':
                    # get all children of that child + the child
                    tokens.extend(self.get_children_recurse(child, direction='left'))
                    tokens.append(child)
                    tokens.extend(self.get_children_recurse(child, direction='right'))
                    dict_tokens['idx_'+str(i)] = tokens
        return dict_tokens

    def get_to_clause(self, root_token):
        """
        Get TO-clause tokens.
        Eg: "... , set to blanks."
        Here, the token 'blanks' is the to-clause token
        """
        to_clause_tokens = []
        for child in root_token.rights:
            if child.dep == xcomp:
                to_clause_tokens.append(child)
        
        return to_clause_tokens

    def get_right_dative_pobj(self, root_token):
        """
        Get dative pobj of the root token.
        Eg: in sentence ` .... set smart student code to "A" `, `set` is the 
        root token and `A` is the right dative pobj associated with it.

        Note:We only consider tokens that are right of root token.
        """
        objects = []
        for child in root_token.rights:
            if child.dep_ == 'dative':
                for child_2 in child.children:
                    if child_2.dep == pobj:
                        objects.append(child_2)
        return objects

    def get_pobj(self, prep_token, delimiter):
        objects = []
        for child  in prep_token.children:
    # If punctuation, then get the next token, so continue...
            if child.dep == punct:
                continue
            elif child.dep == pobj:
                objects.extend(self.get_phrase(child))
                if delimiter: # add delimiter
                    objects.append(None)
                #objects.append(child)
    # If prep, then get the child of that child... 
    # (eg: " set to 'R' ", here 'to' is a prep, but we need 'R')
            elif child.dep == prep:
                objects.extend(self.get_pobj(child, delimiter))
            else:
                #return None
                pass
        return objects

    def find_left_prep_obj(self, root_token):
        """
        Find prep objects that are in the left of root
        """
        return self.find_prep_obj(root_token, "left")

    def find_right_prep_obj(self, root_token):
        """
        Find prep objects that are in the right of root
        """
        return self.find_prep_obj(root_token, "right")

    def find_prep_obj(self, root_token, direction=None, delimiter=False):
        """
        Find prepositonal modifiers of root element.
        In statement, "For OR, if the xxx is valid, the yyy will be set to 'G'." ,
        the root element is 'set' and prep objects are 'OR' and 'G'
        """
        objects = []
        if direction == "left":
            child_tokens = [child for child in root_token.lefts]
        elif direction == "right":
            child_tokens = [child for child in root_token.rights]
        else:
            child_tokens = [child for child in root_token.children]

        for child in child_tokens:
            if child.dep == prep:
                #print('prep obj of (', root_token, ') is: ', get_pobj(child))
                objects.extend(self.get_pobj(child, delimiter))
        return objects

    def merge_noun_chunks(self, doc):
        for np in doc.noun_chunks:
            #np.merge(np.root.tag_, np.text, np.root.ent_type_)
            np.merge(ent_type = np.root.ent_type_, tag = np.root.tag_ )
        return doc

    def get_ents(self, doc):
        ents = [(ent.text, ent.label_) for ent in doc.ents if ent.text !='\n']
        print('Entities:', ents)
        return ents

    def get_children_recurse(self, token,direction=None):
        """
        Get children of a token recursively...
            use this when you need to get all tokens to the left or right till
            the end of or beginning of sentence - i.e. beyond 'token's syntactic
            continuity.
        """
        objects = []
        if direction == 'right':
            children = token.rights
        elif direction == 'left':
            children = token.lefts
        else:
            children = token.children
        
        for child in children:
            if direction == 'right':
                objects.extend(self.get_phrase(child))
            objects.extend(self.get_children_recurse(child, direction))
            if direction == 'left':
                objects.extend(self.get_phrase(child))
        
        return objects


    def get_covered_entity(self, doc, token):
        """
        Check if the token falls within entity.
        """
        for ent in doc.ents:
            if token.i >= ent.start and token.i < ent.end:
                return ent
        return None
    
    def find_tokens_for_be(self, root_token):
        """
        Find tokens associated with lemma 'be'. 
        For example in sentences ' Product Type cannot be left blank '
        the token 'blank' is what we need.
        """
        objects = []
        for child in root_token.children:
            if child.dep in SYMBOLS_FOR_LEMMA_BE:
                objects.extend([child_2 for child_2 in child.children])
                objects.append(child)
        print('for be... objects list is:', objects)
        return objects
    
    def find_verb_presence(self, doc):
        """
        Find if the doc has at least one VERB
        """
        verbs = [token for token in doc if token.pos == VERB]
        if len(verbs) > 0:
            return True
        else:
            return False
    def get_list_of_lists(self, lists_tokens, delimiter=None):
        """
        Given a list containing objects/tokens that are separated by a delimiter,
        return list of lists - after removing the delimiter
        """
        one_list = []
        lists = []
        # form a list of list of condition tokens. 'None' will work
        # as delimiter object betweeen multiple conditions.
        for token in lists_tokens:
            if token is delimiter:
                lists.append(one_list)
                one_list=[]
            else:
                one_list.append(token)

        return lists

    def introduce_space(self, text):
        text = regex_insert_space.sub(r'. \1',text)
        return text

    def introduce_new_line(self, text):
        text = regex_hyphen_sentence.sub(r'. \1', text)
        return text

    def get_nlp(self, modelPath=None):
        #nlp = spacy.load("D:/Ananth/Allstate/spacy/models/en_core_web_sm-2.0.0/en_core_web_sm/en_core_web_sm-2.0.0")
        #nlp = spacy.load("D:/Ananth/Allstate/spacy/models/en_core_web_md-2.0.0/en_core_web_md/en_core_web_md-2.0.0")
        
        #nlp = spacy.load(modelPath)
        my_path = os.path.abspath(os.path.dirname(__file__))
        model_path = os.path.join(my_path, "models/trained")
        #model_path = os.path.join(my_path, "spacy-models/en_core_web_md-2.0.0/en_core_web_md/en_core_web_md-2.0.0")
        nlp = spacy.load(model_path)
        #nlp = trained.load()
    
        pipes = [pipe for pipe in nlp.pipe_names]
        print('pipes... ' , pipes)
        return nlp

    def cleanup_text(self, one_rule):
        #clean up the data
        one_rule = one_rule.replace('\t', '\n')
        #print(one_rule)
        #print('-----------------------')
        one_rule = re.sub(r"[\r\n]+","\n",one_rule)
        # print(one_rule)
        # print('-----------------------')
        one_rule = re.sub(r"\n[ ]*[\n]+","\n",one_rule)
        # print(one_rule)
        # print('-----------------------')
        one_rule = re.sub(r"\n[ ]*","\n",one_rule)
        # print(one_rule)
        # remove non-ASCII Characters - is this OK to do????
        one_rule = re.sub(r'[^\x00-\x7F]+',' ', one_rule)
        #one_rule = re.sub(r'\x91','&&&&',one_rule)
        # print('-----------------------')

        # introduce space if necessary..
        one_rule = self.introduce_space(one_rule)
        # introduce new line if necessary..
        one_rule = self.introduce_new_line(one_rule)

        # remove {LINK ....}
        one_rule = re.sub(r'{LINK.*}','',one_rule)
        # remove anything within paranthesis + paranthesis.. i.e. `(<anything inside>)`
        one_rule = re.sub(r'\(.*\)','',one_rule)
        one_rule = one_rule.strip()
        # print('^^^', one_rule, '$$$')
        # print('-----------------------****')
        #print(one_rule.split("\n"))

        #print(re.findall(r'\u0xe2\u0x20ac\u0x2122',one_rule))
        #one_rule.find(u";u0xe2")
        #str1 = one_rule[85:88]
        #print (str1)
        #print("".join(hex(ord(n)) for n in str1))
        return one_rule
    #--------------------------------------------------------------------------------------------------------------------#

    def get_doc(self, nlp, one_rule, clean=False):
        if clean:
            one_rule = self.cleanup_text(one_rule)
        return nlp(one_rule)

    def do_not_call(self):

        nlp = self.get_nlp()

        one_rule = u''+open('D:/Ananth/Allstate/spacy/input/OneRule - Copy.txt').read()


        doc = self.get_doc(nlp, one_rule, clean=True)

        for sent in doc.sents:
            #print('-->', str(sent).replace("\n",""), '<--')
            #print('\n', str(sent), 'root (', sent.root, ')')
            print('\n', str(sent))
            self.find_attributes(nlp, str(sent))
        #print('--------------------------------')

