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

ban_words_list = ['KTV','夜场','按摩','美容','文化','传播','传媒','营销','人力','咨询','调查','调研','顾问广告','商贸','食品','管理','顾问','食品饮料']
tel_pattern = re.compile('((\d{11})|^((\d{7,8})|(\d{4}|\d{3})-(\d{7,8})|(\d{4}|\d{3})-(\d{7,8})-(\d{4}|\d{3}|\d{2}|\d{1})|(\d{7,8})-(\d{4}|\d{3}|\d{2}|\d{1}))$)')
salary_pattern = re.compile('\d+')

def filter_by_ban_words(prod):
    for ban_word in ban_words_list:
        if prod['title'].find(ban_word) != -1:
            return ban_word
        if prod['company'].find(ban_word) != -1:
            return ban_word
    return ''

def filter_by_tel(tel):
    if tel_pattern.match(tel):
        return False
    return True

def filter_by_region(prod):
    if prod['company'].find('北京') != -1:
        return False
    if prod['addr'].find('北京') != -1:
        return False
    return True

def filter_by_salary(salary):
    num = salary_pattern.match(salary)
    print salary
    print num.group()
    import pdb;pdb.set_trace()
    if not num:
        return True
    num = int(num.group())
    if salary.find('时') != -1:
        if num <= 50 and num >= 10:
            return False
    if salary.find('日') != -1 or salary.find('天') != -1:
        if num >= 60 and num <= 300:
            return False
    return True

def handle_date_dict(cursor, date_dict):
    for prod in cursor:
        if prod['create_time'] in date_dict:
            date_dict[prod['create_time']] += 1
        else:
            date_dict[prod['create_time']] = 1

def filter_by_agency(table):
    company_list = table.distinct('company')
    cnt = 0
    for company in company_list:
        date_dict = {}
        cursor = table.find({"company":company})
        handle_date_dict(cursor, date_dict)
        cursor = job_table.find({"company":company})
        handle_date_dict(cursor, date_dict)
        cursor = vertical_job_table.find({"company":company})
        handle_date_dict(cursor, date_dict)
        for value in date_dict.values():
            if value > 5:
                cnt += 1
                print 'Black company: ' + company
                table.remove({"company":company})
                job_table.remove({"company":company})
                vertical_job_table.remove({"company":company})
                break
    print 'Filter by agency count: ' + str(cnt)
        
def add_icon(prod):
    pass

def transform(source_table, dest_table):
    filter_by_agency(source_table)
    cursor = source_table.find()
    for prod in cursor:
        try:
            print prod['id'] + ' ' + prod['title']
            ban_word = filter_by_ban_words(prod)
            if ban_word != '':
                inv_prod = {}
                inv_prod['id'] = prod['id']
                inv_prod['reason'] = 'Filter by word: ' + ban_word
                print inv_prod['reason']
                invalid_table.save(inv_prod)
                #source_table.remove(prod)
                continue
            if filter_by_tel(prod['tel']):
                inv_prod = {}
                inv_prod['id'] = prod['id']
                inv_prod['reason'] = 'Filter by tel: ' + prod['tel']
                print inv_prod['reason']
                invalid_table.save(inv_prod)
                #source_table.remove(prod)
                continue
            if filter_by_region(prod):
                inv_prod = {}
                inv_prod['id'] = prod['id']
                inv_prod['reason'] = 'Filter by region: not in Beijing'
                print inv_prod['reason']
                invalid_table.save(inv_prod)
                #source_table.remove(prod)
                continue
            if filter_by_salary(prod['salary']):
                inv_prod = {}
                inv_prod['id'] = prod['id']
                inv_prod['reason'] = 'Filter by salary'
                print inv_prod['reason']
                invalid_table.save(inv_prod)
                #source_table.remove(prod)
                continue
            add_icon(prod)
            prod['send'] = False
            del(prod['_id'])
            #dest_table.save(prod)
        except Exception as e:
            print e
            #source_table.remove(prod)
            continue

if __name__ == "__main__":
    transform(temp_table, job_table)
    transform(vertical_temp_table, vertical_job_table)
