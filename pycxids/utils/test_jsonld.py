# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
import pytest
from unittest.mock import Mock, patch
from pyld import jsonld
import pycxids.utils.jsonld as myjsonld
from pycxids.utils.jsonld_contexts import dsp_context

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
    """
    Reference: https://github.com/International-Data-Spaces-Association/ids-specification/issues/132
    """
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

def test_array_object():
    """
    Reference: https://github.com/International-Data-Spaces-Association/ids-specification/issues/125
    """
    doc1 = {
        'dspace:policy': [
            {
                '@id': '1'
            }
        ]
    }
    doc2 = {
        'dspace:policy': {
                '@id': '1'
            }
    }
    
    co1 = myjsonld.compact(doc1, context=context_myprefix)
    print(json.dumps(co1, indent=4))
    assert isinstance(co1.get('myprefix:policy'), list), "We always want a list here"

    co2 = myjsonld.compact(doc2, context=context_myprefix)
    print(json.dumps(co2, indent=4))
    assert isinstance(co2.get('myprefix:policy'), list), "We always want a list here"

    # and just for fun, test it with the default_context
    co1 = myjsonld.compact(doc1)
    print(json.dumps(co1, indent=4))
    assert isinstance(co1.get('dspace:policy'), list), "Should be prefixed with the default_context dspace"


def requests_get_mock(*args, **kwargs):
    print(args)
    print(kwargs)
    context = json.dumps(dsp_context, indent=4).encode()
    return context

def document_loader(url, optioons):
    doc = {
        'contentType': None,
        'contextUrl': None,
        'documentUrl': url,
        'document': dsp_context
    }

    return doc

@patch('requests.get', Mock(side_effect=requests_get_mock))
def test_policy_references():
    fn = './pycxids/core/http_binding/examples/catalog_dsp_spec_example_modified_with_policy_references.json'
    #fn = './pycxids/core/http_binding/examples/catalog_dsp_spec_example.json'
    catalog_text = ''
    with open(fn, 'rt') as f:
        catalog_text = f.read()
    doc = json.loads(catalog_text)

    jsonld.set_document_loader(document_loader)
    co = jsonld.compact(doc, ctx=context, options={'expandContext': dsp_context})
    print(json.dumps(co, indent=4))



if __name__ == '__main__':
    pytest.main([__file__, "-s", "-k", "test_policy_references"])
