import re
import redis
import queue
from download import load_page
from selenium import webdriver
from selenium.webdriver.chrome import options
from post import Post
from post import detailThread
from post import postThread
from post import commentThread
from parser import Parser
from db import MongoAPI
from user import User
#from pyvirtualdisplay import Display  


class Crawler:    #一个版块定义一个Crawler
    def __init__(self, link):
        self.link = link
        self.code = re.findall(',(.*).',self.link)[0][:-4]
        self.source = 'eastmoney'
        self.post_list = []  #存放Post对象的列表
        self.user_list = []  #存放User对象的列表
        self.post_list_q = None  #存放版块每一页的链接，如guba.eastmoney.com/list,300743_x.html
        
    def get_page_num(self):        #获取版块总页数
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('lang=zh_CN.UTF-8')
            chrome_options.add_argument('User-Agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            #display = Display(visible=0, size=(800, 800))  #linux服务器需要selenium需要用到
            #display.start()  
            driver = webdriver.Chrome(chrome_options=chrome_options)
            driver.get(self.link)
            page_num = driver.find_element_by_xpath('//div[@id="mainbody"]/div[@id="articlelistnew"]/div[@class="pager"]/span/span/span[@class="sumpage"]').text
            driver.quit()
        except:
            page_num = 1
        return int(page_num) 
    
    #获取Post
    def get_post(self, Parser):  #多线程获取文章列表，q为队列，存放页面数
        url = self.post_list_q.get(timeout=20)  #从队列中取一个链接
        html = load_page(url)
        posts = html.xpath('//div[@id="articlelistnew"]/div[@class="articleh"]') #所有文章
        posts_ele = Parser.get_page_ele(posts)  #获取文章的关键元素
        for e in posts_ele:
            if e['post_type'] == 'settop' or e['post_type'] == 'ad':  #如果是 讨论或大赛 类型就跳过
                continue
            p = Post(e['url'], e['user_nickname'], e['title'], e['post_type'], e['post_id'],
                    e['view_count'], e['comment_count'], self.code, self.source)
            self.post_list.append(p)

    def get_post_list_queue(self):   #存放版块页面链接的队列
        q = queue.Queue()
        for i in range(self.page_num):
            q.put(self.link[:-5]+'_'+str(i+1)+'.html')
        self.post_list_q = q
                           
    #获取用户列表
    def get_user_list(self, Parser):
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        for post in self.post_list:
            if ((post.user_id) != '') and (r.sismember('user_id', post.user_id)) == False:    #作者id不为空且未保留过
                self.user_list.append(User(post.user_id, post.user_nickname))
                r.sadd('user_id', post.user_id)                #将用户id存入redis
            for comment in post.comments:
                if (r.sismember('user_id', post.user_id)) == False:    #作者id不为空且未保留过
                    self.user_list.append(User(comment['user_id'], comment['user_nickname']))
                    r.sadd('user_id', comment['user_id'])                #将用户id存入redis
    
    def get_page_post(self, url, parser):
        html = load_page(url)
        posts = html.xpath('//div[@id="articlelistnew"]//div[@class="articleh"]') #所有文章    
        posts_ele = parser.get_page_ele(posts)   #获取文章的关键元素
        post_list = []
        for e in posts_ele:
            if e['post_type'] == 'settop' or e['post_type'] == 'ad':  #如果是 讨论或大赛 类型就跳过
                continue
            p = Post(e['url'], e['user_nickname'], e['title'], e['post_type'], e['post_id'],
                    e['view_count'], e['comment_count'], self.code, self.source)
            post_list.append(p)
        return post_list

    #抓取函数   
    def crawl(self):
        self.page_num = self.get_page_num()  #获取版块页数
        #获取存放版块页面链接的队列，如http://guba.eastmoney.com/list,300729_xxxxxx.html
        self.get_post_list_queue()
        print('本版块页数为:' + str(self.page_num))
        parser = Parser()
        # 获取版块页面的帖子列表
        thread_num = 6  #线程数设置为6
        thread_list = []
        for i in range(thread_num):  #获取如http://guba.eastmoney.com/list,300729_1.html页面的帖子的信息
            thread = postThread('Thread'+str(i+1), self.get_post, parser)
            thread.start()
            thread_list.append(thread)
        for thread in thread_list:
            thread.join()
        #print(len(self.post_list))  #打印该版块帖子数目
        # 获取帖子对象队列及帖子详情
        post_queue = queue.Queue()
        for post in self.post_list:
            post_queue.put(post)
        thread_list = [] 
        db = MongoAPI("localhost", 27017, "community", "post")
        for i in range(thread_num):     #从队列中获取post对象，并获取post的详细信息包括评论
            thread = detailThread('Thread'+str(i+1), parser, post_queue, db) 
            thread.start()
            thread_list.append(thread)
        for thread in thread_list:
            thread.join()
       
        #  获取用户队列及用户详情
        self.get_user_list(parser)  #获取用户列表
        db = MongoAPI("localhost", 27017, "community", "user")
        user_queue = queue.Queue()
        for user in self.user_list:  #将User对象插入队列中
            user_queue.put(user)
        thread_list = []
        for i in range(thread_num):   #获取用户详情
            thread = detailThread('Thread'+str(i+1), parser, user_queue, db)
            thread.start()
            thread_list.append(thread)
        for thread in thread_list:
            thread.join()
            
    #爬取新数据
    def crawl_new_data(self):
        parser = Parser()
        """获取新文章数据"""
        isNew = 1
        just_like = 0  #纪录纯点赞导致的帖子更新的数目
        page_num = 1  #设置初始页数
        db = MongoAPI("localhost", 27017, "community", "post")
        while isNew == 1:
            url = 'http://guba.eastmoney.com/list,' + self.code + '_' + str(page_num) +  '.html'  #从第一页开始往后
            try:
                post_list = self.get_page_post(url, parser)  #获取当前页面的所有帖子
            except:
                break
            for post in post_list:  #对每条主帖进行判断
                db_post = db.get_one({'url': post.url})  #从数据库中查询主帖
                if db_post != None:  #有记录说明该主帖已经被保存过 
                    update_time = db_post['last_update_at']  #获取该主帖在数据库中的最后更新时间
                    last_comment_time = post.get_last_comment_time(parser)  #获取主帖页面的最后评论时间
                    if update_time >= last_comment_time:  #若为普通主帖，则判断主帖和评论有无变更，点赞也可能把帖子置顶上去
                        #print('上次最后更新帖子%s，时间为%s' % (post.url, update_time))
                        just_like += 1
                        if just_like == 5:
                            isNew = 0
                            self.post_list = self.post_list[:-5]  #把五条无效旧帖删除
                            break
                    else:
                        just_like = 0
                self.post_list.append(post) 
                #print('这是新帖子，插入：%s' % post.url)   #在运行时，提示新帖子记录
            page_num += 1  #翻页
        """获取新文章的详细数据"""
        # 获取帖子对象队列及帖子详情
        post_queue = queue.Queue()
        for post in self.post_list:
            post_queue.put(post)
        thread_num = 5
        thread_list = []
        for i in range(thread_num):     #从队列中获取post对象，并获取post的详细信息包括评论
            thread = detailThread('Thread'+str(i+1), parser, post_queue, db) 
            thread.start()
            thread_list.append(thread)
        for thread in thread_list:
            thread.join()
        #  获取用户队列及用户详情
        self.get_user_list(parser)  #获取用户列表
        db = MongoAPI("localhost", 27017, "community", "user")
        for u in self.user_list:
            u.set_detail(parser)
            u.save(db)
        print("爬取代码:%s 页数:%s 文章数:%s 用户数:%s" % (self.code, page_num-1, len(self.post_list), len(self.user_list)))