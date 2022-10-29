# -*- coding: utf-8 -*-
import codecs
import os
import re
import subprocess
import chardet
from lxml import html
import requests
import sys
sys.path.append("./lib.py")
from logger import Logger


class Pack(object):

    '''
    用于将txt文件转换成mobi文件，包含两个方法，一个是读取目录生成text.html，一个是打包mobi文件
    '''

    def __init__(self):
        #初始化下载类可以直接调用
        self.d = Download()

    def txt_to_html(self, book_details):
        logger = Logger('txt_to_html')
        '''
        Description: 
            读取txt文件和其中的目录，生成相关的text.html文件，如果是已经生成过text.html文件的抓取类型
            则跳过上述生成步骤，直接返回传入的title_details
        Args: 
            book_details: 类型同抓取方法类当中的返回一致，即[title,author]
        Returns: 
            title_url: 生成text.html在temp目录当中，同时返回title_url的list，格式[0,章节名称]
        '''

        # 章节正则表达式
        re_char_chn = re.compile(
            r'^\s*[第卷]\s*[0123456789一二三四五六七八九十零〇百千两]{1,9}[章?回?部?节?集?卷?]\s*.*[\n|\r|\r\n]', re.S)
        re_char_eng = re.compile(
            r'^\s*[c-zC-z]{7,7}\s*[0-9]*.*[\n|\r|\r\n]', re.S)
        #re_title = re.compile(r'《(.*)》.*作者：(.*).txt', re.S)
        encodings = {'UTF-16': 'utf16', 'ISO-8859-1': 'gbk',
                     'UTF-8-SIG': 'utf8', 'ascii': 'gbk', 'GB2312': 'gbk'}

        pagestart = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html xmlns="http://www.w3.org/1999/xhtml"><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><title>power_by_jonchil</title><link type="text/css" href="style.css" rel="Stylesheet"/></head><body>'
        pageend = '</body></html>'

        title = book_details[0]
        author = book_details[1]

        logger.info('开始制作书籍：%s' % title)

        with open('lib/%s/%s-%s.txt' % (title, title, author), 'rb') as f:
            l = f.read(500)
            encoding = chardet.detect(l)['encoding']

        # 正则表达式获取文章正文
        with codecs.open('lib/%s/%s-%s.txt' % (title, title, author), 'rb', encodings[encoding], 'ignore') as f:
            lines = f.readlines()
            # print(encoding)
        # 列表生成式，通过正则表达式筛选lines当中元素，同时通过if筛选长度大于0的元素
        # 有[0]的原因是正则findall方法给出的是一个list，通过if把为0的列表，即不符合正则的部分去掉
        # 没有if的话会报错，因为不符合正则的部分用[0]来切分的话，out of range
        char_chn = [re_char_chn.findall(
            x)[0] for x in lines if len(re_char_chn.findall(x)) > 0]
        if len(char_chn) == 0:
            char_chn = [re_char_eng.findall(
                x)[0] for x in lines if len(re_char_eng.findall(x)) > 0]
            if len(char_chn) == 0:
                logger.info('无法解析目录')

        with open('lib/%s/text.html' % title, 'at') as f:
            #章节中的id自增序列号
            j = 1
            f.write(pagestart)
            # titleurl初始化为空，返回后给rest_to_mobi使用
            title_url = {}
            #如果正常获取目录即char_chn不为空，则正常写入目录和正文
            if len(char_chn) != 0:
                for i in range(len(lines)):
                    #不读取第一目录前的内容，通常为广告
                    if i < lines.index(char_chn[0]):
                        continue
                    # 如果lines[i]在标题lis当中，则写入标题
                    elif lines[i] in char_chn:
                        f.write('\n')
                        f.write('<h2 id="id%s">%s</h2>' %
                                (j, lines[i].strip('\r\n').strip('\u3000')))
                        f.write('\n')
                        # print(i)
                        #在写入标题的时候存入title_url当中
                        title_url[j-1] = [lines[i]]
                        j = j + 1
                        #print('写入章节：%s' % lines[i])
                    #剩下的就是正文部分写入章节后面
                    else:
                        #删除章节正文为空的部分
                        if lines[i].strip('\r\n') == '':
                            continue
                        else:
                            f.write('<p class="a">%s</p>' %
                                    (lines[i].strip('\r\n').strip('\u3000')))
                            f.write('\n')
                            # 还需添加每段空两格
            #意外情况如果无法获取任何目录，则直接写正文
            else:
                for i in range(len(lines)):
                    if lines[i].strip('\r\n') == '':
                        # print('删除空章节')
                        continue
                    else:
                        f.write('<p class="a">%s</p>' %
                                (lines[i].strip('\r\n').strip('\u3000')))
                        #print('写入正文%s' % i)
                        f.write('\n')
            f.write(pageend)
        return title_url

    def res_to_mobi(self, url):
        logger = Logger('res_to_mobi')
        '''
        Description: 
            打包ncx,opf,text.html,style.css文件为mobi文件，先读取临时文件，再写入实际内容保存
        Args:
            title_url，章节名称的dict，格式是{0:titlename,1:titlename}，从0开始
        Returns:
            N/A, 生成mobi文件保存在目录当中
        '''

        #生成html文件，执行txt_to_html，并返回目录结构数组
        [title, author] = self.d.zxcs(url)
        title_url = self.txt_to_html([title,author])

        # 读取模板ncx文件，获取其中内容
        with open('temp/mobi/toc.ncx', 'rt') as f:
            ncx = f.read()
        ncxstart = ncx.split('$toclist')[0]
        ncxend = ncx.split('$toclist')[1]

        # 读取模板opf文件获取其中内容
        with open('temp/mobi/title.opf', 'rt') as f:
            opf = f.read()

        # 读取css文件
        with open('temp/mobi/style.css', 'rt') as f:
            stylecss = f.read()

        # 读取cover文件
        with open('temp/cover.jpg', 'rb') as f:
            cover = f.read()

        # 先写入ncx文件
        with open('lib/%s/toc.ncx' % title, 'at') as f:
            f.write(ncxstart)
            if len(title_url) != 0:
                for n in range(len(title_url)):
                    f.write('<navPoint id="navpoint-%s" playOrder="%s"><navLabel><text>%s</text></navLabel><content src="text.html#id%s"/></navPoint>' %
                            (n+1, n+1, title_url[n][0], n+1))
                    f.write('\n')
            else:
                f.write(
                    '<navPoint id="navpoint" playOrder="1"><navLabel><text>%s</text></navLabel><content src="text.html"/></navPoint>' % '全部')
                f.write(ncxend)
        logger.info('NCX制作完毕')

        # 写入OPF文件
        with open('lib/%s/%s-%s.opf' % (title, title, author), 'at') as f:
            opf = opf.replace('$title', title).replace('$author', author)
            f.write(opf)
        logger.info('OPF制作完毕')

        # 写入css文件
        with open('lib/%s/style.css' % title, 'at') as f:
            f.write(stylecss)
        logger.info('style.css制作完毕')

        # 写入cover文件
        with open('lib/%s/cover.jpg' % title, 'ab') as f:
            f.write(cover)
        logger.info('封面制作完毕')

        # 开始转换mobi
        logger.info('开始转换mobi')
        workdir = os.getcwd() + '/lib/%s/' % title
        workopf = '%s/%s-%s.opf' % (workdir, title, author)
        workkindlegen = os.getcwd() + '/kindlegen/kindlegen'
        out = os.popen('%s -c1 -dont_append_source -locale zh %s' %
                       (workkindlegen, workopf)).read()
        # print(out)
        logger.info(out)


class Download(object):
    '''
    不同的方法抓取不同小说网站的内容，共有两种抓取方式
    1、直接下载txt文件，返回[title,author]类型的list
    2、通过抓取章节直接生成text.htm文件，并返回[title,author,{chapter1:1,chapter2:2......}]这种书籍基本信息
    其中所有的章节计数都从1开始，而不是0

    '''

    def __init__(self):
        pass

    def piaotian(self, bookurl):
        '''
        抓取章节信息

        Args:
            bookurl，飘天站点的小说主页

        Returns:
            text.html，直接生成可以用于转换的html文件
            title_details，[title,author,{chapter1:0,chapter2:0......}]这种书籍基本信息
        '''

        # 获取小说名称
        title = ''
        author = ''
        # piaotian目录分页数
        pagenum = 0
        # 书籍总共的章节数，由分页数当中具体的章节计数而来
        chapternum = 0
        # 书籍章节-url字典
        title_url = {}
        title_no = {}
        # 获取bookid，因为是修改的，所以单独获取
        bookid = bookurl.split('/')[-1].split('.')[0]

        # 内部变量申明
        pageurl = []
        #title_url = {}
        len_title_url = 0
        baseurl = 'http://m.piaotian.com/html/'
        # piaotian的书籍分类就是bookid的第一个数字
        bookdir = str(bookid)[0]

        # 获取书籍在网站上的章节分页数
        re_pagenum = re.compile(r'(.*)/(\d{1,4})页(.*)', re.S)
        # 获取书籍title
        re_title = re.compile(r'(.*)<h1 id="_52mb_h1"><.*>(.*)</a></h1>', re.S)

        r = requests.Session()

        # 获取作者和书籍名称信息，这里title获取有问题所以放在下一个页面获取
        title_page = r.get(bookurl)
        title_page.encoding = 'gb2312'
        c = title_page.text
        tree = html.fromstring(c)
        author = tree.xpath(
            '/html[1]/body[1]/div[4]/div[1]/div[2]/p[2]/a[1]/text()')[0]

        # 获取书籍的页数基本信息
        charpter_page = r.get(baseurl + bookdir + '/' + str(bookid))
        charpter_page.encoding = 'gbk'
        c = charpter_page.text
        title = re_title.match(c).group(2)
        pagenum = int(re_pagenum.match(c).group(2))
        [pageurl.append('http://m.piaotian.com/html/%s/%s_%s/' %
                        (bookdir, bookid, d)) for d in range(1, pagenum+1)]

        # 获取书籍的目录title和url，并循环加入到title:url这种形式的字典当中
        r = requests.Session()
        for n in range(len(pageurl)):
            s = r.get(pageurl[n])

            print('正在抓取的网页，详情如下：', pageurl[n])
            s.encoding = 'gbk'
            if s.status_code == 200:
                c = s.text
                tree = html.fromstring(c)
                # xpath解析网页中的目录标题，和目录url，同时目录url是相对引用，合并成绝对引用
                list_title = tree.xpath('//html/body/div[2]/ul/li/a/text()')
                list_url = tree.xpath('//html/body/div[2]/ul/li/a/@href')
                list_url = ['http://m.piaotian.com'+list_url[i]
                            for i in range(len(list_url))]

                # 将title和url加入到一个字典当中，循环添加所有的信息
                for i in range(len(list_url)):
                    print('正在抓取第%s|%s页，总计第%s小节：%s' %
                          (n+1, pagenum, len_title_url+i, list_title[i]))
                    title_url[len_title_url + i] = [list_title[i], list_url[i]]

            # 这里获取上次的字典长度，下次方便直接相加，让title_url字典的key是不断增加的int
            len_title_url = len(title_url)
            print('上次抓取完成后合计：', len_title_url)
            print('-----------------------------------')
        # 将总计的章节数目，写入到量当中，方便后续引用
        chapternum = len_title_url

        # 正则表达式获取文章正文
        rc = re.compile(
            r'(.*)<div id="nr1">(.*)(<br/><br/>&nbsp;&nbsp;&nbsp;&nbsp;{飘天文学www.piaotian.com感谢各位书友的支持，您的支持就是我们最大的动力})?(<br/></div>\r\n    </div>\r\n\r\n    <div class="nr_page">\r\n    \t <table cellpadding="0" cellspacing="0">\r\n             <tr>\r\n            \t<td class="prev">)(.*)', re.S)
        r = requests.Session()

        pagestart = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html xmlns="http://www.w3.org/1999/xhtml"><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><title>%s</title><link type="text/css" href="style.css" rel="Stylesheet"/></head><body>' % title
        pageend = '</body></html>'

        if title in os.listdir('lib'):
            print('书籍目录已存在！清除已有内容，重新生成文件！')
            [os.remove('lib/%s/%s' % (title, file))
             for file in os.listdir('lib/%s' % title)]
        else:
            os.mkdir('lib/%s' % title)

        with open('lib/%s/text.html' % title, 'at') as f:
            f.write(pagestart)
            for n in range(len(title_url)):
                print('%s:[%s,%s]' % (n, title_url[n][0], title_url[n][1]))
                s = r.get(title_url[n][1])
                s.encoding = 'gbk'
                c = s.text

                article_content = rc.match(c).group(2)
                article_content = article_content.replace(
                    '<br/><br/>', '</p><p>')
#                article_content = article_content.encode('utf-8')

                # 标题用h2包括，后面跟一个空行，id从1开始
                f.write('<h2 id="id%s">%s</h2>' % (n+1, title_url[n][0]))
                f.write('<br/>')
                f.write(article_content)
                # 以下用于每章节后面添加pagebreak分页
                f.write('<mbp:pagebreak/>')
                # with open ('%s-%s.txt' % (n+1,title_url[n][0]),'wt') as f:
                #    f.write(article_content)

                # 借助title_url的循环，生成title_no章节对应数字的字典
                title_no[title_url[n][0]] = n

            f.write(pageend)

        book_details = [title, author, title_no]
        return book_details

    def zxcs(self, bookurl):
        logger = Logger('zxcs')
        # 获取小说名称
        title = ''
        author = ''

        # requests下载小说
        book_dl_url = '%s%s' % (
            'http://www.zxcs.me/download.php?id=', bookurl.split('/')[-1])
        r = requests.Session()

        # 获取下载页面的小说下载地址
        d = r.get(book_dl_url)
        logger.info('抓取下载地址……')
        d.encoding
        c = d.text
        tree = html.fromstring(c)
        dl_url = tree.xpath(
            '/html/body/div[2]/div[2]/div[3]/div[2]/span[1]/a/@href')

        # 获取小说名称和作者名称
        titleauthor = tree.xpath('/html/body/div[2]/div[2]/h2/text()')[0]
        re_titleauthor = re.compile(r'《(.*)》.*作者：(.*)')
        title = re_titleauthor.match(titleauthor).group(1)
        author = re_titleauthor.match(titleauthor).group(2)

        # 确认是存在书籍目录
        if title in os.listdir('lib'):
            logger.info('书籍目录已存在！清除已有内容，重新生成文件！')
            [os.remove('lib/%s/%s' % (title, file))
             for file in os.listdir('lib/%s' % title)]
        else:
            os.mkdir('lib/%s' % title)

        # 直接下载文件
        l = r.get(dl_url[0])
        with open('lib/%s/%s.rar' % (title, title), 'wb') as f:
            f.write(l.content)
        logger.info('下载完成该本')

        # 下载完成后解压到本地，并删除原始的rar文件
        #os.system('rar x -y -c- lib/%s/%s.rar lib/%s/ ' % (title,title,title))
        logger.info('解压rar文件')
        subprocess.run(['rar', 'x', '-y', '-c-', 'lib/%s/%s.rar' %
                       (title, title), 'lib/%s/' % title], stdout=subprocess.PIPE)
        logger.info('解压成功')
        #删除txt之外内容，并重命名txt为title-author.txt的形式
        todel = ['rar','url','URL']
        for file in os.listdir('lib/%s' % title):
            if file[-3:] in todel:
                os.remove('lib/%s/%s' % (title,file))
            # 重命名小说为书名-作者的格式
            elif file[-3:] in 'txt':
                os.rename("lib/%s/%s" % (title,file), "lib/%s/%s-%s.txt" % (title, title, author))
        logger.info('清理目录删除txt外文件并重命名txt')
        return [title, author]

    def jjxs(self, bookurl):
        logger = Logger('jjxs')
        '''
        用于抓取99小说网手机版的小说，需要现在小说主页用xpath找到下载链接，再进入下载链接通过xpath
        找到世纪下载网址，然后直接下载小说txt文档

        Args:bookurl

        Returns:txt
        '''

        baseurl = 'http://m.jjxsw.com'
        r = requests.Session()

        # 获取下载页面的小说下载地址
        d = r.get(bookurl)
        logger.info('抓取主页地址……')
        d.encoding = 'utf-8'
        c = d.text
        tree = html.fromstring(c)
        # xpath获取相对下载页地址
        dl_rel_url = tree.xpath(
            '/html[1]/body[1]/div[9]/ul[1]/li[1]/a[1]/@href')
        title = tree.xpath('/html[1]/body[1]/div[4]/div[2]/h1[1]/text()')[0]
        author = tree.xpath(
            '/html[1]/body[1]/div[4]/div[2]/span[3]/a[1]/text()')[0]
        # 组合成目标地址，用于requests
        dl_tar_url = baseurl + dl_rel_url[0]

        tar_html = r.get(dl_tar_url)
        tar_html_text = tar_html.text
        tree = html.fromstring(tar_html_text)
        dl_abs_url = tree.xpath(
            '/html[1]/body[1]/div[4]/ul[1]/li[2]/a[1]/@href')
        # 合成最终下载链接
        dl_url = baseurl + dl_abs_url[0]

        dl_txt = r.get(dl_url)

        # 确认是存在书籍目录
        if title in os.listdir('lib'):
            logger.info('书籍目录已存在！清除已有内容，重新生成文件！')
            [os.remove('lib/%s/%s' % (title, file))
            for file in os.listdir('lib/%s' % title)]
        else:
            os.mkdir('lib/%s' % title)

        # 书籍名称是title-author.txt这种形式
        with open('lib/%s/%s.txt' % (title, title+'-'+author), 'wb') as f:
            f.write(dl_txt.content)

        return [title, author]


if __name__ == '__main__':

    p = Pack()
    p.res_to_mobi('http://www.zxcs.me/post/13396')
