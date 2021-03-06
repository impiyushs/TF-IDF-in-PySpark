# -*- coding: utf-8 -*-
"""TF.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Jc6UIX7wADmuPzZIsVoBfsQOZm9aFsKB
"""

import sys
import shutil
import re
import math
from collections import Counter
# shutil.rmtree('TF_index')
# !zip -r TF_index.zip TF_index
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

# split file
def split_file(line):
    spl = line.split(" ", 1)
    return (spl[0], spl[1])
dfRDD = fileRDD1.map(split_file)

# construct the above RDD into:
# word@doc-1#freq+doc-2#freq+doc-3#freq+...
def tf_construct(line):
    res = []
    skip = ['']
    words = [word for word in line[1].split(" ") if word not in ['']]
    counter  = Counter(words)
    result = [(k, (str(line[0]) + "#"+ str(1+math.log10(v)))) for k, v in counter.items()] 
    return result

tf = dfRDD.flatMap(tf_construct)
tfReduce = tf.groupByKey().map(lambda x : (x[0]+"@"+"+".join(list(x[1]))))

####################### step 2 output. Write this RDD to TF_index directory.
tfReduce.saveAsTextFile('TF_index')
