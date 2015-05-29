#-*- coding:utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect,HttpResponse
from django.contrib import auth
from django.core.context_processors import csrf
from django.contrib.auth.forms import UserCreationForm
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.template import RequestContext
import os
import sys
import pymongo
import time
import datetime
import hashlib

def get_connection():
    try:
        conn = pymongo.MongoClient()
        return conn
    except Exception as e:
        print e
        print 'Cannot connect mongodb!'
        return None

def remove_word(cat, word):
    try:
        mongo_conn = get_connection()
        temp_table = mongo_conn['jzb']['word_conf']
        temp_table.remove({"cat":cat, "word":word}) 
    except Exception as e:
        print e
        print 'Remove word failed! ' + cat + ' ' + word 

def add_word(cat, word):
    try:
        mongo_conn = get_connection()
        temp_table = mongo_conn['jzb']['word_conf']
        temp_table.save({"cat":cat, "word":word}) 
    except Exception as e:
        print e
        print 'Add word failed! ' + cat + ' ' + word 

def handle_request(request):
    cat = request.POST['cat']
    word = request.POST['word']
    mode = request.POST['submit']
    if mode == u"添加":
        print "add " + cat + " " + word
        add_word(cat, word)
    if mode == u"删除":
        print "remove " + cat + " " + word
        remove_word(cat, word)

@csrf_protect
def words_manage(request):
    if request.method == 'POST':
        handle_request(request)
    mongo_conn = get_connection()
    if mongo_conn:
        pro_words_list = []
        sim_words_list = []
        fre_words_list = []
        ban_words_list = []
        word_table = mongo_conn['jzb']['word_conf']
        for prod in word_table.find():
            if prod['cat'] == 'pro':
                pro_words_list.append(prod['word'])
            if prod['cat'] == 'sim':
                sim_words_list.append(prod['word'])
            if prod['cat'] == 'fre':
                fre_words_list.append(prod['word'])
            if prod['cat'] == 'ban':
                ban_words_list.append(prod['word'])
        mongo_conn.close()
        word_list = []
        i = 0
        while True:
            prod = {}
            if i < len(pro_words_list):
                prod['pro'] = pro_words_list[i]
            else:
                prod['pro'] = ""
            if i < len(sim_words_list):
                prod['sim'] = sim_words_list[i]
            else:
                prod['sim'] = ""
            if i < len(fre_words_list):
                prod['fre'] = fre_words_list[i]
            else:
                prod['fre'] = ""
            if i < len(ban_words_list):
                prod['ban'] = ban_words_list[i]
            else:
                prod['ban'] = ""
            if prod['pro'] == "" and prod['sim'] == "" and prod['fre'] == "" and prod['ban'] == "":
                break
            word_list.append(prod)
            i += 1
        return render_to_response('manage.html',{'word_list':word_list}, context_instance=RequestContext(request))
    else:
        print 'mongodb connection failed!'

