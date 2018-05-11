import re
import datetime
import lxml

"""用于解析页面，参数html为etree元素"""
class Parser(object):
    def get_last_comment_time(self, html):  #获取文章的最后更新时间
        try:
            last_comment_time = html.xpath('//div[@id="zwlist"]/div[@class="zwli clearfix"][1]/div[@class="zwlitx"]/div/div[@class="zwlitime"]')[0].text.split('发表于')[1].strip()
            last_comment_time = datetime.datetime.strptime(last_comment_time, "%Y-%m-%d %H:%M:%S")  #把字符串转为datetime类型
        except:
            last_comment_time = self.get_post_time(html)  #若没有评论，就返回发帖时间
        return last_comment_time
    
    def get_comment_list(self, html):  #获取文章的评论列表
        comments = html.xpath('//div[@id="mainbody"]/div[@id="zwlist"]//div[@class="zwli clearfix"]')
        return comments
    
    def get_comment_detail(self, comment):  #获取文章的评论的细节
        comment_id = comment.attrib['data-huifuid']
        user_id = comment.attrib['data-huifuuid']
        if len(comment.xpath('div[@class="zwlitx"]/div/div[@class="zwlianame"]/span/a'))!=0:
            user_nickname = comment.xpath('div[@class="zwlitx"]/div/div[@class="zwlianame"]/span/a')[0].text
        else:  #如果回帖者是如来自Android客户端的“上海网友”，则评论会没有用户id信息
            user_nickname = comment.xpath('div[@class="zwlitx"]/div/div[@class="zwlianame"]/span/span')[0].text
            user_id = 'Null'
            #print(user_nickname, user_id)
        created_at = comment.xpath('div[@class="zwlitx"]/div/div[@class="zwlitime"]')[0].text.split('发表于')[1].strip()
        created_at = datetime.datetime.strptime(created_at,"%Y-%m-%d %H:%M:%S")
        content = self.get_comment_content(comment)
        reply_to = self.get_comment_reply_to(comment)
        return dict({'comment_id': comment_id,
                     'user_id': user_id,
                     'user_nickname': user_nickname,
                     'created_at': created_at,
                     'content': content,
                     'reply_to': reply_to
        })
   
    def get_comment_content(self, comment):    #获取评论内容
        comment_content = ''
        comment_imgs = comment.xpath('div[@class="zwlitx"]/div/div[@class="zwlitext stockcodec"]/img')
        if len(comment_imgs) != 0:
            for img in comment_imgs:
                try:
                    comment_content += '['+img.attrib['title']+']'
                except:
                    continue
        content = comment.xpath('div[@class="zwlitx"]/div/div[@class="zwlitext stockcodec"]//text()')
        if len(content) != 0:
            for i in range(len(content)):
                comment_content += content[i].strip()
        return comment_content
    
    def get_comment_reply_to(self, comment):  #获取评论 回复的评论 内容
        reply_to = comment.xpath('div[@class="zwlitx"]/div/div[@class="zwlitalkbox clearfix"]')
        if len(reply_to) == 0:
            return ''
        if len(reply_to[0].xpath('div/a')) != 0:
            reply_to_user_nickname = reply_to[0].xpath('div/a')[0].text.strip()
        else:  #如果回复的对象是如“http://guba.eastmoney.com/news,600000,176775237_2.html#storeply”
            reply_to_user_nickname = reply_to[0].xpath('div/span')[0].text.strip()
        reply_to_comment = ''
        reply_to_comment_imgs = reply_to[0].xpath('div/span/img')
        if len(reply_to_comment_imgs) != 0:
            for img in reply_to_comment_imgs:
                reply_to_comment += '['+img.attrib['title']+']'
        #if (reply_to[0].xpath('div/span'))!= None and len((reply_to[0].xpath('div//span'))) != 0:
        try:
            if len(reply_to[0].xpath('div//span')) == 1:
                reply_to_comment += reply_to[0].xpath('div/span[1]//text()')[0].strip()
            elif len(reply_to[0].xpath('div//span')) == 2:
                reply_to_comment += reply_to[0].xpath('div/span[2]//text()')[0].strip()
        except:
            pass
        reply_to_comment_id = reply_to[0].xpath('div')[0].attrib['data-huifuid']
        reply_to_dict = {
                    'reply_to_user_nickname': reply_to_user_nickname,
                    'reply_to_comment': reply_to_comment,
                    'reply_to_comment_id': reply_to_comment_id
        }
        return reply_to_dict

    
    def get_post_title(self, html):  #获取文章标题
        try:
            title = html.xpath('//div[@id="zwcontent"]//div[@id="zwconttbt"]/text()')[0].strip()
        except:
            title = ''
        return title
    
    def get_post_question(self, html):  #获取文章问题
        q = html.xpath('//div[@id="zwcontent"]/div[@class="zwcontentmain"]/div[@class="qa"]/div[@class="question"]/div')[0].text
        return q
    
    def get_post_answer(self, html):  #获取文章答复
        a =  html.xpath('//div[@id="zwcontent"]/div[@class="zwcontentmain"]/div[@class="qa"]/div[@class="answer_wrap"]\
        /div/div[@class="content_wrap"]')[0]
        a_from = a.xpath('div[@class="sign"]/span')[0].text[1:-1].split('来自')[1].strip()
        a_time = (a.xpath('div[@class="sign"]/text()'))[1].split('答复时间')[1].strip()
        a_content = (a.xpath('div[@class="content"]/text()'))[1].strip()
        return dict({'from': a_from, 'time': a_time, 'content': a_content})
    
    def get_news_content(self, html):  #获取新闻内容
        news_content = ''
        content = html.xpath('//div[@id="zwconbody"]/div[@class="stockcodec"]/div[@id="zw_body"]//p//text()')
        for c in content:
            news_content += (c.strip()+'\n')
        return news_content
    
    def get_post_content(self, html):  #获取文章内容
        post_content = ''
        imgs = html.xpath('//div[@id="zwconbody"]/div[@class="stockcodec"]/img')
        if len(imgs)!= 0:
            for img in imgs:
                try:
                    post_content += ('['+img.attrib['title']+']')
                except:
                    continue
        content = html.xpath('//div[@id="zwconbody"]/div[@class="stockcodec"]/text()')
        for s in content:
            post_content += (s.strip())
        post_content = post_content.strip()
        return post_content
    
    def get_post_time(self, html):  #获取文章发表时间
        try:
            post_time = html.xpath('//div[@id="zwcontent"]/div[@id="zwcontt"]/div[@id="zwconttb"]/div[2]')[0].text
            post_time = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',post_time)[0]
            post_time = datetime.datetime.strptime(post_time,"%Y-%m-%d %H:%M:%S")
        except:
            post_time = datetime.datetime.strptime('1970-01-01 12:00:00',"%Y-%m-%d %H:%M:%S")
        return post_time
   
    def get_author_id(self, html):  #获取文章作者id
        try:   #资讯类号不存在userid
            author_id = html.xpath('//div[@id="zwconttphoto"]/a')[0].attrib['data-popper']
        except:
            author_id = ''
        return author_id
    
    def get_page_ele(self, posts):  #获取版块某一页的文章的关键元素 
        ele_list = []
        for p in posts:
            try:
                url = p.xpath('span[@class="l3"]/a')[0].attrib['href']
                if url[0] == '/':  #有的链接首个字符带有/，有的没有，要做判断
                    url = url[1:]
            except:
                continue
            post_type = p.xpath('span[@class="l3"]/em/@class')  #以下为判断文章的类型
            if len(post_type) != 0:  #如果不是普通帖子，且类型是《大赛》或者《话题讨论》，则跳过
                post_type = post_type[0]
                if post_type == 'ad' or post_type == 'settop':
                    continue
            else:
                post_type = 'normal'
            try:
                title = p.xpath('span[@class="l3"]/a')[0].text
                last_update_time = p.xpath('span[@class="l3"]/em/@class')
                view_count = p.xpath('span[@class="l1"]')[0].text #阅读数量
                comment_count = p.xpath('span[@class="l2"]')[0].text #评论数量
                if len(p.xpath('span[@class="l4"]/a'))!= 0:  #用户昵称有可能为如“上海手机网友”的情况。如http://guba.eastmoney.com/news,600000,177049240.html
                    user_nickname = p.xpath('span[@class="l4"]/a')[0].text
                else:
                    user_nickname = p.xpath('span[@class="l4"]/span')[0].text
            except:
                print('出问题了%s:%s' % (url,title))
                continue
            p_ele = dict({
                'url': 'http://guba.eastmoney.com/' + url,
                'user_nickname': user_nickname,
                'title': title,
                'post_type': post_type,
                'last_update_time' : last_update_time,
                'post_id': re.findall(r'(\d*).html',url)[0],
                'view_count': view_count,
                'comment_count': comment_count
            })
            ele_list.append(p_ele)       
        return ele_list
    """以下函数为获取用户信息"""
    def get_user_reg_date(self, html):
        return html.xpath('//div[@id="influence"]/span/text()')[1][1:-1] #注册时间 
    def get_user_avator(self, html):
        return html.xpath('//div[@class="tainfo"]/div[@class="photo"]/img/@src')[0]  #头像链接
    def get_user_fans_count(self, html):
        return html.xpath('//div[@class="tainfo"]/div[@class="photo"]/div[@class="tanums"]//td//text()')[4] #粉丝数
    def get_user_following_count(self, html):
        return html.xpath('//div[@class="tainfo"]/div[@class="photo"]/div[@class="tanums"]//td//text()')[2] #关注数
    def get_user_influence(self, html):
        return html.xpath('//div[@id="influence"]/span/@data-influence')[0] #影响力
    def get_user_introduce(self, html):
        return html.xpath('//div[@class="tainfos"]/div[@class="taintro"]/text()')[0].strip() #介绍
    def get_user_visit_count(self, html):
        return html.xpath('//div[@class="tainfos"]/div[@class="sumfw"]/span/text()')[0][:-1]  #总访问
    def get_user_post_count(self, html):
        return re.findall('（.*）',html.xpath('//div[@id="mainbody"]/div[@class="grtab5"]//a/text()')[0])[0][1:-1]  #发帖数
    def get_user_comment_count(self, html):
        return re.findall('（.*）',html.xpath('//div[@id="mainbody"]/div[@class="grtab5"]//a/text()')[1])[0][1:-1]  #评论数
    def get_user_optional_count(self, html):
        return html.xpath('//div[@class="tainfo"]/div[@class="photo"]/div[@class="tanums"]//td//text()')[0] #自选股数
    def get_user_capacity_circle(self, html):  ##能力圈
        code_list = []
        capacity_circle = html.xpath('//div[@id="influence"]//a/@href')
        if len(capacity_circle)!=0:
            for i in capacity_circle:    #能力圈股票代码
                code_list.append(re.findall(',(.*).html',i)[0])
        return code_list