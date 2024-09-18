from datetime import timedelta

DATABASE_CONFIG_KEY = "db_config_key"

DB_NAME = "untappd"
COLLECTION_NAME = "beers"
REDIS_VERSION = 6
REDIS_CACHE_TTL = timedelta(hours=6)

DATE_FORMAT_STRING = "%Y-%m-%d"
DATETIME_FORMAT_STRING = "%Y-%m-%dT%H:%M:%S"
