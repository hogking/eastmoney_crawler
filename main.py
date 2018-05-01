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
def get_post(method):
    queue = redis.StrictRedis(host='localhost', port=6379, db=0)
    while queue.llen('code') != 0:  #若队列中还有任务
        start = time.time()
        code = queue.lpop('code').decode()  #从队列中获取一个代码
        url = "http://guba.eastmoney.com/list," + code + '.html'
        print('开始爬取%s,链接：%s' % (code,url))
        c = Crawler(url)
        if method != 'update':
            c.crawl()
        else:
            c.crawl_new_data()
        end = time.time()
        print('爬取%s完毕，耗费时间: %s\n' % (code, str(end-start)))
        
if __name__ == "__main__":
    #获取任务队列
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    redis_queue.get_redis_queue(r)
    #开始时间
    start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('开始时间：%s\n' % start_time)
    #多进程执行
    p = Pool(5)
    #update为增量更新
    method = 'update'
    #get_post(method)
    for i in range(6):
        p.apply_async(get_post, args=(method,))  #用于获取增量数据
    p.close()
    p.join()
    #结束时间
    end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('结束时间：%s' % end_time)
    print('爬取结束')