import PyPDF2
import base64
import json
import mailbox
import requests
import time
import os

from fpdf import FPDF
from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
from pprint import pprint
from zipfile import ZipFile
from parse_and_index import parse_json
from parse_and_index import parse_string

def connect_elasticsearch():
    print('Connecting to server...')

    _es = None
    _es = Elasticsearch([{
        'host': 'localhost',
        'port': 9200
    }])

    # .ping pings the server and returns True if connected
    if _es.ping():
        print('Connected to server')
    else:
        print('Unable to connect to server')

    return _es

def unzip_file(z):
    zipFile = z
    i = 0

    with ZipFile(zipFile, 'r') as zip:
        for name in zip.namelist():
            file = zip.extract(name)
            handle_new_file(name)

def handle_new_file(file):
    split = file.split('.')  # Converts from "filename.ext" to "filename" str
    filename = split[0].lower()
    if len(split) > 1:
        ext = split[1].lower()

        if ext == 'pdf':
            prepare_PDF(file, filename)
        elif ext == 'txt':
            prepare_txt(file, filename)
        elif ext == 'mbox':
            prepare_mbox(file)
        else:
            print('Unknown file type: ', ext)
    else:
        print('No extension, disregarding')

    # TODO: Remove this try/catch block
    # I'm not sure what the exception here is, but it needs to be dealt with
    try:
        os.remove(file)
    except Exception as ex:
        print("PEPEPE", ex)

def prepare_PDF(pdf, filename):
    file = pdf

    # I think this block is going to have to stay
    # In the event that a file is corrupted in some way we need to
    # be able to handle it. I don't think there is any way to fix
    # it generically within the code
    try:
        read_pdf = PyPDF2.PdfFileReader(file, strict=False)  # Possible break: Corrupted file (can't open)
        if read_pdf.isEncrypted:
            read_pdf.decrypt('')  # Possible break: decryption failure

        pdf_meta = read_pdf.getDocumentInfo()

        # print("META: ", pdf_meta, type(pdf_meta))
        num = read_pdf.getNumPages()
        # print("PDF pages: ", num)
        all_pages = {}  # Dictionary for page data
        all_pages["meta"] = {}  # Put meta data into a dict key

        for meta, value in pdf_meta.items():  # Possible break: Nonetype for some reason (not iterable)
            # print(meta, value)
            all_pages["meta"][meta] = value

        for page in range(num):
            data = read_pdf.getPage(page)
            page_text = data.extractText()  # extract page's text
            all_pages[page] = page_text  # put text data into the dict

        json_data = json.dumps(all_pages)  # converts JSON to String
        # print("\nJSON: ", json_data, 'Type: ', type(json_data))
        parse_json(json_data, es, filename)
    except Exception as ex:
        # TODO: Work on a decryption algorthim
        # (gonna be hard bc this is a transcript encryption)
        if type(ex) is TypeError:
            print("TypeError detected, assuming indirect object. Discarding...")
        else:
            print("Unknown Error:", ex)
        return

#######################################################

    #TODO: Fix IndeirectObject TypeError
    #This error block exists only to allow the program to actually run
    #There is a major bug with handling Indirect Objects that I have to figure out
    #This simply discards them

#######################################################

def prepare_txt(txt, filename):
    with open(txt) as file:
        text = file.read()

    os.remove(txt)
    parse_string(text, es, filename)

def prepare_mbox(_mbox):
    mbox = mailbox.mbox(_mbox)
    print("Parsing .mbox file:", _mbox)
    numMessages = mbox.__len__()
    numParsed = -1
    last = -1
    for message in mbox:
        numParsed += 1
        percentage = round((numParsed / numMessages) * 100)
        if percentage != last and (percentage % 10 == 0):
            print(percentage, "% complete...")
            last = percentage

        body = None
        fb = None
        filename = "Not Found"
        attachments = []
        if message.is_multipart():
            for part in message.walk():  # walks through sub parts
                if part.is_multipart():
                    for subpart in part.walk():
                        if subpart.get_content_type() == 'text/plain:':
                            body = subpart.get_payload(decode=True)

                elif part.get('Content-Disposition') is not None or not 'inline':
                    filename = part.get_filename()
                    if filename is not None:
                        try:
                            fb = open(filename, 'wb')
                            fb.write(part.get_payload(decode=True))
                            fb.close()
                            # print(fb.name)
                            attachments.append(fb.name)
                        except Exception as ex:
                            print(ex)
                            #tally_errors(ex, filename)

                elif part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True)

        elif message.get('Content-Disposition') is not None or not 'inline':
            filename = message.get_filename()
            if filename is not None:
                try:
                    fb = open(filename, 'wb')
                    fb.write(message.get_payload(decode=True))
                    fb.close()
                    # print(fb.name)
                    attachments.append(fb.name)
                except Exception as ex:
                    print(ex)
                    #tally_errors(ex, filename)

        elif message.get_content_type() == 'text/plain':
            body = message.get_payload(decode=True)

        emailInfo = {
            "Sender": message['from'],
            "Subject": message['subject'],
        }



        global ID
        ID += 1
        parse_string(str(body), es, ID, emailInfo)

        for file in range(0, len(attachments)):
            if filename is not None:
                handle_new_file(attachments[file])

if __name__ == '__main__':
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/83.0.4103.116 Safari/537.36',
        'Pragma': 'no-cache'
    }

    ID = 0
    zip = 'testZip.zip'
    sus_words = 'susWords.txt'
    es = connect_elasticsearch()
    unzip_file(zip)