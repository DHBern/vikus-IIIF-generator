import logging
import aioredis
import asyncio
import requests
import json
import os
import time
import logging
import sys
import numpy as np
import struct


class Cache:
    def __init__(self, *args, **kwargs):
        self.redis = kwargs.get(
            'redis', aioredis.from_url("redis://redis"))
        self.logger = kwargs.get('logger', logging.getLogger('cache'))
        self.psub = self.redis.pubsub()

    async def saveFeatures(self, id, a):
        # print("saveFeatures", a.shape)
        encoded = a.tobytes()
        # Store encoded data in Redis
        return await self.redis.set("f{}".format(id), encoded)

    async def getFeatures(self, id):
        encoded = await self.redis.get("f{}".format(id))
        if encoded is None:
            return None
        features = np.frombuffer(encoded, dtype=np.float32, count=512)
        # print("getFeatures", a.shape)
        return features

    async def getJsonFromUrl(self, url, session=None, retries=5):
        for i in range(retries):
            try:
                if session is None:
                    response = requests.get(url).text
                    return response.encode('utf-8')

                async with session.get(url) as response:
                    text = await response.text(encoding='utf-8')
                    return text

            except Exception as e:
                self.logger.error(e)
                self.logger.error("retry {i} {url}" .format(i=i, url=url))
                await asyncio.sleep(1)
        return None

    async def getJson(self, url, session=None, retries=5):
        self.logger.debug("get cache for {}".format(url))
        if await self.redis.exists(url):
            self.logger.debug("cache hit")
            cached = await self.redis.get(url)
            return json.loads(cached)
        else:
            self.logger.debug("cache miss")
            data = await self.getJsonFromUrl(url, session, retries)
            if data is not None:
                self.logger.debug("cache set")
                await self.redis.set(url, data)
                return json.loads(data)
            else:
                return None


async def main():
    cache = Cache()

    await cache.redis.set('test', 'test')
    print(await cache.redis.get('test'))


if __name__ == "__main__":
    asyncio.run(main())
