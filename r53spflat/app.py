import os
import json
import logging
import tempfile
import boto3
from helper import FileHelper, SpfHelper

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LambdaException(Exception):
    pass


RESULTS_FOLDER = tempfile.gettempdir() + '/r53spflat'


def lambda_handler(event, context):
    global RESULTS_FOLDER

    slack_webhook = os.environ['SLACK_WEBHOOK_URL']
    bucket = os.environ['BUCKET_NAME']

    spf_helper = SpfHelper(slack_webhook=slack_webhook)
    s3_client = boto3.client('s3')

    result = s3_client.list_objects_v2(Bucket=bucket, Prefix=SpfHelper.SPF_CONFIGS_FOLDER + '/')
    files = result.get('Contents')
    for file in files:
        file_key = file['Key']
        file_size = file['Size']
        basename = os.path.basename(file_key)
        filename, ext = os.path.splitext(basename)
        if ext == '.json':
            previous_path = os.path.join(RESULTS_FOLDER, filename + '_results.json')
            if os.path.exists(previous_path):
                with open(previous_path) as prev_hashes:
                    previous_result = json.load(prev_hashes)

            data = s3_client.get_object(Bucket=bucket, Key=file_key)
            json_str = data['Body'].read().decode('utf-8')
            settings = json.loads(json_str)

            resolvers = settings.get("resolvers", [])
            domains = settings.get("sending_domains", [])

            spf = spf_helper.flatten(
                input_records=domains,
                lastresult=previous_result,
                dns_servers=resolvers,
                update=True,
                force_update=False,
                slack=True
            )

            with open(previous_path, "w+") as f:
                json.dump(spf, f, indent=4, sort_keys=True)
