import boto3
import botocore.exceptions
from botocore.client import Config
import os
import csv
import logging
import hashlib
import json
import tempfile
import email
import os
from pathlib import Path
from dns.resolver import Resolver
from sender_policy_flattener.crawler import spf2ips
from sender_policy_flattener.formatting import sequence_hash
from sender_policy_flattener.email_utils import email_changes
from r53_dns import TXTrec
from slack_sdk.webhook import WebhookClient
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class S3Helper:
    @staticmethod
    def get_contents(bucket, key):
        s3_client = boto3.client('s3')

        contents = None

        try:
            data = s3_client.get_object(Bucket=bucket, Key=key)
            contents = data['Body'].read().decode('utf-8')
        except ClientError:
            pass

        return contents

    @staticmethod
    def set_contents(bucket, key, contents):
        s3_client = boto3.client('s3')

        try:
            s3_client.put_object(Body=contents, Bucket=bucket, Key=key)
        except ClientError:
            return False

        return True


class FileHelper:
    @staticmethod
    def get_contents(file_path):
        contents = None

        if not os.path.exists(file_path):
            return None

        with open(file_path, 'r') as f:
            contents = f.read()

        return contents


class SpfHelper:
    SPF_CONFIGS_FOLDER = 'r53spflat'
    CONFIGS_FOLDER = 'configs'
    SPF_FILE_PREFIX = 'spfs-'
    MONITOR_SUMS_PREFIX = 'monitor_sums-'

    def __init__(self, slack_webhook):
        self.slack_webhook = slack_webhook

    def get_config_files(self):
        files = []
        configs_path = Path(__file__).parent.__str__() + '/' + self.CONFIGS_FOLDER
        if not os.path.exists(configs_path):
            return []

        for file in os.listdir(configs_path):
            if file.endswith('.json'):
                files.append(os.path.join(configs_path, file))

        return files

    def log_and_slack(self, message):
        webhook = WebhookClient(self.slack_webhook)
        logger.info(message)
        webhook.send(text=message)

    def flatten(
            self,
            input_records,
            dns_servers,
            update=False,
            last_result=None,
            force_update=False,
            slack=False
    ):
        resolver = Resolver()
        if dns_servers:
            resolver.nameservers = dns_servers

        if last_result is None:
            last_result = dict()

        current = dict()
        for domain, spf_targets in input_records.items():
            records = spf2ips(spf_targets, domain, resolver)
            hashsum = sequence_hash(records)
            current[domain] = {"sum": hashsum, "records": records}
            if last_result.get(domain, False) and current.get(domain, False):
                previous_sum = last_result[domain]["sum"]
                current_sum = current[domain]["sum"]
                mismatch = previous_sum != current_sum
                if mismatch:
                    logging.info(f'***WARNING: SPF changes detected for sender domain {domain}')
                else:
                    logging.info(f'NO SPF changes detected for sender domain {domain}')

                if mismatch and slack:
                    logging.info('Sending mis-match details to slack')
                    if update or force_update:
                        the_subject = f'[WARNING] SPF Records for {domain} have changed and should be updated.'
                    else:
                        the_subject = f'[NOTICE] SPF Records for {domain} have been updated.'

                    self.log_and_slack(the_subject)

                if (mismatch and update) or force_update:
                    r53zone = TXTrec(domain)
                    numrecs = len(records)

                    self.log_and_slack(f'**** Updating {numrecs} SPF Records for domain {domain}')
                    for i in range(0, numrecs):
                        recname = f'spf{i}.{domain}'
                        self.log_and_slack(f'===> Updating {recname} TXT record..')
                        if r53zone.update(recname, records[i], addok=True):
                            self.log_and_slack(f'..Successfully updated')
                        else:
                            self.log_and_slack(f'Failed!\n\n********** WARNING: Update of {recname} TXT record Failed')

        return current if update or force_update or len(last_result) == 0 else last_result
