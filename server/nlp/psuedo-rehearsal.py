import spacy
from spacy.gold import GoldParse
import random, time
from toolz import itertoolz
from pathlib import Path
from ner_build_goldparse import BuildGoldParse
#load existing model...

nlp = spacy.load("D:/Ananth/Allstate/spacy/models/en_core_web_sm-2.0.0/en_core_web_sm/en_core_web_sm-2.0.0")
revision_data = []
training_data = []
other_pipes = []
OUT_DIR = 'D:/Ananth/Allstate/spacy/models/trained'
NEW_MODEL_NAME = 'custom_trained'
#entity_label
LABEL = 'CUSTOM'
#original labels
LABELS_ORIGINAL=['PERSON','NORP', 'FACILITY', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT', \
'WORK_OF_ART', 'LAW', 'LANGUAGE', 'DATE', 'TIME', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']

def initialize_nlp(nlp):
    if 'ner' not in nlp.pipe_names:
        ner = nlp.create_pipe('ner')
        nlp.add_pipe(ner)
    # otherwise, get it, so we can add labels to it
    else:
        ner = nlp.get_pipe('ner')

    ner.add_label(LABEL)   # add new entity label to entity recognizer
    #add original lables also to nlp pipeline
    for label in LABELS_ORIGINAL:
        ner.add_label(label)   
    # get names of other pipes to disable them during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'ner']


def get_revision_text(file_name):
    """
    Randomly select 1000 sentences.
    """
    all_data = None
    revision_texts = []
    indexes = []
    with open(file_name, encoding="utf-8") as file_data:
        all_data = file_data.read()
        all_data_splitted = all_data.split('\n')

    if all_data:
        random.seed(time.clock())
        for x in range(1005):
            i = random.randint(0,len(all_data_splitted)-1)
            indexes.append(i)
            #ignore any blank sentences
            if(len(all_data_splitted[i].strip()) > 0):
                revision_texts.append(all_data_splitted[i])
    return revision_texts    

def get_training_text(file_name):
    all_data = None
    all_data_splitted = []
    with open(file_name, encoding="utf-8") as file_data:
        all_data = file_data.read()
        all_data_splitted = all_data.split('\n')
        return all_data_splitted

def create_revision_data(revision_texts):
    nlp_training = spacy.load("D:/Ananth/Allstate/spacy/models/en_core_web_sm-2.0.0/en_core_web_sm/en_core_web_sm-2.0.0", disable=['parser'])
    
    for doc in nlp_training.pipe(revision_texts):
        #tags = [w.tag_ for w in doc]
        #heads = [w.head.i for w in doc]
        #deps = [w.dep_ for w in doc]
        n = len(doc)
        tags = [None] * n
        heads = [None] * n
        deps = [None] * n
        entities = [(e.start_char, e.end_char, e.label_) for e in doc.ents]
        # add a custom element to indicate this doc has original NERs
        doc.user_data = 'original'
        revision_data.append((doc, GoldParse(doc, tags=tags, heads=heads,
                                            deps=deps, entities=entities)))
    print('deleteing nlp_training model (1)')
    del nlp_training
    return revision_data

def train_model(revision_texts, matches_dict):
    """
    Apply the initial model to raw examples. You'll want to experiment
    with finding a good number of revision texts. It can also help to
    filter out some data.
    """
    revision_data = create_revision_data(revision_texts)
    nlp_training = spacy.load("D:/Ananth/Allstate/spacy/models/en_core_web_sm-2.0.0/en_core_web_sm/en_core_web_sm-2.0.0", disable=['ner'])
    #nlp_training.entity.add_label(LABEL)

    for key, value in matches_dict.items():
       # disable ner for training data
        doc = nlp_training(key)
        n = len(doc)
        tags = [None] * n
        heads = [None] * n
        deps = [None] * n
        # tags = [w.tag_ for w in doc]
        # heads = [w.head.i for w in doc]
        # deps = [w.dep_ for w in doc]
        losses = {}
        entities = [(e[1],e[2], LABEL) for e in value]
        training_data.append((doc, GoldParse(doc, tags=tags, heads=heads,
                                            deps=deps, entities=entities)))
    #delete training module loaded... 
    print('deleting nlp_training model....(2)')
    del nlp_training
    #print(revision_data)
    n_epoch = 5
    batch_size = 120
    


    with nlp.disable_pipes(*other_pipes):  # only train NER
        optimizer = nlp.begin_training()

        for i in range(n_epoch):
            examples = revision_data + training_data
            #examples = training_data
            losses = {}
            random.shuffle(examples)
            for batch in itertoolz.partition_all(batch_size, examples):
                docs, golds = zip(*batch)
                print('progress... training batch:',  i+1*batch_size)
                #print(batch)
                # recreate the doc to avoid a bug in spacy training module do this only for new NER docs
                # do this only for custom NER DOC object. For revision texts based DOC objects, have the 
                # original doc so original NERs remain.
                docs_modified = []
                for doc in docs:
                    if doc.user_data != 'generic':
                        doc = nlp.make_doc(doc.text)
                    docs_modified.append(doc)
                nlp.update(docs_modified, golds, sgd=optimizer, drop=0.35, losses=losses)
    print('training completed... losses:', losses)

    # test the trained model
    test_text = 'What are different Product Type that comes after\
    Conviction date or occurence data of an endorsement insurance? This is New york'
    doc = nlp(test_text)
    print("Entities in '%s'" % test_text)
    for ent in doc.ents:
        print(ent.label_, ent.text)

    # save model to a directory
    output_dir = Path(OUT_DIR)
    if not output_dir.exists():
        output_dir.mkdir()
    nlp.meta['name'] = NEW_MODEL_NAME  # rename model
    nlp.to_disk(output_dir)
    print("Saved model to", output_dir)

    # test the saved model
    print("Loading from", output_dir)
    nlp2 = spacy.load(output_dir)
    doc2 = nlp2(test_text)
    for ent in doc2.ents:
        print(ent.label_, ent.text)
#*-------------------------------------------*
# Code starts from here...
#
bgp = BuildGoldParse()
initialize_nlp(nlp)

training_file = 'D:/Ananth/Allstate/spacy/training/custom-sentdetec-model - Copy.train'
revision_file = 'D:/Ananth/Allstate/spacy/training/corpus - many geners - limited'
entities_file = 'D:/Ananth/Allstate/spacy/source/out - Copy.csv'

revision_texts = get_revision_text(revision_file)
#training_texts = get_training_text(training_file)

matches_dict = bgp.build(training_file, entities_file)

train_model(revision_texts,matches_dict)