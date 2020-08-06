import PyPDF2
import base64
import json
import mailbox
import requests
import os

from fpdf import FPDF
from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
from pprint import pprint
from zipfile import ZipFile

def parse_json(j, es, filename):
    print('\nParsing: ', filename)
    loaded = json.loads(j)
    meta = loaded.get('meta')

    creatorInfo = {
        'author'       : meta.get('/Author'),
        'wordProcessor': meta.get('/Creator'),
        'creationDate' : meta.get('/CreationDate'),
        'lastModified' : meta.get('/ModDate'),
    }

    del loaded['meta']      #deletes meta from dictionary, leaving only text

    jsonStr = str(loaded)
    jsonStr = jsonStr.replace("\\n", '')
    jsonStr = jsonStr.replace("\\", '')
    jsonStr = jsonStr.lower()
    #print("JSONSTR: ", type(jsonStr))
    parse_string(jsonStr, es, filename, creatorInfo)

def parse_string(_str, es, filename, creatorjson={}):
    #print("_STR: ", type(_str))
    creatorInfo = creatorjson

    wordCount = len(_str.split())
    sus_words = 'susWords.txt'
    totalSus = 0
    drug = 0
    violent = 0
    whiteCollar = 0
    wordArray = []

    with open(sus_words) as file:
        words = file.read().split()

    #Parsing section
    for i in range(0, len(words)):
        start = 0
        while True:
            start = _str.find(words[i], start)
            if start == -1:
                break
            totalSus += 1
            start += len(words[i])

            wordArray.append(words[i])
            if i <= 9:  # These numbers come from the location of selected words
                drug += 1  # From the susWords.txt TODO: MAKE THIS SYSTEM MORE FLEXIBLE
            elif i <= 18:
                violent += 1
            elif i <= 23:
                whiteCollar += 1

    indexBody = {
        "FileText": _str,
        "WordCount": wordCount,
        "TotalSuspicious": totalSus,
        "TotalSuspicious": totalSus,
        "DrugRelated": drug,
        "ViolentCrime": violent,
        "WhiteCollarCrime": whiteCollar,
        "LocatedWords": wordArray,
        "CreatorInfo": creatorInfo
    }

    # Create new PDF
    # newPDF = FPDF()
    # newPDF.add_page()
    # newPDF.set_font("Arial", size=12)
    # newPDF.multi_cell(150, 12, txt=soup_noFormat_lower)
    # filename = "_" + index_name + ".pdf"
    # newPDF.output(filename)

    print("Parsing Complete for:", filename)  # ,"\nNumber of suspicious words:", totalSus)
    indexFile(indexBody, es, filename)

def indexFile(dict, es, index_name):
    print ("\nIndexing under: localhost:9200/files/_doc/", index_name)

    body_doc = dict
    result = es.index(index="files", doc_type="_doc", id=index_name, body=body_doc)
    print("File successfully indexed")
    print("\n============================================")