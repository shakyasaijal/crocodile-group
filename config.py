import os

class Config:
    SECRET_KEY = os.urandom(24)
    MONGO_URI = 'mongodb://saijalshakya1:saijalshakya@ac-ubbbco8-shard-00-00.wysv8uc.mongodb.net:27017,ac-ubbbco8-shard-00-01.wysv8uc.mongodb.net:27017,ac-ubbbco8-shard-00-02.wysv8uc.mongodb.net:27017/?ssl=true&replicaSet=atlas-1bq327-shard-0&authSource=admin&retryWrites=true&w=majority&appName=College'

config = Config()
