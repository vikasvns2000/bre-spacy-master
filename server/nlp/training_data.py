import spacy
import random
import json_processing as jp
import get_train_data as gd

LABEL='CUSTOM'

def initialize_nlp(nlp):
    try:
        if 'ner' not in nlp.pipe_names:
            ner = nlp.create_pipe('ner')
            nlp.add_pipe(ner)
        #otherwise, get it, so we can add labels to it
        else:
            ner = nlp.get_pipe('ner')
            ner.add_label(LABEL)   # add new entity label to entity recognizer    #add original lables also to nlp pipeline
    except Exception as e:
        print("error in initialize_nlp", e)


def training_data():
    TRAIN_DATA_1=gd.get_train_data()
    TRAIN_DATA=TRAIN_DATA_1
    print(TRAIN_DATA_1)

    try:
        nlp = spacy.load("D:/Traning_data/en_core_web_sm-2.0.0/en_core_web_sm-2.0.0/en_core_web_sm/en_core_web_sm-2.0.0")
        initialize_nlp(nlp)
        optimizer = nlp.begin_training() #start training data
        other_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'ner']

        with nlp.disable_pipes(*other_pipes):
            for i in range(20):
                random.shuffle(TRAIN_DATA)
                for text, annotations in TRAIN_DATA:
                    nlp.update([text], [annotations], sgd=optimizer)

        nlp.to_disk("D:/Traning_data/en_core_web_sm-2.0.0/en_core_web_sm-2.0.0/en_core_web_sm/en_core_web_sm-2.0.0")
    except Exception as e:
        print("error ",e)

training_data()