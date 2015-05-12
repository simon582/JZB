#-*- coding:utf-8 -*-
import sys
import urllib2
import urllib
import cookielib
import pymongo
import hashlib
import StringIO
import time
from random import randint
from scrapy import Selector
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
    prod['create_time'] = hxs.xpath('//p[@class="fc70 mb-5"]/span[@class="txt"]/text()')[0].extract().strip()
    prod['create_time'] = prod['create_time'].replace('更新时间：','')
    print 'create_time: ' + prod['create_time']
    prod['contact'] = hxs.xpath('//dl[@class="pos-relat"]/dd[1]/text()')[0].extract().replace(' ','').replace('\r','').replace('\n','').split('(')[0].replace('联系人：','').strip()
    print 'contact: ' + prod['contact']
    prod['addr'] = hxs.xpath('//dl[@class="pos-relat"]/dd[3]/text()')[0].extract().replace('工作地点：','').strip()
    print 'address: ' + prod['addr']
    prod['tel'] = hxs.xpath('//span[@id="isShowPhoneTop"]/img/@src')[0].extract()
    prod['tel'] = 'http://' + prod['url'].split('/')[2] + prod['tel']
    print 'tel: ' + prod['tel']
    '''
    prod['content'] = ''
    zhiwei_div = hxs.xpath('//div[@class="zhiwei"]')
    text_list = zhiwei_div.xpath('.//text()')
    for text in text_list:
        prod['content'] += text.extract().strip()
    print 'content: ' + prod['content'] 
    '''

def save(prod):
    if prod['vertical']:
        vertical_temp_table.save(prod)
    else:
        temp_table.save(prod)

def work(list_url):
    print 'List url: ' + list_url
    hxs = Selector(text=get_html_by_data(list_url, fake_ip=True))
    info_list = hxs.xpath('//dl[@class="list-noimg job-list"]|//dl[@class="list-img job-list"]')
    for info in info_list:
        try:
            prod = {}
            prod['source'] = 'ganji'
            prod['url'] = info.xpath('./dt/a/@href')[0].extract()
            print 'url: ' + prod['url']
            prod['title'] = info.xpath('./dt/a/text()')[0].extract().strip()
            print 'title: ' + prod['title']
            prod['company'] = info.xpath('./dd[@class="company"]/a/@title')[0].extract().strip()
            print 'company: ' + prod['company']
            ver = info.xpath('.//span[@class="icon-hr"]')
            if len(ver) > 0:
                prod['vertical'] = True
            else:
                prod['vertical'] = False
            print 'vertical: ' + str(prod['vertical'])
            prod['id'] = hashlib.md5(prod['title']+prod['company']+prod['source']).hexdigest().upper()
            if exist(prod['id']):
                continue
            crawl_detail(prod)
            #save(prod)
            import pdb;pdb.set_trace()
            time.sleep(1)
        except Exception as e:
            print e
            continue
    return True

if __name__ == "__main__":
    start_url = "http://bj.ganji.com/jzxuesheng/e1i1l1o#CUR_PAGE#/"
    page = 1
    while work(start_url.replace('#CUR_PAGE#',str(page))):
        page += 1
        if page > 100:
            print 'Current page exceeded 100, script terminated.'
            break
