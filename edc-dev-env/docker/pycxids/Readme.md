Dummy container with installed `pycxids` package

```
docker-compose -f docker-compose-helpers.yaml run pycxids /bin/bash

# inside the container, e.g.

python3 /usr/local/lib/python3.11/site-packages/pycxids/demo/i40pcf/test_pcf_create_and_fetch.py


```