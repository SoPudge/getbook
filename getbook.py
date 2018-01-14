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
        len_title_url = 0
        baseurl = 'http://m.piaotian.com'
        re_pagenum = re.compile(r'(.*)/(\d{1,4})页(.*)',re.S)

        #获取书籍在移动端网页的目录页数，通过正则表达式读取requets的内容
        r = requests.get(baseurl+'/html/1/'+str(bookid))
        r.encoding = 'gbk'
        c = r.text
        pagenum = int(re_pagenum.match(c).group(2))
        [pageurl.append('http://m.piaotian.com/html/1/%s_%s/' % (bookid,d)) for d in range(1,pagenum+1)]

        #获取书籍的目录title和url，并循环加入到title:url这种形式的字典当中
        r = requests.Session()
        for n in range(len(pageurl)):
            s = r.get(pageurl[n])

            print('正在抓取的网页，详情如下：',pageurl[n])
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
                    print('正在抓取第%s|%s页，总计第%s小节：%s' % (n+1,pagenum,len_title_url+i,list_title[i]))
                    title_url[len_title_url + i] = [list_title[i],list_url[i]]

            #这里获取上次的字典长度，下次方便直接相加，让title_url字典的key是不断增加的int
            len_title_url = len(title_url) 
            print('上次抓取完成后合计：',len_title_url)
            print('-----------------------------------')
        return title_url


    def getcontent(self,title_url):
        rc = re.compile(r'(.*)<div id="nr1">(.*)(<br/></div>\r\n    </div>\r\n\r\n    <div class="nr_page">\r\n    \t <table cellpadding="0" cellspacing="0">\r\n             <tr>\r\n            \t<td class="prev">)(.*)',re.S)

        r = requests.Session()
        for n in range(len(title_url)):
            print('%s:[%s,%s]' % (n,title_url[n][0],title_url[n][1]))
            s = r.get(title_url[n][1])
            s.encoding = 'gbk'
            c = s.text
            
            article_content = rc.match(c).group(2)
            with open('book.html','at') as f:
                f.write('<h2>%s</h2>' % title_url[n][0])
                #f.write('## %s' % title_url[n][0])
                f.write('<br/><br/>')
                f.write(article_content)
                f.write('<br/><br/>')
            #with open ('%s-%s.txt' % (n+1,title_url[n][0]),'wt') as f:
            #    f.write(article_content)

if __name__ == '__main__':
    test = piaotian()
    title_url = test.getlist(1657)
    test.getcontent(title_url)

