import datetime
import time
import queue
import redis
from multiprocessing import Process
from multiprocessing import Pool
from db import MongoAPI
from crawler import Crawler
import redis_queue 

#用于增量爬取更新的文章
def get_post(method, i):
    queue = redis.StrictRedis(host='localhost', port=6379, db=0)
    mongodb = MongoAPI("localhost", 27017, "community", "post") 
    while queue.llen('code') != 0:  #若队列中还有任务，就爬取该代码内容
        try:
            start = time.time()
            code = queue.lpop('code').decode()  #从队列中获取一个代码 
            url = "http://guba.eastmoney.com/list," + code + '.html'
            print('进程%s开始爬取%s,链接：%s' % (i, code, url))  
            c = Crawler(url)
            if method != 'update':  #参数不为'update'，则会爬取全部文章
                c.crawl()
            elif mongodb.check_exist({'code': code}) == False:  #如果数据库中不含该股票的帖子数据，说明未爬取过
                print('不存在%s的记录，全爬取' % code)
                c.crawl()
            else:
                c.crawl_new_data()
            end = time.time()
            print('进程%s爬取%s完毕，当前时间：%s，耗费时间: %s\n' % (i, code, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), str(end-start)))
        except:
            continue
        
if __name__ == "__main__":
    #获取任务队列
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    redis_queue.get_redis_queue(r)
    #开始时间
    start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('开始时间：%s\n' % start_time)
    #多进程执行
    p = Pool(8)  #设置进程数
    #update为增量更新
    #method = 'update'  #'update'为增量爬取，若为其它变量，则为首次全爬取
    method = 'all'
    for i in range(9):
        p.apply_async(get_post, args=(method,i))  #多进程获取数据
    p.close()
    p.join()
    #结束时间
    end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('结束时间：%s' % end_time)
    print('爬取结束')