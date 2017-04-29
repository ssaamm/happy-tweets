import asyncio
from collections import namedtuple
import json
import itertools as it
import random

from kafka.common import KafkaError
from aiokafka import AIOKafkaConsumer
import websockets

from nltk.sentiment.vader import SentimentIntensityAnalyzer
import numpy as np
from shapely.geometry import Point, Polygon, box


def pairwise(iterable):
    """ https://docs.python.org/3/library/itertools.html?highlight=pairwise """
    a, b = it.tee(iterable)
    next(b, None)
    return zip(a, b)


class SentimentRegion(object):
    def __init__(self, polygon):
        self.region = polygon
        self.sum = 0
        self.count = 0

    def __lt__(self, other):
        return self.region.bounds < other.region.bounds

    @property
    def avg_sentiment(self):
        try:
            return self.sum / self.count
        except ZeroDivisionError:
            return np.nan


class Earth(object):
    def __init__(self, resolution=50):
        self.resolution = resolution

        lat_intervals = [(a, b) for a, b in pairwise(np.linspace(-85, 85, num=resolution+1))]
        lon_intervals = [(a, b) for a, b in pairwise(np.linspace(-180, 180, num=resolution+1))]
        self.grid = [SentimentRegion(box(lon_itv[0], lat_itv[0], lon_itv[1], lat_itv[1]))
                     for lat_itv in lat_intervals for lon_itv in lon_intervals]

    def update(self, polygon, sentiment):
        updates = []
        for tile_id, sent_region in enumerate(self.grid):
            if not sent_region.region.intersects(polygon):
                continue

            sent_region.sum += sentiment
            sent_region.count += 1

            yield (tile_id, sent_region.avg_sentiment)

    def print_grid(self):
        for ndx, sent_region in enumerate(sorted(self.grid)):
            print('{:.1f}'.format(sent_region.avg_sentiment), end=' ')
            if ndx % self.resolution == self.resolution - 1:
                print()

    @property
    def polygons(self):
        return [list((c[1], c[0]) for c in sent_region.region.exterior.coords) for sent_region in self.grid]


def handle_tweet(tweet, earth, sent_analyzer):
    if tweet['lang'] != 'en':
        return

    if tweet['place'] is not None:
        sentiment = sent_analyzer.polarity_scores(tweet['text'])['compound']

        bounding_box = tweet['place']['bounding_box']
        assert bounding_box['type'] == 'Polygon'
        assert len(bounding_box['coordinates']) == 1

        polygon = Polygon(bounding_box['coordinates'][0])
        yield from earth.update(polygon, sentiment)


async def consume_task(consumer, earth, sent_analyzer):
    while True:
        try:
            msg = await consumer.getone()
            updates = list(handle_tweet(json.loads(msg.value.decode('utf-8')), earth, sent_analyzer))
            if updates:
                print(updates)
        except KafkaError as err:
            print(err)


async def updates(websocket, path):
    sent_analyzer = SentimentIntensityAnalyzer()
    earth = Earth(50)

    await websocket.send(json.dumps({'type': 'initialize', 'polygons': earth.polygons}))

    consumer = AIOKafkaConsumer('tweets', loop=loop, bootstrap_servers='localhost:9092')
    await consumer.start()

    try:
        async for msg in consumer:
            for tile_id, sentiment in handle_tweet(json.loads(msg.value.decode('utf-8')), earth, sent_analyzer):
                await websocket.send(json.dumps({'type': 'update', 'tile_id': tile_id, 'score': sentiment}))
    finally:
        await consumer.stop()

    while True:
        await asyncio.sleep(0.5)

if __name__ == '__main__':
    start_server = websockets.serve(updates, 'localhost', 5000)
    loop = asyncio.get_event_loop()
    loop.create_task(start_server)
    loop.run_forever()
