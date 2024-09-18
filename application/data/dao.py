import logging
import os
import pickle

import fakeredis
import redis
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from application.constants import DB_NAME, REDIS_VERSION, COLLECTION_NAME, REDIS_CACHE_TTL
from application.data.beer import Beer

LOG = logging.getLogger(__name__)


class ApplicationDao:
    def __init__(self, database: Database = None, cache: redis.Redis = None):
        # If no cache is given, spin up a fake one
        if cache is None:
            self.cache = fakeredis.FakeStrictRedis(version=REDIS_VERSION)
        else:
            self.cache = cache

        # If no database provided, connect to one
        if database is None:
            username = os.environ.get("MONGO_USER")
            password = os.environ.get("MONGO_PASSWORD")
            host = os.environ.get("MONGO_HOST")
            self.client = MongoClient(
                f"mongodb+srv://{username}:{password}@{host}/{DB_NAME}?retryWrites=true&w=majority"
            )

            database: Database = self.client[DB_NAME]

        # Set up database and collection variables
        self.database = database
        self.collection: Collection = self.database[COLLECTION_NAME]

        LOG.info(f"Database collections: {self.database.list_collection_names()}")

    def get_beers(self) -> list[Beer]:
        serialized_beer_list = self.cache.get("beer_list")
        if serialized_beer_list:
            return pickle.loads(serialized_beer_list)

        documents = self.collection.find()
        beers = [Beer(**{k: v for k, v in doc.items() if k != '_id'}) for doc in documents]

        serialized_data = pickle.dumps(beers)
        self.cache.set("beer_list", serialized_data, ex=REDIS_CACHE_TTL)

        return beers
