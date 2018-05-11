import datetime
from download import load_page

class User(object):
    def __init__(self, user_id, user_nickname):
        self.id = user_id  #用户id
        self.nickname = user_nickname  #昵称
        
    def set_detail(self, parser):
        self.url = 'http://iguba.eastmoney.com/' + self.id  #页面链接
        try:
            html = load_page(self.url)
            self.avator = parser.get_user_avator(html)  #头像
            self.avator = ''
            self.reg_date = datetime.datetime.strptime(parser.get_user_reg_date(html),"%Y-%m-%d")  #注册日期
            self.following_count = parser.get_user_following_count(html)  #关注数
            self.fans_count = parser.get_user_fans_count(html)  #粉丝数
            self.influence = parser.get_user_influence(html)  #影响力
            self.introduce = parser.get_user_introduce(html)  #个人简介
            self.visit_count = parser.get_user_visit_count(html)  #访问数
            self.post_count = parser.get_user_post_count(html)  #发帖数
            self.comment_count = parser.get_user_comment_count(html)  #回帖数
            self.optional_count = parser.get_user_optional_count(html)  #自选股数
            self.capacity_circle = parser.get_user_capacity_circle(html)  #能力圈
            self.source = 'eastmoney'
            return 1
        except:
            return 0
    def save(self, db):
        db.update({'id': self.id}, {
            'id': self.id,
            'url': self.url,
            'nickname': self.nickname,
            'avator': self.avator,
            'reg_date': self.reg_date,
            'following_count': self.following_count,
            'fans_count': self.fans_count,
            'influence': self.influence,
            'introduce': self.introduce,
            'visit_count': self.visit_count,
            'post_count': self.post_count,
            'comment_count': self.comment_count,
            'optional_count': self.optional_count,
            'capacity_circle': self.capacity_circle,
            'source': self.source,
        })