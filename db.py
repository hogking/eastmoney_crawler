from pymongo import MongoClient

class MongoAPI(object):
    def __init__(self, db_ip, db_port, db_name, collection_name):
        self.db_ip = db_ip
        self.db_port = db_port
        self.db_name = db_name
        self.collection_name = collection_name
        self.conn = MongoClient(self.db_ip, self.db_port)
        self.db = self.conn[self.db_name]
        self.collection = self.db[self.collection_name]

    def get_one(self, query):
        return self.collection.find_one(query, projection = {"_id": False})

    def get_all(self, query):
        return self.collection.find(query)

    def add_one(self, kv_dict):
        return self.collection.insert_one(kv_dict)

    def add_many(self, kv_dict):
        return self.collection.insert_many(kv_dict)

    def delete(self, query):
        return self.collection.delete_many(query)

    def check_exist(self, query):
        ret = self.collection.find_one(query)
        return ret != None

    def update(self, query, kv_dict):
        self.collection.update_one(query, {
            '$set': kv_dict
        }, upsert=True)
