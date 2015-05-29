#-*- coding:utf-8 -*-
import sys
import urllib2
import urllib
import cookielib
import pymongo
import hashlib
import StringIO
from random import randint
from scrapy import Selector
sys.path.append('../../tesseract')
from pytesser import *
from PIL import Image
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

'''Recognize telephone image'''
# 二值化
threshold = 140
table = []
for i in range(256):
    if i < threshold:
        table.append(0)
    else:
        table.append(1)

#对于识别成字母的 采用该表进行修正
rep={'O':'0',
    'U':'0',
    'C':'0',
    'D':'0',
    'I':'1',
    'H':'18',
    'L':'1',
    'Z':'2',
    'S':'8',
    'E':'8'
    }

def get_html_by_data(url, use_cookie=False, fake_ip=False):
    data = {}
    post_data = urllib.urlencode(data)
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    req = urllib2.Request(url)
    if use_cookie:
        cookie_file = open('cookie')
        cookie = cookie_file.read()
        req.add_header("Cookie", cookie)
    if fake_ip:
        ip = "%s.%s.%s.%s" % (str(randint(0,255)), str(randint(0,255)), str(randint(0,255)), str(randint(0,255)))
        req.add_header("X-Forwarded-For", ip)
    req.add_header("User-agent", "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36")
    f = opener.open(req)
    html = f.read()
    html_file = open('test.html','w')
    print >> html_file, html
    f.close()
    return html

def exist(id):
    if invalid_table.find({"id":id}).count() > 0:
        return True
    if temp_table.find({"id":id}).count() > 0:
        return True
    if vertical_temp_table.find({"id":id}).count() > 0:
        return True
    if job_table.find({"id":id}).count() > 0:
        return True
    if vertical_job_table.find({"id":id}).count() > 0:
        return True
    return False

def rec_tel(url):
    im = Image.open(StringIO.StringIO(get_html_by_data(url,fake_ip=True)))
    imgry = im.convert('L')
    out = imgry.point(table,'1')
    text = image_to_string(out)
    text = text.strip()
    text = text.upper()
    for r in rep:
        text = text.replace(r,rep[r])
    return text

def crawl_tel(url):
    while True:
        tel = rec_tel(url)
        print 'rec tel: ' + tel
        try:
            if tel[:3] == "400" and len(tel.replace('-','')) != 10:
                continue
            t = int(tel.replace('-','').replace(' ',''))
            return tel
        except:
            continue

def crawl_detail(prod):
    hxs = Selector(text=get_html_by_data(prod['url'], fake_ip=True))
    prod['create_time'] = hxs.xpath('//ul[@class="headtag"]/li/text()')[0].extract().strip()
    prod['create_time'] = prod['create_time'].replace('更新时间：','').split(' ')[0]
    print 'create_time: ' + prod['create_time']
    dl_list = hxs.xpath('//div[@class="xq clearfix"]/dl')
    for dl in dl_list:
        try:
            key = dl.xpath('./dt/text()')[0].extract().strip()
            value = dl.xpath('./dd/text()')[0].extract().strip()
            if key == '联系人：':
                prod['contact'] = value
                print 'contact: ' + prod['contact']
            elif key == '联系方式：':
                tel_url = 'http://www.jianzhiku.com/' + dl.xpath('./dd/img/@src')[0].extract()
                prod['tel'] = crawl_tel(tel_url)
                print 'tel: ' + prod['tel']
            elif key == '工作地点：':
                prod['addr'] = value
                print 'address: ' + prod['addr']
        except:
            continue
    prod['content'] = ''
    zhiwei_div = hxs.xpath('//div[@class="jz-tabc"]')
    text_list = zhiwei_div.xpath('.//text()')
    for text in text_list:
        prod['content'] += text.extract().strip()
    print 'content: ' + prod['content'] 

def save(prod):
    if prod['vertical']:
        vertical_temp_table.save(prod)
    else:
        temp_table.save(prod)

def work(list_url):
    print 'List url: ' + list_url
    hxs = Selector(text=get_html_by_data(list_url, fake_ip=True))
    info_list = hxs.xpath('//div[@id="all-list"]/ul/li')
    if len(info_list) == 0:
        return False
    for info in info_list:
        try:
            prod = {}
            prod['source'] = 'jianzhiku'
            prod['url'] = info.xpath('.//span[@class="table-view-body"]/a/@href')[0].extract()
            prod['url'] = 'http://www.jianzhiku.com' + prod['url']
            print 'url: ' + prod['url']
            prod['title'] = info.xpath('.//span[@class="table-view-body"]/a/text()')[0].extract().strip()
            print 'title: ' + prod['title']
            prod['company'] = info.xpath('./div[@class="table-view-block"]/text()')[0].extract().strip()
            print 'company: ' + prod['company']
            prod['vertical'] = True
            print 'vertical: ' + str(prod['vertical'])
            prod['salary'] = info.xpath('//span[@class="highlight"]/text()')[0].extract().strip()
            print 'salary: ' + prod['salary']
            prod['id'] = hashlib.md5(prod['title']+prod['company']+prod['salary']).hexdigest().upper()
            if exist(prod['id']):
                continue
            crawl_detail(prod)
            save(prod)
            #import pdb;pdb.set_trace()
        except Exception as e:
            print e
            continue
    return True

if __name__ == "__main__":
    start_url = "http://www.jianzhiku.com/c-bj/job-job/#CUR_PAGE#"
    page = 1
    while work(start_url.replace('#CUR_PAGE#',str(page))):
        page += 1
        if page > 100:
            print 'Current page exceeded 100, script terminated.'
            break
