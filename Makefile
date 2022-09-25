#!make
include .env.local
export
current_dir = $(shell pwd)
base_dir = $(shell basename "$(current_dir)")

sync-config:
	aws s3 sync ./r53spflat/configs s3://$(BUCKET)/spf_configs --exclude "*" --include "*.json" --profile $(AWS_PROFILE)

test-cli:
	AWS_PROFILE=$(AWS_PROFILE); ./venv/bin/python r53spflat/cli.py --bucket $(BUCKET) --slack-webhook $(WEBHOOK_URL)

build-local:
	sam build --use-container --container-env-var-file env-vars.local.json --profile $(AWS_PROFILE)

test-local:
	sam local invoke "R53SpflatProcessFunction" --debug --env-vars env-vars.local.json --profile $(AWS_PROFILE)
