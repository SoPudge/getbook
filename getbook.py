# -*- coding: utf-8 -*-                                                                                                                                  
import re
import requests 
from lxml import html

class piaotian(object):
    def __init__(self):
        pass

    def getlist(self,bookid):
        #内部变量申明
        pageurl = []
        title_url = {}
        baseurl = 'http://m.piaotian.com'
        re_pagenum = re.compile(r'(.*)/(\d{1,4})页(.*)',re.S)

        #获取书籍在移动端网页的目录页数，通过正则表达式读取requets的内容
        r = requests.get(baseurl+'/html/1/'+str(bookid))
        r.encoding = 'gbk'
        c = r.text
        pagenum = int(re_pagenum.match(c).group(2))+1
        [pageurl.append('http://m.piaotian.com/html/1/%s_%s/' % (bookid,d)) for d in range(1,pagenum)]

        #获取书籍的目录title和url，并循环加入到title:url这种形式的字典当中
        r = requests.Session()
        for n in range(len(pageurl)):
            s = r.get(pageurl[n])
            print(pageurl[n])
            s.encoding = 'gbk'
            if s.status_code == 200:
                c = s.text
                tree = html.fromstring(c)
                #xpath解析网页中的目录标题，和目录url，同时目录url是相对引用，合并成绝对引用
                list_title = tree.xpath('//html/body/div[2]/ul/li/a/text()')
                list_url = tree.xpath('//html/body/div[2]/ul/li/a/@href')
                list_url = [baseurl+list_url[i] for i in range(len(list_url))]
                #将title和url加入到一个字典当中，循环添加所有的信息
                for i in range(len(list_url)):
                    title_url[list_title[i]]=list_url[i]
                    print('正在抓取第%s|%s页，第%s小节目录及url' % (n+1,pagenum-1,len(title_url)))
        return title_url


    def getcontent(self):
        pass

if __name__ == '__main__':
    test = piaotian()
    test.getlist(1657)

