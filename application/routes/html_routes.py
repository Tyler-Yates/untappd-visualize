import logging

from flask import Blueprint, current_app, render_template

from application.constants import DATABASE_CONFIG_KEY
from application.data.dao import ApplicationDao

LOG = logging.getLogger(__name__)
HTML_BLUEPRINT = Blueprint("routes_html", __name__)
DEFAULT_DAYS_BACK = 7


@HTML_BLUEPRINT.route("/")
def homepage():
    return render_template("index.html")


@HTML_BLUEPRINT.route("/breweries")
def breweries():
    breweries = _get_dao().get_breweries()

    return render_template("breweries.html", breweries=breweries)


@HTML_BLUEPRINT.route("/beers")
def beers():
    beers = _get_dao().get_beers()

    return render_template("beers.html", beers=beers)


def _get_dao() -> ApplicationDao:
    return current_app.config[DATABASE_CONFIG_KEY]
