# eastmoney_crawler
使用多进程、多线程爬取东方财富股吧沪深股票文章、评论及发言用户信息。

### 说明

请求：requests

解析：lxml

数据库：mongodb

消息队列：redis

全站爬取时需要使用到selenium获取股吧页面数目，若程序放在linux服务器上运行，则需要在crawl.py中导入pyvirtualdisplay，并且在使用selenium的`get_page_num()`中加上

```
display = Display(visible=0, size=(800, 800))  

display.start() 
```

**mongodb与redis默认连接为localhost**。

### 任务

任务定义在redis_queue.py中，默认爬取上海+深圳股票的股吧帖子。

### 运行模式

程序可进行**全部爬取**或者**增量更新**。

若要使用增量更新，将main.py中`method = 'update'`即可。

