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
            t = int(tel.replace('-',''))
            return tel
        except:
            continue

def crawl_detail(prod):
    hxs = Selector(text=get_html_by_data(prod['url'], fake_ip=True))
    prod['create_time'] = ''
    prod['salary'] = ''
    li_list = hxs.xpath('//ul[@class="terminal-ul clearfix"]/li')
    for li in li_list:
        try:
            key = li.xpath('./span/text()')[0].extract()
            val = li.xpath('./strong/text()|./strong/span/text()')[0].extract()
            if key == "职位月薪：":
                prod['salary'] = val.strip()
            if key == "发布日期：":
                prod['create_time'] = val.strip()
        except:
            continue
    print 'create_time: ' + prod['create_time']
    print 'salary: ' + prod['salary']
    try:
        prod['addr'] = hxs.xpath('//div[@class="tab-inner-cont"]/h2/text()')[0].extract().strip()
    except:
        prod['addr'] = ""
    print 'address: ' + prod['addr']
    prod['content'] = ''
    zhiwei_div = hxs.xpath('//div[@class="tab-inner-cont"]')
    text_list = zhiwei_div.xpath('.//text()')
    for text in text_list:
        prod['content'] += text.extract().strip()
    print 'content: ' + prod['content'] 
    #prod['contact'] = hxs.xpath('//div[@class="box"]/ul/li/text()')[0].extract().replace(' ','').replace('\r','').replace('\n','').split(':')[1].strip()
    #print 'contact: ' + prod['contact']
    #tel_url = hxs.xpath('//div[@class="box"]/ul/li/img/@src')[0].extract().strip()
    #print 'tel url: ' + tel_url
    #prod['tel'] = crawl_tel(tel_url)
    #prod['tel'] = tel_url
    #print 'tel: ' + prod['tel']

def save(prod):
    if prod['vertical']:
        vertical_temp_table.save(prod)
    else:
        temp_table.save(prod)

def work(list_url):
    print 'List url: ' + list_url
    hxs = Selector(text=get_html_by_data(list_url, fake_ip=True))
    info_list = hxs.xpath('//table[@class="newlist"]')
    if len(info_list) == 0:
        return False
    for info in info_list:
        try:
            prod = {}
            prod['source'] = 'zhilian'
            prod['url'] = info.xpath('.//td[@class="zwmc"]/div/a/@href')[0].extract()
            print 'url: ' + prod['url']
            prod['title'] = ''
            for part in info.xpath('.//td[@class="zwmc"]/div/a/text()|.//td[@class="zwmc"]/div/a/b/text()'):
                prod['title'] += part.extract().strip()
            print 'title: ' + prod['title']
            prod['vertical'] = False
            print 'vertical: ' + str(prod['vertical'])
            prod['company'] = info.xpath('.//td[@class="gsmc"]/a/text()')[0].extract()
            print 'company: ' + prod['company']
            prod['id'] = hashlib.md5(prod['title']+prod['url']).hexdigest().upper()
            if exist(prod['id']):
                continue
            crawl_detail(prod)
            #import pdb;pdb.set_trace()
            save(prod)
        except Exception as e:
            print e
            continue
    return True

if __name__ == "__main__":
    start_url = 'http://sou.zhaopin.com/jobs/searchresult.ashx?jl=%E5%8C%97%E4%BA%AC&kw=%E5%85%BC%E8%81%8C&sm=0&sg=8acaa38c72624ce49247f9d5d1d6fb17&p=#CUR_PAGE#'
    page = 1
    while work(start_url.replace('#CUR_PAGE#',str(page))):
        page += 1
        if page > 100:
            print 'Current page exceeded 100, script terminated.'
            break
