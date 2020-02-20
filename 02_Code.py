
# 1 - Packages

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
nltk.download('stopwords')
from flask import Flask, jsonify, request, redirect
import os
## 2 - Read Data

full_path = os.path.realpath(__file__)
path, filename = os.path.split(full_path)
df_file = pd.read_csv(path+'/jobs_data.csv')

print("First 5 entery of our Data\n", df_file.head())
df_file = df_file.drop_duplicates(subset='title')


'''
# PreProcessing Data

## before we start to take a step  we need to handle our data

**some of these handles are:**
    - braces
    - punctuation
    - quotes
    - Tokenization — convert sentences to words
    - Stemming  back word to its root like studying - study
    -  under_score ,stop words and other depends on user input because our data cleaned some of these 

'''

def clean_text(words):
    '''
    a fcuntion return cleaned text from punctuation, braces, quotes and others
    argument:
        string of words
    return:
        cleaned string
    '''
    words = list(words)
    reqular_expression = '][,"\'/-_'
    cleaned_words = ""
    for word in words:
        one_cleaned_word = ""
        word = word.replace('/', ' ')
        word = word.replace(']', ' ')
        word = word.replace('[', ' ')
        for c in word:
            if not c.isdigit() and c not in reqular_expression:
                one_cleaned_word +=c
        cleaned_words +=one_cleaned_word
    return cleaned_words

def remove_stop_words(words):
    '''
    a function return list of words without stop words
    stop words like the,and, over and others english stopwords
    argument:
        string of words
    return:
        list of words
    '''
    words = word_tokenize(words)
    stop_words = set(stopwords.words('english'))
    words = [w for w in words if not w in stop_words]
    return words


def file_cleaning(file):
    '''
    a function that return over all cleaned file
    argument:
        csv file
    return:
        cleaned file
    '''
    for key, value in file.iterrows():
        value['title'] = clean_text(value['title'])
        value['jobFunction'] = clean_text(value['jobFunction'])
        cleaned_title = remove_stop_words(value['title'])
        cleaned_function = remove_stop_words(value['jobFunction'])
        value['title'] = ' '.join(map(str,cleaned_title)).lower()
        value['jobFunction'] = ' '.join(map(str,cleaned_function)).lower()
    return file


def compute_jaccard_similarity_score(x, y):
    """
        a function to return similarities between two string
    argument:
        x as  string which user_job_title
        y for each of job title in our file
    """
    intersection_cardinality = len(set(x).intersection(set(y)))
    union_cardinality = len(set(x).union(set(y)))
    return intersection_cardinality / float(union_cardinality)


def weighted_similarity(job_title, title_list):
    '''
    function take a string and comapre its similarity
    similarity for each job title with this title
    argument:
        user job_title, and all of our job_title
    return:
        sordted list of set with the weights and the index meet this weight in our data 
    '''
    weighted_similarity = []
    for indx, title in enumerate(title_list):
        weights = compute_jaccard_similarity_score(title, job_title)
        weighted_similarity.append((weights, indx))
        weighted_similarity.sort(reverse=True)
    return weighted_similarity


def most_related_jobFunction(job_title, df_file_updated):
    '''
        this function return most frequent job function to user
        argument:
            user job_title, our data file
        return:
            most related 5 job function
    '''
    all_related_weighted_similarity = weighted_similarity(job_title, df_file_updated['title'])
    most_related_jobs = []
    for job in range(0, 2):
        most_related_jobs.append(df_file_updated['jobFunction'][all_related_weighted_similarity[job][1]])
    return most_related_jobs


def recommendation_model(file_to_clean, user_job_title):
    '''
        1 - clean the file data
        2 - read cleaned file
        3-  remove null values from cleaned file
        4 - get related job function
        argument:
            file we need to clean for our recommendation
        return:
            related job function
        
    '''
    df_file = file_to_clean.drop(['Unnamed: 0', 'industry'],axis=1)
    df_file = file_cleaning(df_file)
    
    full_path = os.path.realpath(__file__)
    path, filename = os.path.split(full_path)
    
    df_file.to_csv(path + '/jobs_data_updated.csv', index=False)
    df_file_updated = pd.read_csv(path+ '/jobs_data_updated.csv')
    
    df_file_updated =  df_file_updated.dropna()
    
    user_job_titl = user_job_title
    most_jobfunction = most_related_jobFunction(user_job_title, df_file_updated)

    return most_jobfunction

app = Flask(__name__)
@app.route('/job_function/', methods=['GET'])

def job_function():
    Job_title = request.args['Job_title']
    Job_title = clean_text(Job_title).lower()
    most_jobfunction = recommendation_model(df_file, Job_title)
    job_functions= set()
    for val in most_jobfunction:
        words = remove_stop_words(val)
        for word in words:
            job_functions.add(word.upper())
    job_functions = list(job_functions)
    return jsonify({"Most Related function for job title of "+str(Job_title): job_functions})



@app.route('/', methods=['GET'])

def job_title():
    Job_title = request.args['Job_title']
    return redirect("http://0.0.0.0:8055/job_function/?Job_title="+Job_title, code=302)

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8055)
