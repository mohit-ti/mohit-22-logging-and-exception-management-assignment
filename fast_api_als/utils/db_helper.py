import json
import logging

import boto3
from boto3.dynamodb.conditions import Key

from fast_api_als import constants

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)0.8s] %(message)s",
)
logger = logging.getLogger(__name__)


class DBHelper:
    def __init__(self, session: boto3.session.Session):
        self.session = session
        self.ddb_resource = session.resource('dynamodb')
        self.table = self.ddb_resource.Table(constants.DB_TABLE_NAME)

    def insert_lead(self, lead_hash: str, lead_provider: str, response: str):
        logger.info(f"Inserting lead from {lead_provider} with response as {response}")
        item = {
            'pk': f'LEAD#{lead_hash}',
            'sk': lead_provider,
            'response': response
        }
        res = self.table.put_item(Item=item)
        verify_add_entry_response(res, f"{lead_provider}+'-'+{lead_hash}")

    def insert_oem_lead(self, uuid: str, oem: str, make: str, model: str, date: str, email: str, phone: str, last_name: str,
                        timestamp: str, make_model_filter_status: str):

        item = {
            'pk': f"{oem}#{uuid}",
            'sk': f"{make}#{model}" if make_model_filter_status else "",
            'gsipk': f"{oem}#{date}",
            'gsisk': "0#0",
            'make': make,
            'model': model,
            'email': email,
            'phone': phone,
            'last_name': last_name,
            'timestamp': timestamp,
            'conversion_status': "0",
            "make_model_filter_status": make_model_filter_status
        }

        response = self.table.put_item(Item=item)
        verify_add_entry_response(response, f"{oem}#{email}#{phone}#{last_name}")

    def check_duplicate_api_call(self, lead_hash: str, lead_provider: str):
        res = self.table.get_item(
            Key = {
                'pk': lead_hash,
                'sk': lead_provider
            }
        )
        item = res.get('Item')
        if not item:
            return False
        else:
            return True

    def accepted_lead_not_sent_for_oem(self, oem: str, date: str):
        res = self.table.query(
            IndexName='gsi-index',
            KeyConditionExpression=Key('gsipk').eq(f"{oem}#{date}")
                                   & Key('gsisk').begins_with("0#0")
        )
        return res.get('Items', [])

    def update_lead_conversion_status(self, uuid: str, oem: str, make: str, model: str ):
        res = self.table.get_item(
            Key={
                'pk': f"{uuid}#{oem}"
            }
        )
        item = res['Item']
        if not item:
            logger.info(f"No item found for {uuid}#{oem}#{make}#{model}")
            return False
        item['gsisk'] = item['gsisk'][0]+"#"+"1"
        res = self.table.put_item(Item=item)
        verify_add_entry_response(res, f"{uuid}#{oem}#{make}#{model}")
        return True

    def update_lead_sent_status(self, uuid: str, oem: str, make: str, model: str):
        res = self.table.get_item(
            Key={
                'pk': f"{uuid}#{oem}"
            }
        )
        item = res['Item']
        if not item:
            logger.info(f"No item found for {uuid}#{oem}#{make}#{model}")
            return False
        item['gsisk'] = "1#0"
        res = self.table.put_item(Item=item)
        verify_add_entry_response(res, f"{uuid}#{oem}#{make}#{model}")
        return True


def verify_add_entry_response(response, data):
    status_code = response['ResponseMetadata']['HTTPStatusCode']
    if not status_code == 200:
        logger.error(f"Failed to add {data} to the database.")
    else:
        logger.info("New entry added successfully.")