Route53 SPF Flattener Lambda
============================

## Make .env variables
Fill out local variables when using Make commands.
```
cp .env .env.local
```

## CLI Usage (Lambda uses Python 3.9)
### Install Older Python 3.9 (Debian) (Optional)
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.9
sudo apt install python3.9-distutils
```

### Create venv For Project
```bash
virtualenv venv --python="/usr/bin/python3.9"
source ./venv/bin/activate
pip install -r r53spflat/requirements-cli.txt

# analyse a pdf for testing
python r53spflat/cli.py /tmp/champ/test.pdf --bucket $(BUCKET) --supplier $(SUPPLIER)

# full cli command for when you're outside of the venv and using --force to not reuse cached results
AWS_PROFILE=$(AWS_PROFILE); ./venv/bin/python r53spflat/cli.py --bucket $(BUCKET) --slack-webhook $(WEBHOOK_URL)  
```

## Init SSM Values
```
aws ssm put-parameter --name "/Test/r53spflat/BUCKET_NAME" --type "String" --value "xxxxxxxx"
aws ssm put-parameter --name "/Test/r53spflat/SLACK_WEBHOOK_URL" --type "String" --value "https://hooks.slack.com/services/XXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```
