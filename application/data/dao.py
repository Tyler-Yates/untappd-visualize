import logging
import os
import pickle
from collections import defaultdict
from statistics import median

import fakeredis
import redis
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from application.constants import DB_NAME, REDIS_VERSION, BEERS_COLLECTION_NAME, REDIS_CACHE_TTL, \
    BREWERIES_COLLECTION_NAME, COUNTRIES
from application.data.beer import Beer
from application.data.brewery import Brewery
from application.data.country import Country
from application.data.style import Style

LOG = logging.getLogger(__name__)


class ApplicationDao:
    def __init__(self, database: Database = None, cache: redis.Redis = None):
        # If no cache is given, spin up a fake one
        if cache is None:
            self.cache = fakeredis.FakeStrictRedis(version=REDIS_VERSION)
        else:
            self.cache = cache

        # Support resetting the cache for development testing
        if os.environ.get("RESET_CACHE", "false") == "true":
            LOG.info("Flushing cache")
            self.cache.flushall()

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
            # noinspection PyTypeChecker
            return pickle.loads(serialized_beer_list)

        documents = self.beers_collection.find()
        beers = [Beer(**{k: v for k, v in doc.items() if k != '_id'}) for doc in documents]

        serialized_data = pickle.dumps(beers)
        self.cache.set("beer_list", serialized_data, ex=REDIS_CACHE_TTL)

        return beers

    def get_breweries(self) -> list[Brewery]:
        serialized_breweries_list = self.cache.get("breweries_list")
        if serialized_breweries_list:
            # noinspection PyTypeChecker
            return pickle.loads(serialized_breweries_list)

        documents = self.breweries_collection.find()
        brewery_id_to_beers = self._get_brewery_to_beers()

        breweries = []
        for document in documents:
            full_location = document["full_location"]
            brewery_id = document["id"]

            ratings = [b.rating for b in brewery_id_to_beers[brewery_id]]
            filtered_ratings = [value for value in ratings if value != -1.0]
            avg_rating = sum(filtered_ratings) / len(filtered_ratings) if filtered_ratings else -1

            brewery = Brewery(
                id=brewery_id,
                name=document["name"],
                type=document["type"],
                full_location=full_location,
                num_checkins=len(ratings),
                num_checkins_with_ratings=len(filtered_ratings),
                avg_rating=avg_rating,
                country=self._get_country(full_location)
            )
            breweries.append(brewery)

        serialized_data = pickle.dumps(breweries)
        self.cache.set("breweries_list", serialized_data, ex=REDIS_CACHE_TTL)

        return breweries

    @staticmethod
    def _get_country(full_location: str) -> str:
        full_location = full_location.strip()
        for country in COUNTRIES:
            if full_location.endswith(country):
                return country

        return "?"

    def get_countries(self) -> list[Country]:
        serialized_countries_list = self.cache.get("countries_list")
        if serialized_countries_list:
            # noinspection PyTypeChecker
            return pickle.loads(serialized_countries_list)

        breweries = self.get_breweries()
        country_to_breweries = defaultdict(list)
        for brewery in breweries:
            country_to_breweries[brewery.country].append(brewery)

        countries = []
        for country in country_to_breweries.keys():
            country_breweries = country_to_breweries[country]
            num_breweries = len(country_breweries)
            num_checkins = sum(brewery.num_checkins for brewery in country_breweries)

            num_rated_checkins = sum(brewery.num_checkins_with_ratings for brewery in country_breweries)
            if num_rated_checkins > 0:
                total_rating = sum(
                    brewery.avg_rating * brewery.num_checkins_with_ratings for brewery in country_breweries)
                avg_rating = total_rating / num_rated_checkins
            else:
                avg_rating = -1

            countries.append(Country(name=country, num_breweries=num_breweries, num_checkins=num_checkins,
                                     avg_rating=avg_rating))

        serialized_data = pickle.dumps(countries)
        self.cache.set("countries_list", serialized_data, ex=REDIS_CACHE_TTL)

        return countries

    def _get_brewery_to_beers(self) -> dict[str, list[Beer]]:
        brewery_id_to_checkins = defaultdict(list)
        beers = self.get_beers()

        for beer in beers:
            brewery_id = beer.brewery_id
            brewery_id_to_checkins[brewery_id].append(beer)

        return brewery_id_to_checkins

    def get_styles(self) -> list[Style]:
        serialized_styles_list = self.cache.get("styles_list")
        if serialized_styles_list:
            # noinspection PyTypeChecker
            return pickle.loads(serialized_styles_list)

        beers = self.get_beers()
        style_to_ratings = defaultdict(list)
        for beer in beers:
            style_to_ratings[beer.style].append(beer.rating)

        styles = []
        for style_name, ratings in style_to_ratings.items():
            filtered_ratings = [value for value in ratings if value != -1.0]

            num_checkins = len(ratings)
            avg_rating = sum(filtered_ratings) / len(filtered_ratings) if filtered_ratings else -1
            median_rating = median(filtered_ratings) if filtered_ratings else -1
            min_rating = min(filtered_ratings) if filtered_ratings else -1
            max_rating = max(filtered_ratings) if filtered_ratings else -1
            style = Style(name=style_name, num_checkins=num_checkins, min_rating=min_rating, max_rating=max_rating,
                          avg_rating=avg_rating, median_rating=median_rating)
            styles.append(style)

        serialized_data = pickle.dumps(styles)
        self.cache.set("styles_list", serialized_data, ex=REDIS_CACHE_TTL)

        return styles
