#-*- coding: utf-8 -*-                                                                                                                                  

from getbook import Download
from getbook import Pack

def job(url):

    '''

    '''

    #判断来自哪个url，调用不同的方法来下载小说
    if url.find('zxcs') >= 0:
        book_path = Download.zxcs(url)
    elif url.find('piaotian') >= 0:
        book_path = Download.piaotian(url)
    else:
        book_path = Download.jjxs(url)

    #通过txt to html将lib目录当中的txt书籍制作成text.html并返回title no字典
    #如果对于已经制作好的html文件，则直接返回字典
    title_no = Pack.txt_to_html(book_path)

    Pack.res_to_mobi(title_no)


    

    


