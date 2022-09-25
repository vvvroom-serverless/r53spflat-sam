import logging
import sys
import os
import json
import tempfile
import argparse
import ssl
import boto3
from helper import FileHelper, SpfHelper

logger = logging.getLogger()
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler(sys.stdout)
logger.addHandler(streamHandler)

BUCKET = ''
RESULTS_FOLDER = tempfile.gettempdir() + '/r53spflat'


def main() -> int:
    global BUCKET
    global RESULTS_FOLDER

    parser = argparse.ArgumentParser(description='Flatten SPF Records')
    parser.add_argument('--force', help='Force process', default=False, action='store_true')
    parser.add_argument('--slack', help='Send to slack', default=False, action='store_true')
    parser.add_argument('--update', help='Update SPF records in Route53', default=False, action='store_true')
    parser.add_argument('--bucket', type=str, help='Bucket name', default=BUCKET)
    parser.add_argument('--slack-webhook', type=str, help='Slack webhook')
    parser.add_argument('--output', type=str, help='Output folder', default=RESULTS_FOLDER)

    args = parser.parse_args()

    force_mode = args.force
    if force_mode:
        logger.info('Force Mode: ' + str(force_mode))

    to_slack = args.slack
    if to_slack:
        logger.info('To Slack: ' + str(logger))

    slack_webhook = args.slack_webhook
    if slack_webhook:
        logger.info('Slack Webhook: ' + slack_webhook)

    update_records = args.update
    if update_records:
        logger.info('Update Records: ' + str(update_records))

    ssl._create_default_https_context = ssl._create_unverified_context

    BUCKET = args.bucket
    logger.info('Bucket: ' + BUCKET)

    RESULTS_FOLDER = args.output
    logger.info('Output: ' + RESULTS_FOLDER)

    spf_helper = SpfHelper(slack_webhook=slack_webhook)
    s3_client = boto3.client('s3')

    result = s3_client.list_objects_v2(Bucket=BUCKET, Prefix=SpfHelper.SPF_CONFIGS_FOLDER + '/')
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

            data = s3_client.get_object(Bucket=BUCKET, Key=file_key)
            json_str = data['Body'].read().decode('utf-8')
            settings = json.loads(json_str)

            resolvers = settings.get("resolvers", [])
            domains = settings.get("sending_domains", [])

            spf = spf_helper.flatten(
                input_records=domains,
                lastresult=previous_result,
                dns_servers=resolvers,
                update=update_records,
                force_update=force_mode,
                slack=to_slack
            )

            with open(previous_path, "w+") as f:
                json.dump(spf, f, indent=4, sort_keys=True)

    return 0


if __name__ == "__main__":
    if not os.path.exists(RESULTS_FOLDER):
        os.makedirs(RESULTS_FOLDER)

    sys.exit(main())
