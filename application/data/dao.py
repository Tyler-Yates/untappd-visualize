import logging
import os
import pickle
from collections import defaultdict

import fakeredis
import redis
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from application.constants import DB_NAME, REDIS_VERSION, BEERS_COLLECTION_NAME, REDIS_CACHE_TTL, \
    BREWERIES_COLLECTION_NAME
from application.data.beer import Beer
from application.data.brewery import Brewery

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
        self.beers_collection: Collection = self.database[BEERS_COLLECTION_NAME]
        self.breweries_collection: Collection = self.database[BREWERIES_COLLECTION_NAME]

        LOG.info(f"Database collections: {self.database.list_collection_names()}")

    def get_beers(self) -> list[Beer]:
        serialized_beer_list = self.cache.get("beer_list")
        if serialized_beer_list:
            return pickle.loads(serialized_beer_list)

        documents = self.beers_collection.find()
        beers = [Beer(**{k: v for k, v in doc.items() if k != '_id'}) for doc in documents]

        serialized_data = pickle.dumps(beers)
        self.cache.set("beer_list", serialized_data, ex=REDIS_CACHE_TTL)

        return beers

    def get_breweries(self) -> list[Brewery]:
        serialized_breweries_list = self.cache.get("breweries_list")
        if serialized_breweries_list:
            return pickle.loads(serialized_breweries_list)

        documents = self.breweries_collection.find()
        brewery_id_to_checkins = self.get_brewery_checkins()

        breweries = []
        for document in documents:
            brewery = Brewery(
                id=document["id"],
                name=document["name"],
                type=document["type"],
                full_location=document["full_location"],
                num_checkins=brewery_id_to_checkins.get(document["id"], 0)
            )
            breweries.append(brewery)

        serialized_data = pickle.dumps(breweries)
        self.cache.set("breweries_list", serialized_data, ex=REDIS_CACHE_TTL)

        return breweries

    def get_brewery_checkins(self) -> dict[str, int]:
        brewery_id_to_checkins = defaultdict(int)
        beers = self.get_beers()

        for beer in beers:
            brewery_id = beer.brewery_id
            brewery_id_to_checkins[brewery_id] += 1

        return brewery_id_to_checkins
