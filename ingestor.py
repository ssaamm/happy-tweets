import json
import sys

from tweepy import Stream, OAuthHandler, API
from tweepy.streaming import StreamListener
from kafka import KafkaProducer

from secrets import api_key, api_secret, access_token, access_secret

class KafkaAdapter(StreamListener):
    def __init__(self, topic='tweets'):
        super().__init__()
        self.producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
        self.topic = topic

    def on_status(self, status):
        self.producer.send(self.topic, json.dumps(status._json).encode('utf-8'))
        return True

if __name__ == '__main__':
    auth = OAuthHandler(api_key, api_secret)
    auth.set_access_token(access_token, access_secret)
    api = API(auth)

    stream = Stream(auth=api.auth, listener=KafkaAdapter())
    stream.filter(track=sys.argv[1:])
