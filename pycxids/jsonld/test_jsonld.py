# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
import pytest
from pyld import jsonld

context = {
    "dspace": "https://w3id.org/dspace/v0.8/",
    "dspace:timestamp": {
       "@type": "xsd:dateTime"
    }
  }
context_myprefix = {
    "myprefix": "https://w3id.org/dspace/v0.8/",
    "myprefix:timestamp": {
       "@type": "xsd:dateTime"
    }
  }


def test_dsp_timestamps():
    doc1 = {
        "@context": context,
        "dspace:timestamp" : "2023-01-01T01:00:00Z"
    }
    doc2 = {
        "@context": context,
        "dspace:timestamp" : {
            "@type": "xsd:dateTime",
            "@value": "2023-01-01T01:00:00Z"
        }
    }
    doc3 = {
        "dspace:timestamp" : "2023-01-01T01:00:00Z"
    }

    # first expand docs with its existing context
    expanded1 = jsonld.expand(doc1)
    print(json.dumps(expanded1, indent=4))
    expanded2 = jsonld.expand(doc2)
    print(json.dumps(expanded2, indent=4))
    # now compact the result again
    exp_compacted1 = jsonld.compact(expanded1, ctx=context_myprefix)
    print(json.dumps(exp_compacted1, indent=4))
    #exp_compacted1['myprefix:timestamp'] = {}
    assert isinstance(exp_compacted1.get('myprefix:timestamp'), str)
    exp_compacted2 = jsonld.compact(expanded2, ctx=context_myprefix)
    print(json.dumps(exp_compacted2, indent=4))
    assert isinstance(exp_compacted2.get('myprefix:timestamp'), str)

    # payload / doc without context
    co_3_wrong = jsonld.compact(doc3, ctx=context_myprefix)
    print(json.dumps(co_3_wrong, indent=4))
    assert isinstance(co_3_wrong.get('dspace:timestamp'), str), "dspace prefix must be there, but doesn't help us"

    co_3_correct = jsonld.compact(doc3, ctx=context_myprefix, options={'expandContext': context})
    print(json.dumps(co_3_correct, indent=4))
    assert isinstance(co_3_correct.get('myprefix:timestamp'), str), "The correct prefix myprefix is not there!"



if __name__ == '__main__':
    pytest.main([__file__, "-s"])
