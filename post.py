import time
import datetime
import math
import json
import requests
import threading
import queue
from download import load_page
from download import get_html


class Post:
    def __init__(self, url, user_nickname, title, post_type, post_id, view_count,
                 comment_count, code, source):
        (self.url, self.user_nickname, self.title, self.post_type, self.post_id,
        self.view_count, self.comment_count, self.code, self.source) = (url, user_nickname, 
        title, post_type, post_id, view_count, comment_count, code, source)
        self.content, self.user_id, self.user_influ, self.user_age = ['']*4
        self.post_time = datetime.datetime(1970,1,1,12,0,0)
        self.last_update_at = datetime.datetime(1970,1,1,12,0,0)
        self.like_count = 0
        if int(comment_count)==0:
            self.page_count = 1
        else:
            self.page_count = math.ceil(int(comment_count)/30)
        self.comments = []  #Post的列表
        self.q = None  #队列
    
    def save(self, db):  #保存主帖到数据库
        db.update({'url': self.url}, {
            'id': self.post_id,
            'url': self.url,
            'uesr_nickname': self.user_nickname,
            'title': self.title,
            'created_at': self.post_time,
            'comment_count': self.comment_count,
            'view_count': self.view_count,
            'content': self.content,
            'user_id': self.user_id,
            'user_influence': self.user_influ,
            'type': self.post_type,
            'user_age': self.user_age,
            'like_count': self.like_count,
            'last_update_at': self.last_update_at,
            'page_count': self.page_count,
            'code': self.code,
            'source': self.source,
            'comments': self.comments
        })
    
    def set_detail(self, parser):  #获取主帖详细内容
        self.like_count = self.get_like_count()  #文章点赞
        html = load_page(self.url)
        if html == None:
            return 0
        if self.post_type == 'qa':   #如果文章类型是问董秘类型
            try:
                self.question = parser.get_post_question(html)
                self.answer = parser.get_post_answer(html)
                self.content = {'question': self.question, 'answer': self.answer}
            except:
                self.content = parser.get_post_content(html)  #文章内容
        elif self.post_type == 'hinfo':  #如果是新闻，hinfo类型
            self.content = parser.get_news_content(html)
        else:  #普通文章，normal类型
            title = parser.get_post_title(html)
            if title == '':  #若获取标题先失败了，说明该帖子实际上不存在，退出获取。函数返回0
                return 0
            self.title = title
            self.content = parser.get_post_content(html)  #文章内容
        self.post_time = parser.get_post_time(html)  #文章发表时间   
        self.user_id = parser.get_author_id(html)  #作者id
        if self.user_id != '':
            self.user_influ = self.get_user_influ()  #影响力
            self.user_age = self.get_user_age()  #吧龄 
        if self.page_count < 10:  #如果评论页面数小于10页
            self.get_comments(parser)  #获取评论
        else:  
            self.get_comment_queue()  #获取评论页面队列
            thread_num = 3
            thread_list = []
            for i in range(thread_num):  #开启线程，每个线程运行get_comment()
                thread = commentThread('Thread' + str(i+1), self, parser)
                thread.start()
                thread_list.append(thread)                             
            for thread in thread_list:  #等待所有线程完成
                thread.join()
        if len(self.comments) != 0:                    #如果评论数不为0
            self.last_update_at = self.comments[-1]['created_at']    #获取最后更新时间    
            self.get_comments_like_count()          #获取所有的评论的点赞
            self.get_comments_user_info()           #获取所有的评论用户的影响力、吧龄
        else:
            self.last_update_at = self.post_time
        return 1

    def get_comments_user_info(self):  #获取全部评论的影响力及吧龄数据
        times = math.ceil(len(self.comments)/30)  #需要把多个用户的id分开多次获取
        url = ["http://iguba.eastmoney.com/interf/user.aspx?action=influence&uids="]
        if times == 1:    #如果评论数小于30，就一次性获取
            for c in self.comments:
                url.append(c['user_id']+'%2C')
            url = ''.join(url)
            user_json = json.loads((requests.get(url)).text[1:-1])
            for i in range(len(self.comments)):
                self.comments[i]['user_influence'] = user_json['re'][i]['user_influ_level']
                self.comments[i]['user_age'] = user_json['re'][i]['user_age']
            return
        for t in range(times):    #否则，就分批获取
            url = ["http://iguba.eastmoney.com/interf/user.aspx?action=influence&uids="]
            for i in range(30):
                if (t*30+i) > (len(self.comments)-1):
                    break
                url.append('%s%%2C' % self.comments[t*30+i]['user_id'])
            url = ''.join(url)
            user_json = json.loads((requests.get(url)).text[1:-1])
            for i in range(30):
                if (t*30+i) > (len(self.comments)-1):
                    break         
                self.comments[t*30+i]['user_influence'] = user_json['re'][i]['user_influ_level']
                self.comments[t*30+i]['user_age'] = user_json['re'][i]['user_age']
   
    def get_comments_like_count(self):  #获取全部评论的点赞数据 
        times = math.ceil(len(self.comments)/30)   #次数
        url = ["http://iguba.eastmoney.com/interf/guba.aspx?action=getreplylikegd&id="
            +self.post_id+'&replyids=']
        if times == 1:        #如果评论数小于30，就一次性获取
            for c in self.comments:
                url.append('%s%%7C%s' % (c['id'],c['user_id']))
                url.append('%2C')
            url.pop() #把最后的%2C去掉
            url.append('&code=%s' % self.code)
            url = ''.join(url)  #得到json链接
            like_json = json.loads((requests.get(url)).text[1:-1])
            for i in range(len(self.comments)):
                self.comments[i]['like_count'] = like_json['result'][i]['count']
            return
        for t in range(times):   #否则分批获取。
            url = ["http://iguba.eastmoney.com/interf/guba.aspx?action=getreplylikegd&id="
            +self.post_id+'&replyids=']
            for i in range(30):
                if (t*30+i) > (len(self.comments)-1):
                    break
                url.append('%s%%7C%s' % (self.comments[t*30+i]['id'], self.comments[t*30+i]['user_id']))
                url.append('%2C')
            url.pop()  #把最后的%2C去掉
            url.append('&code=%s' % self.code)
            url = ''.join(url)  #得到json链接
            like_json = json.loads((requests.get(url)).text[1:-1])
            for i in range(30):
                if (t*30+i) > (len(self.comments)-1):
                    break
                self.comments[t*30+i]['like_count'] = like_json['result'][i]['count']
                
    def get_like_count(self):  #获取点赞
        text = get_html('http://iguba.eastmoney.com/interf/guba.aspx?action=getpraise&id=%s' % self.post_id)
        like_count = json.loads(text[1:-1])['count']
        return like_count

    def get_author_info(self):   #获取文章作者信息（包含吧龄和影响力） 
        text = get_html('http://iguba.eastmoney.com/interf/user.aspx?action=influence&uids=%s' % self.user_id)
        author_info = json.loads(text[1:-1])['re']
        author_info = author_info[0]
        return author_info

    def get_user_influ(self):    #获取作者影响力
        return (self.get_author_info())['user_influ_level']

    def get_user_age(self):      #获取作者年龄
        return (self.get_author_info())['user_age']

    def join(self,crawler):      #加入到crawler当中
        crawler.post_list.append(self)

    def get_comments(self, parser):  #获取主帖评论
        for num in range(self.page_count):
            url = self.url[:-5] + '_' + str(num+1) + '.html'
            html = load_page(url)
            if html == None:
                return 0
            #获取当前页的 所有评论 标签
            comments = parser.get_comment_list(html)
            for c in comments:  #每一个评论
                d = parser.get_comment_detail(c)
                comment = dict({
                        'id':d['comment_id'], 
                        'user_nickname': d['user_nickname'],
                        'user_id': d['user_id'],
                        'created_at': d['created_at'],
                        'content': d['content'], 
                        'reply_to':d['reply_to']
                        })
                self.comments.append(comment)

    def get_comment_queue(self):
        q = queue.Queue()
        #set q
        for num in range(self.page_count):
            url = self.url[:-5] + '_' + str(num+1) + '.html'
            q.put(url)
        self.q = q

    def get_comment(self, parser):
        url = self.q.get(timeout=2)
        html = load_page(url)
        if html == None:
            return
        time.sleep(0.1)
        #获取当前页的 所有评论 标签
        comments = parser.get_comment_list(html)
        for c in comments:  #每一个评论
            d = parser.get_comment_detail(c)
            comment = dict({
                    'id': d['comment_id'], 
                    'user_nickname': d['user_nickname'],
                    'user_id': d['user_id'],
                    'created_at': d['created_at'],
                    'content': d['content'], 
                    'reply_to': d['reply_to']
                    })
            self.comments.append(comment)
    """获取数据库中当前股票的最后更新时间"""
    def get_db_last_update_time(self, collection):
        time = collection.find({'url': self.url}, {'last_update_at': 1})[0]['last_update_at']
        return time
    """获取网站中当前股票的最后更新时间"""
    def get_last_comment_time(self, Parser):
        url = self.url[:-5] + ',d.html'
        html = load_page(url)
        time.sleep(0.1)
        last_comment_time = Parser.get_last_comment_time(html)
        return last_comment_time
    
    def get_post_content(self, Parser):
        html = load_page(self.url)
        time.sleep(0.1)
        content = Parser.get_post_content(html)
        return content
                
    
class commentThread(threading.Thread):
    def __init__(self, name, post, parser):
        threading.Thread.__init__(self)
        self.name = name
        self.parser = parser
        self.post = post
    def run(self):
        while True:
            try:
                self.post.get_comment(self.parser)
            except:
                break

class detailThread(threading.Thread):
    def __init__(self, name, parser, q, db):
        threading.Thread.__init__(self)
        self.name = name
        self.parser = parser
        self.q = q
        self.db = db
    def run(self):
        #print('%s开始保存' % self.name)
        while not (self.q).empty():
            data = (self.q).get(timeout=2)
            result = data.set_detail(self.parser)
            if result != 0:
                data.save(self.db)
            else:
                continue
        #print('%s保存完毕' % self.name)

class postThread(threading.Thread):
    def __init__(self, name, func, parser):
        threading.Thread.__init__(self)
        self.name = name
        self.parser = parser
        self.func = func
    def run(self):
        while True:
            try:
                self.func(self.parser)
            except:  #队列任务获取结束
                break