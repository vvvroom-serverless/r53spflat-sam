#!make
include .env.local
export
current_dir = $(shell pwd)
base_dir = $(shell basename "$(current_dir)")

sync-config-up:
	aws s3 sync ./r53spflat/configs s3://$(BUCKET)/r53spflat --exclude "*" --include "*.json" --profile $(AWS_PROFILE)

sync-config-down:
	aws s3 sync s3://$(BUCKET)/r53spflat ./r53spflat/configs --exclude "*" --include "*.json" --profile $(AWS_PROFILE)

test-cli:
	AWS_PROFILE=$(AWS_PROFILE); ./venv/bin/python r53spflat/cli.py --bucket $(BUCKET) --slack-webhook $(WEBHOOK_URL) --update

build-local:
	sam build --use-container --container-env-var-file env-vars.local.json --profile $(AWS_PROFILE)

test-local:
	sam local invoke "R53SpflatProcessFunction" --debug --env-vars env-vars.local.json --profile $(AWS_PROFILE)
