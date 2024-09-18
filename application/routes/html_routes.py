import logging

from flask import Blueprint, current_app, render_template

from application.constants import DATABASE_CONFIG_KEY
from application.data.dao import ApplicationDao

LOG = logging.getLogger(__name__)
HTML_BLUEPRINT = Blueprint("routes_html", __name__)
DEFAULT_DAYS_BACK = 7


@HTML_BLUEPRINT.route("/")
def homepage():
    beers = _get_dao().get_beers()

    return render_template("index.html", beers=beers)


def _get_dao() -> ApplicationDao:
    return current_app.config[DATABASE_CONFIG_KEY]
