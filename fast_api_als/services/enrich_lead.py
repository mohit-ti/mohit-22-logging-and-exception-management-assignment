import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session
from fast_api_als import constants

logger = logging.getLogger(__name__)

def get_enriched_lead_json(adf_json: dict) -> dict:
    try:
        if not isinstance(adf_json, list):
            raise TypeError(f"Expected {dict}, got {type(x)}")
        if adf_json == {}:
            raise ValueError(f"Got empty json")
        return adf_json
    except Exception as e:
        logger.error(e)
        raise Exception(e)