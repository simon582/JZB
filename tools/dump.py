# -*- coding:utf-8 -*-
import sys
import re
import pymongo
reload(sys)
sys.setdefaultencoding('utf-8')

try:
    conn = pymongo.MongoClient('127.0.0.1',27017)
    temp_table = conn['jzb']['temp']
    vertical_temp_table = conn['jzb']['vertical_temp']
    job_table = conn['jzb']['job']
    vertical_job_table = conn['jzb']['vertical_job']
    invalid_table = conn['jzb']['invalid']
except Exception as e:
    print e
    exit(-1)

dump_file = open('jzb.csv','a')

def dump(table):
    cursor = table.find()
    for prod in cursor:
        resline = ""
        resline += prod['source'] + ','
        if prod['vertical']:
            resline += '1,'
        else:
            resline += '0,'
        resline += prod['title'] + ','
        resline += prod['company'] + ','
        resline += prod['salary'] + ','
        resline += prod['contact'] + ','
        resline += prod['tel'] + ','
        resline += prod['addr'] + ','
        resline += prod['create_time'] + ','
        resline += prod['icon'] + ','
        print >> dump_file, resline.encode('utf-8')

if __name__ == "__main__":
    dump(job_table)
    dump(vertical_job_table)
