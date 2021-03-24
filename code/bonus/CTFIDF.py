# -*- coding: utf-8 -*-
"""CTFIDF.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_l3Lxjk8aJ1gTe61eFUpcJtzMrZwPF5q
"""

import sys
import shutil
import re
import math
from collections import Counter
# shutil.rmtree('TF_index')
# !zip -r TF_index.zip CTF_index
# !unzip TF_index.zip
!pip install pyspark
from pyspark import SparkContext, SparkConf

# create Spark context with necessary configuration
conf = SparkConf()
conf.setMaster('local')
conf.setAppName('TF/IDF')
sc = SparkContext.getOrCreate(conf=conf)

# read data
# Edit file name to give your input data
dataFile = '2.txt'
stopWordFile = 'stopwords-en.txt'
# create RDDS, read stopwords file
fileRDD = sc.textFile(dataFile)

# Remove punctutaion function

def lower_clean_str(x):
  punc='!"#$%&\'()*+,;=?@[]^_`{|}~-'
  # punc='!"#$%&\'()*+,./:;<=>?@[\\]^_`{|}~-'
  lowercased_str = x.lower()
  for ch in punc:
    lowercased_str = lowercased_str.replace(ch, ' ')
    lowercased_str = ' '.join(lowercased_str.split())
  return lowercased_str
def lower_clean_str1(x):
  # punc='!"#$%&\'()*+,;=?@[]^_`{|}~-'
  punc='!"#$%&\'()*+,./:;<=>?@[\\]^_`{|}~-'
  lowercased_str = x.lower()
  for ch in punc:
    lowercased_str = lowercased_str.replace(ch, ' ')
    lowercased_str = ' '.join(lowercased_str.split())
  return lowercased_str

#Run remove punctuation function on data
fileRDD = sc.textFile(dataFile)
fileRDD = fileRDD.map(lower_clean_str)

# Remove urls
def remove_urls_tags(x):
  regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
  # regex = 'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
  url_str = re.sub(regex, " ", x)
  html_regex = r"<.*?>"
  finalStr = re.sub(html_regex, " ", url_str)
  return finalStr

fileRDD = fileRDD.map(remove_urls_tags)
fileRDD = fileRDD.map(lower_clean_str1)

# Remove stop words function
def remove_stop_words(stri):
  with open(stopWordFile,'r') as stop:
    stop_w = stop.read()
    #splitting stopwords.txt by new line
    stop_list = re.split('\n', stop_w)
    for word in stop_list:
        if word in stri:
            stri = stri.replace(" "+ word + " ", " ")
    return stri
    
fileRDD1 = fileRDD.map(remove_stop_words)
fileRDD1 = fileRDD1.map(lambda line : line.strip())
# fileRDD1.take(10)

def split_file(line):
    spl = line.split(" ", 1)
    return (spl[0], spl[1])
dfRDD = fileRDD1.map(split_file)

# 1. construct the above RDD into: Construct TF
# calculating log-weighted term frequencies of each word (w)
def tf_construct(line):
    res = []
    skip = ['']
    words = [word for word in line[1].split(" ") if word not in ['']]
    counter  = Counter(words)
    result = [(k, (line[0], 1+math.log10(v))) for k, v in counter.items()] 
    return result

tf = dfRDD.flatMap(tf_construct)
tfReduce = tf.groupByKey().map(lambda x : (x[0],list(x[1])))
# tfReduce.take(2)

# calculate IDF
N = fileRDD1.count()
prd3 = tfReduce.map(lambda x : (x[0], len(x[1])))
IDF=prd3.map(lambda x: (x[0],math.log10(N/(1+x[1]))))

# Join tf and IDF together
joinTFIDF = tfReduce.join(IDF)
# joinTFIDF.take(5)

# 2. Now multiply each freq value with idf value to get TF-IDF score of each word
# which transform the RDD into:
# (word, ([(doc-1, tf-idf), (doc-2, tf-idf), (doc-3, tf-idf), ...]))
def extract_join(jd):
    wrd = jd[0]
    lis = jd[1][0]
    idf = jd[1][1]
    li =[]
    for x in lis:
      li.append((x[0], ((float)(x[1]) *(float)(idf))))
    return (wrd,li)

tfIDFFinal = joinTFIDF.map(extract_join)
# tfIDFFinal.take(2)

# 3.  Follow the same procedure given in Task – 2 to cosine normalize the construct the normalized TFIDF index of format:
# (word, ([(doc-1, weighted_tf-idf), (doc-2, weighted_tf-idf), ...]))

def tf_construct(line):
    mul = [(k, v*v) for k,v in line[1]]
    li = [v[1] for v in mul]
    eucl=math.sqrt(sum(li))
    result = [(line[0], (str(k) + "#"+ str(v/eucl))) for k, v in mul]
    return result

tf = tfIDFFinal.flatMap(tf_construct)
CTFIDF_indexRDD = tf.groupByKey().map(lambda x : (x[0]+"@"+"+".join(list(x[1]))))
# CTFIDF_indexRDD.take(5)

####################### 4.  Write this RDD to CTFIDF_index directory.
CTFIDF_indexRDD.saveAsTextFile('CTFIDF_index')
