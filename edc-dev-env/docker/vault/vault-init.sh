#!/bin/bash

# enable job control (bg, fg)
set -m

# start vault
docker-entrypoint.sh server -dev &

export VAULT_ADDR="http://localhost:8200"

# try to login until it works
until vault login $VAULT_DEV_ROOT_TOKEN_ID
do
    echo 'Could not login to vault yet. Waiting...'
    sleep 1
done

# to be really sure, we'll wait another second
sleep 1

# add our secrets
vault kv put secret/hello-world hello=world

# add initial data
# filename is used as the key
# file content is used as the value
for filename in $VAULT_INITIAL_DATA_DIR/*;
do
    echo $filename
    bn=`basename $filename`
    echo "basename: $bn"
    cat $filename | vault kv put secret/$bn content=-
done

# output jobs, just for debugging if the background process stopped working...
jobs

# and get the actual server process back to the foreground
fg %1
