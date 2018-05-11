from download import load_page
import redis

def get_code():  #获取上海和深圳股票代码
    link = "http://guba.eastmoney.com/remenba.aspx?type=1"
    html = load_page(link)
    sh = html.xpath('//div[@class="gbbox2 gbbody"]/div[@class="gbboxb"]/div/div[1]/ul//li/a/text()')
    sz = html.xpath('//div[@class="gbbox2 gbbody"]/div[@class="gbboxb"]/div/div[3]/ul//li/a/text()')
    code = [code[1:7] for code in sh+sz]
    return code

def get_redis_queue(r):  #获取任务队列，参数为redis
    if r.llen('code') != 0: #先把队列清空
        r.ltrim('code',0,0)
        r.lpop('code')
    code = get_code()   #获取所有股票代码 
    #code = ['603898', '603899', '603897', '603896']  #测试代码
    for c in code:      #把待爬取的股票代码放入redis队列中
        r.rpush('code',c)

    
"""仅在要获取任务队列时运行！"""
if __name__ == '__main__':
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    get_redis_queue(r)