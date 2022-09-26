import logging
import sys
import os
import json
import tempfile
import argparse
import ssl
import boto3
from helper import FileHelper, SpfHelper, S3Helper
from app import process_flattening

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
        logger.info('To Slack: ' + str(to_slack))

    slack_webhook = args.slack_webhook
    if slack_webhook:
        to_slack = True
        logger.info('Slack Webhook: ' + slack_webhook)

    update_records = args.update
    if update_records:
        logger.info('Update Records: ' + str(update_records))

    ssl._create_default_https_context = ssl._create_unverified_context

    BUCKET = args.bucket
    logger.info('Bucket: ' + BUCKET)

    RESULTS_FOLDER = args.output
    logger.info('Output: ' + RESULTS_FOLDER)

    process_flattening(BUCKET, slack_webhook=slack_webhook, update=update_records, force=force_mode)

    return 0


if __name__ == "__main__":
    if not os.path.exists(RESULTS_FOLDER):
        os.makedirs(RESULTS_FOLDER)

    sys.exit(main())
