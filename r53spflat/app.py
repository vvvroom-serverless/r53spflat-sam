import os
import json
import logging
import tempfile
import boto3
from helper import FileHelper, SpfHelper, S3Helper

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LambdaException(Exception):
    pass


RESULTS_FOLDER = tempfile.gettempdir() + '/r53spflat'


def process_flattening(bucket, slack_webhook=None, update=True, force=False):
    spf_helper = SpfHelper(slack_webhook=slack_webhook)
    s3_client = boto3.client('s3')
    to_slack = False
    if slack_webhook:
        to_slack = True

    result = s3_client.list_objects_v2(Bucket=bucket,
                                       Prefix=SpfHelper.SPF_CONFIGS_FOLDER + '/' + SpfHelper.SPF_FILE_PREFIX)
    files = result.get('Contents')
    for file in files:
        file_key = file['Key']
        file_size = file['Size']
        basename = os.path.basename(file_key)
        filename, ext = os.path.splitext(basename)
        domain = filename.replace(SpfHelper.SPF_FILE_PREFIX, '')
        if ext == '.json':
            logger.info('Processing domain: ' + domain)

            previous_key = os.path.join(SpfHelper.SPF_CONFIGS_FOLDER, SpfHelper.MONITOR_SUMS_PREFIX + domain + '.json')
            previous_result = None
            previous_content = S3Helper.get_contents(bucket, previous_key)
            if previous_content:
                previous_result = json.loads(previous_content)

            json_str = S3Helper.get_contents(bucket, file_key)
            settings = json.loads(json_str)

            resolvers = settings.get("resolvers", [])
            domains = settings.get("sending_domains", [])

            spf = spf_helper.flatten(
                input_records=domains,
                last_result=previous_result,
                dns_servers=resolvers,
                update=update,
                force_update=force,
                slack=to_slack
            )

            spf_json_str = json.dumps(spf, indent=4, sort_keys=True)
            if not S3Helper.set_contents(bucket, previous_key, spf_json_str):
                logger.error('Failed to save monitor sums for domain {}'.format(domain))


def lambda_handler(event, context):
    global RESULTS_FOLDER

    if not os.path.exists(RESULTS_FOLDER):
        os.makedirs(RESULTS_FOLDER)

    slack_webhook = os.environ['SLACK_WEBHOOK_URL']
    bucket = os.environ['BUCKET_NAME']

    logger.info('Bucket: ' + bucket)

    process_flattening(bucket, slack_webhook=slack_webhook, update=True)
