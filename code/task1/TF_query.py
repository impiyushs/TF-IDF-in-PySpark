# -*- coding: utf-8 -*-
"""TF_query.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1havJOhQUsFs01KRp2toiRKBUZHI1mMfV
"""

import sys
import re
from collections import Counter
!pip install pyspark
from pyspark import SparkContext, SparkConf
from random import randint
import shutil
# shutil.rmtree('')
# !unzip TF_index.zip
conf = SparkConf()
conf.setMaster('local')
conf.setAppName('TF/IDF')
sc = SparkContext.getOrCreate(conf=conf)

# Read TF_index
def st_to_dict(line):
  line = line.split("@")
  line1 = line[1].split("+")
  return (line[0], line[1])

# read data
# Edit file name to give your input data
dataFile = 'TF_index'
# create RDDS, read stopwords file
stopWordFile ='stopwords-en.txt'
tf_RDD = sc.textFile(dataFile)

tf_RDD1 = tf_RDD.map(st_to_dict)

############## Pre process

# Remove punctutaion function

def lower_clean_str(x):
  punc='!"#$%&\'()*+,;=?@[]^_`{|}~-'
  # punc='!"#$%&\'()*+,./:;<=>?@[\\]^_`{|}~-'
  lowercased_str = x.lower()
  for ch in punc:
    lowercased_str = lowercased_str.replace(ch, ' ')
    lowercased_str = ' '.join(lowercased_str.split())
  return lowercased_str

def lower_clean_str2(x):
  # punc='!"#$%&\'()*+,;=?@[]^_`{|}~-'
  punc='!"#$%&\'()*+,./:;<=>?@[\\]^_`{|}~-'
  lowercased_str = x.lower()
  for ch in punc:
    lowercased_str = lowercased_str.replace(ch, ' ')
    lowercased_str = ' '.join(lowercased_str.split())
  return lowercased_str


def remove_urls_tags(x):
  regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
  url_str = re.sub(regex, " ", x)
  html_regex = r"<.*?>"
  finalStr = re.sub(html_regex, " ", url_str)
  return finalStr

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

# Preprocess function
def pre_process(fileRDD):
  #Run remove punctuation function on data
  fileRDD = fileRDD.map(lower_clean_str)
  # Remove url_tags
  fileRDD = fileRDD.map(remove_urls_tags)
  fileRDD = fileRDD.map(lower_clean_str2)
  #Remove stop words
  fileRDD1 = fileRDD.map(remove_stop_words)
  fileRDD1 = fileRDD1.map(lambda line : line.strip())
  return fileRDD1

qids=set()
# boolean variable for while check
if_query=True

#while incoming queries
while(if_query):
  #user submits a query
  qry=input("Enter Query")
  a = True
  # Generate randome qID
  while(a):
     qID=0
     _id=randint(100,999)
     if _id not in qids:
        qids.add(_id)
        a=False
        qID=_id
  #convert query to RDD
  rdd = sc.parallelize([qry])
  # all text pre-processing, given in Step-1
  prdqry=pre_process(rdd)
  prd1 = prdqry.collect()
  prd1 = prd1[0].split(" ")
  # Filter the RDD such that  contains only words that are present in the given query
  prd2=tf_RDD1.filter(lambda x: str(x[0]) in prd1)
  prd3=prd2.map(lambda x:x[1])
  prd4=prd3.flatMap(lambda y:y.split('+'))
  #  Function to break tuple
  def break_tup(tp):
    li = tp.split("#")
    return (li[0], float(li[1]))
  # Now transform the RDD so that it will be of format: (doc. ID, freq)
  prd5 = prd4.map(break_tup)
  # For each doc. ID, sum all freq values. Now we have single weight for each valid doc. ID
  prd5=prd5.reduceByKey(lambda x,y:x+y)
  # For each doc. ID, sum all freq values. Now we have single score for each valid doc. ID
  # Sort the RDD by value in decreasing order
  writeRDD = prd5.reduceByKey(lambda a,b: a+b).sortBy(lambda a: a[1],ascending=False).map(lambda x : x[0]).take(10)
  writeRDD=sc.parallelize(writeRDD)
  # results into a directory named qID
  writeRDD.saveAsTextFile(str(qID))
  #  Continue queries ?
  nextQR=input('Continue ? Enter Y or N')
  if_query = True if (nextQR=="Y" or nextQR=="y") else False