#! /bin/bash

# provider read credentials
export AWS_ACCESS_KEY_ID=`cat ./edc-dev-env/vault_secrets/matthias-test-user-provider_access_key`
export AWS_SECRET_ACCESS_KEY=`cat ./edc-dev-env/vault_secrets/matthias-test-user-provider_secret_access_key`
BUCKET=matthias-test-provider

# consumer
#export AWS_ACCESS_KEY_ID=`cat ./edc-dev-env/vault_secrets/matthias-test-user1_access_key`
#export AWS_SECRET_ACCESS_KEY=`cat ./edc-dev-env/vault_secrets/matthias-test-user1_secret_access_key`
#BUCKET=matthias-test-consumer

#echo $AWS_ACCESS_KEY_ID
#echo $AWS_SECRET_ACCESS_KEY
#echo $BUCKET

# aws --version
aws s3 cp s3://$BUCKET/$1 tmp.blob
cat tmp.blob
