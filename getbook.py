#-*- coding: utf-8 -*-                                                                                                                                  
import re
import os
import codecs
import chardet
import requests 
from lxml import html

class piaotian(object):
    def __init__(self):
        #获取小说名称
        self.title = ''
        self.author = ''
        #piaotian目录分页数
        self.pagenum = 0
        #书籍总共的章节数，由分页数当中具体的章节计数而来
        self.chapternum = 0
        #书籍章节-url字典
        self.title_url = {}

    def getlist(self,bookid):
        #内部变量申明
        pageurl = []
        #title_url = {}
        len_title_url = 0
        baseurl = 'http://m.piaotian.com/html/'
        bookdir = str(bookid)[0]

        #获取书籍在网站上的章节分页数
        re_pagenum = re.compile(r'(.*)/(\d{1,4})页(.*)',re.S)
        #获取书籍title
        re_title = re.compile(r'(.*)<h1 id="_52mb_h1"><.*>(.*)</a></h1>',re.S)

        #获取书籍的页数基本信息
        r = requests.get(baseurl + bookdir + '/' + str(bookid))
        r.encoding = 'gbk'
        c = r.text
        self.pagenum = int(re_pagenum.match(c).group(2))
        self.title = re_title.match(c).group(2)
        [pageurl.append('http://m.piaotian.com/html/%s/%s_%s/' % (bookdir,bookid,d)) for d in range(1,self.pagenum+1)]

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
                list_url = ['http://m.piaotian.com'+list_url[i] for i in range(len(list_url))]

                #将title和url加入到一个字典当中，循环添加所有的信息
                for i in range(len(list_url)):
                    print('正在抓取第%s|%s页，总计第%s小节：%s' % (n+1,self.pagenum,len_title_url+i,list_title[i]))
                    self.title_url[len_title_url + i] = [list_title[i],list_url[i]]

            #这里获取上次的字典长度，下次方便直接相加，让title_url字典的key是不断增加的int
            len_title_url = len(self.title_url) 
            print('上次抓取完成后合计：',len_title_url)
            print('-----------------------------------')
        #将总计的章节数目，写入到self变量当中，方便后续引用
        self.chapternum = len_title_url
        return self.title_url

    def getcontent(self,title_url):
        #正则表达式获取文章正文
        rc = re.compile(r'(.*)<div id="nr1">(.*)(<br/><br/>&nbsp;&nbsp;&nbsp;&nbsp;{飘天文学www.piaotian.com感谢各位书友的支持，您的支持就是我们最大的动力})?(<br/></div>\r\n    </div>\r\n\r\n    <div class="nr_page">\r\n    \t <table cellpadding="0" cellspacing="0">\r\n             <tr>\r\n            \t<td class="prev">)(.*)',re.S)
        r = requests.Session()

        pagestart = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html xmlns="http://www.w3.org/1999/xhtml"><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><title>%s</title><link type="text/css" href="style.css" rel="Stylesheet"/></head><body>' % self.title
        pageend = '</body></html>'

        if self.title in os.listdir('lib'): 
            print('书籍目录已存在！清除已有内容，重新生成文件！')
            [os.remove('lib/%s/%s' % (self.title,file)) for file in os.listdir('lib/%s' % self.title)]
        else:
            os.mkdir('lib/%s' % self.title)

        with open('lib/%s/text.html' % self.title,'at') as f:
            f.write(pagestart)
            for n in range(len(title_url)):
                print('%s:[%s,%s]' % (n,title_url[n][0],title_url[n][1]))
                s = r.get(title_url[n][1])
                s.encoding = 'gbk'
                c = s.text
                
                article_content = rc.match(c).group(2)
                article_content = article_content.replace('<br/><br/>','</p><p>')
#                article_content = article_content.encode('utf-8')

                #标题用h2包括，后面跟一个空行，id从1开始
                f.write('<h2 id="id%s">%s</h2>' % (n+1,title_url[n][0]))
                f.write('<br/>')
                f.write(article_content)
                #以下用于每章节后面添加pagebreak分页
                f.write('<mbp:pagebreak/>')
                #with open ('%s-%s.txt' % (n+1,title_url[n][0]),'wt') as f:
                #    f.write(article_content)
            f.write(pageend)

    def ncxopf(self,title_url):
        #读取模板ncx文件，获取其中内容
        with open('temp/toc.ncx','rt') as f:
            ncx = f.read()
        ncxstart = ncx.split('$toclist')[0]
        ncxend = ncx.split('$toclist')[1]

        #读取模板opf文件获取其中内容
        with open('temp/title.opf','rt') as f:
            opf = f.read()
        opfstart = opf.split('$title')[0]
        opfend = opf.split('$title')[1]

        #读取css文件
        with open('temp/style.css','rt') as f:
            stylecss = f.read()

        #读取cover文件
        with open('temp/cover.jpg','rb') as f:
            cover = f.read()

        #先写入ncx文件
        with open ('lib/%s/toc.ncx' % self.title,'at') as f:
            f.write(ncxstart)
            if len(title_url) != 0:
                for n in range(len(title_url)):
                    f.write('<navPoint id="navpoint-%s" playOrder="%s"><navLabel><text>%s</text></navLabel><content src="text.html#id%s"/></navPoint>' % (n+1,n+1,title_url[n][0],n+1))
                    f.write('\n')
                #f.write(ncxend)
            else:
                f.write('<navPoint id="navpoint" playOrder="1"><navLabel><text>%s</text></navLabel><content src="text.html"/></navPoint>' % '全部')
                f.write(ncxend)
        print('NCX制作完毕')

        #写入OPF文件
        with open ('lib/%s/%s.opf' % (self.title,self.title),'at') as f:
            f.write(opfstart)
            f.write(self.title)
            f.write(opfend)
        print('OPF制作完毕')

        #写入css文件
        with open ('lib/%s/style.css' % self.title,'at') as f:
            f.write(stylecss)
        print('style.css制作完毕')

        #写入cover文件
        with open ('lib/%s/cover.jpg' % self.title,'ab') as f:
            f.write(cover)
        print('封面制作完毕')

        #开始转换mobi
        print('------------------------------')
        print('开始转换mobi')
        workdir = os.getcwd() + '/lib/%s/' % self.title
        workopf = '%s/%s.opf' % (workdir,self.title)
        workkindlegen = os.getcwd() + '/kindlegen/kindlegen'
        out = os.popen('%s -c1 -dont_append_source -locale zh %s' % (workkindlegen,workopf)).read()
        print(out)

class zxcs(piaotian):
    def getdir(self,sortid):
        #定义需要下载的知轩藏书目录
        baseurl = 'http://www.zxcs8.com/sort/%s' % sortid

        #获取分类一共多少个分页，方便下载
        r = requests.get(baseurl)
        c = r.text
        tree = html.fromstring(c)
        #通过xpath获取最后一页的链接，同时通过切片获取最后一页的数字值
        pagenum = tree.xpath('/html/body/div[4]/div[2]/div[2]/a[6]/@href')[0][34:]

        r = requests.Session()
        for i in range(1,int(pagenum)+1):
            #获取当前页面的url用于requests
            current_page_url = '%s%s%s' % (baseurl,'/page/',i)
            p = r.get(current_page_url)
            print('%s|%s，抓取书籍列表……' % (i,pagenum))
            c = p.text
            tree = html.fromstring(c)
            #获取当前书页所有的书籍url，名称，作者，和一共多少页
            #将当前页面所有的书籍编号通过正则表达式获取
            rl = re.compile(r'(http://www.zxcs8.com/post/)(.*)')
            list_url = tree.xpath('/html/body/div[4]/div[2]/dl/dt/a/@href')
            list_url = [rl.match(x).group(2) for x in list_url ]
            list_text = tree.xpath('/html/body/div[4]/div[2]/dl/dt/a/text()')

            #抓取完成一页之后，在抓取该页所有书籍的下载地址
            n = 1
            for j in list_url:
                book_dl_url = '%s%s' % ('http://www.zxcs8.com/download.php?id=',j)
                d = r.get(book_dl_url)
                print('------%s|%s，抓取下载地址……' % (n,len(list_url)))
                c = d.text
                tree = html.fromstring(c)
                dl_url = tree.xpath('/html/body/div[2]/div[2]/div[3]/div[2]/span[1]/a/@href')
                #直接下载文件
                l = r.get(dl_url[0])
                with open ('/download/getbook/lib/zxcs/%s.rar' % str(15*(i-1)+n),'wb') as f:
                    f.write(l.content)
                print('--------下载完成该本')
                n = n+1
                print(dl_url)
                self.title_url[j] = [j]
        return self.title_url

    def uncompress(self,filename):
        num = len([j for i in [i[2] for i in os.walk('./lib/zxcs')] for j in i])
        os.system('cd ./lib/zxcs')
        for i in range(1,num+1):
            os.system('rar x -yq %s.rar' % i)
            print('%s|%s解压成功' % (i,num))
        os.system('rm *.URL *.url *.rar')

    def getlist(self,bookid):
        #章节正则表达式
        re_char_chn = re.compile(r'^\s*[第卷]\s*[0123456789一二三四五六七八九十零〇百千两]{1,9}[章?回?部?节?集?卷?]\s*.*[\n|\r|\r\n]',re.S)
        re_char_eng = re.compile(r'^\s*[c-zC-z]{7,7}\s*[0-9]*.*[\n|\r|\r\n]',re.S)
        re_title = re.compile(r'《(.*)》.*作者：(.*).txt',re.S)
        encodings = {'UTF-16':'utf16', 'ISO-8859-1':'gbk', 'UTF-8-SIG':'utf8', 'ascii':'gbk','GB2312':'gbk'}

        pagestart = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html xmlns="http://www.w3.org/1999/xhtml"><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><title>power_by_jonchil</title><link type="text/css" href="style.css" rel="Stylesheet"/></head><body>'
        pageend = '</body></html>'


        self.title = re_title.match(bookid).group(1)
        self.author = re_title.match(bookid).group(2)

        if self.title in os.listdir('../../lib'): 
            print('书籍目录已存在！清除已有内容，重新生成文件！')
            [os.remove('../../lib/%s/%s' % (self.title,file)) for file in os.listdir('../../lib/%s' % self.title)]
        else:
            os.mkdir('../../lib/%s' % self.title)

        print('开始制作书籍：%s',bookid)

        with open(bookid,'rb') as f:
            l = f.read(500)
            encoding = chardet.detect(l)['encoding']

        with codecs.open(bookid,'rb',encodings[encoding],'ignore') as f:
            lines = f.readlines() 
            #print(encoding)
        #列表生成式，通过正则表达式筛选lines当中元素，同时通过if筛选长度大于0的元素
        #有[0]的原因是正则findall方法给出的是一个list，通过if把为0的列表，即不符合正则的部分去掉
        #没有if的话会报错，因为不符合正则的部分用[0]来切分的话，out of range
        char_chn = [re_char_chn.findall(x)[0] for x in lines if len(re_char_chn.findall(x)) > 0]
        if len(char_chn) == 0:
            char_chn = [re_char_eng.findall(x)[0] for x in lines if len(re_char_eng.findall(x)) > 0]
            if len(char_chn) == 0:
                print('无法解析目录')

        with open('../../lib/%s/text.html' % self.title,'at') as f:
            j = 1
            f.write(pagestart)
            #titleurl初始化为空
            self.title_url = {}
            if len(char_chn) != 0:
                for i in range(len(lines)):
                    if i < lines.index(char_chn[0]):
                        print('删除第一目录前内容')
                    elif lines[i] in char_chn:
                        f.write('<mbp:pagebreak/>')
                        f.write('\n')
                        f.write('<h2 id="id%s">%s</h2>' % (j,lines[i].strip('\r\n').strip('\u3000')))
                        f.write('\n')
                        #print(i)
                        self.title_url[j-1] = [lines[i]]
                        j = j + 1
                        #print('写入章节：%s' % lines[i])
                    else:
                        if lines[i].strip('\r\n') == '':
                            print('删除空章节')
                        else:
                            f.write('<p class="a">%s</p>' % (lines[i].strip('\r\n').strip('\u3000')))
                            #print('写入正文%s' % i)
                            f.write('\n')
                            #还需添加每段空两格
            else:
                for i in range(len(lines)):
                    if lines[i].strip('\r\n') == '':
                        print('删除空章节')
                    else:
                        f.write('<p class="a">%s</p>' % (lines[i].strip('\r\n').strip('\u3000')))
                        #print('写入正文%s' % i)
                        f.write('\n')

        return self.title_url

        #with open('../chapter.txt','a') as f:
        #    f.write("%s\n目录长度%s\n%s\n%s\n\n" % (bookid,len(char_chn),encoding,char_chn[:5]))
        #print('打开书籍：%s' % bookid)
        #print('目录长度%s' % len(char_chn))
        #print(encoding)
        #print(char_chn[:5])


if __name__ == '__main__':
    test = piaotian()
    title_url = test.getlist(4765)
    test.getcontent(title_url)
    test.ncxopf(title_url)

    #l = os.listdir('./lib/zxcs')
    #test = zxcs()
    ##test.getdir(47)
    #for i in l:
    #    os.chdir('./lib/zxcs')
    #    title_url = test.getlist(i)
    #    os.chdir('../../')
    #    test.ncxopf(title_url)
