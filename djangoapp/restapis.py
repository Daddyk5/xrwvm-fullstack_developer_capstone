import logging
import os
from urllib.parse import quote

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

backend_url = os.getenv(
    'backend_url', default="http://localhost:3030")
sentiment_analyzer_url = os.getenv(
    'sentiment_analyzer_url',
    default="http://localhost:5050/")

REQUEST_TIMEOUT = 10


def get_request(endpoint, **kwargs):
    """GET from the backend service; returns parsed JSON or None on error."""
    request_url = backend_url + endpoint
    logger.info("GET from %s", request_url)
    try:
        response = requests.get(
            request_url, params=kwargs, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as err:
        logger.error("Network exception occurred: %s", err)
        return None


def analyze_review_sentiments(text):
    """Return the sentiment for a review; falls back to neutral on error."""
    request_url = sentiment_analyzer_url + "analyze/" + quote(text, safe="")
    try:
        response = requests.get(request_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as err:
        logger.error("Sentiment analysis failed: %s", err)
        return {"sentiment": "neutral"}


def post_review(data_dict):
    """Post a review to the backend; raises if the request fails."""
    request_url = backend_url + "/insert_review"
    response = requests.post(
        request_url, json=data_dict, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()
