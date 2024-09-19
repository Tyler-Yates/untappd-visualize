from datetime import timedelta

DATABASE_CONFIG_KEY = "db_config_key"

DB_NAME = "untappd"
BEERS_COLLECTION_NAME = "beers"
BREWERIES_COLLECTION_NAME = "breweries"
REDIS_VERSION = 6
REDIS_CACHE_TTL = timedelta(hours=1)

DATE_FORMAT_STRING = "%Y-%m-%d"
DATETIME_FORMAT_STRING = "%Y-%m-%dT%H:%M:%S"
