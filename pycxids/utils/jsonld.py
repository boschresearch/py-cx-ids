# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import json
from pyld import jsonld
from hashlib import sha256
import base64

DEFAULT_DSP_REMOTE_CONTEXT_V_0_8 = "https://w3id.org/dspace/v0.8/context.json"
DEFAULT_DSP_REMOTE_CONTEXT = DEFAULT_DSP_REMOTE_CONTEXT_V_0_8

default_context = [
    DEFAULT_DSP_REMOTE_CONTEXT,
    {
        'tx': 'https://w3id.org/tractusx/v0.0.1/ns/'
    },
    {
        'edc': 'https://w3id.org/edc/v0.0.1/ns/'
    },
    {
        'cx-policy': 'https://w3id.org/catenax/policy/'
    }
]

normalize_default_options = {'algorithm': 'URDNA2015', 'format': 'application/nquads'}

def normalize(jsonld_document, options = normalize_default_options):
    return jsonld.normalize(jsonld_document, options=options)

def normalize_json(jsonld_document, options = normalize_default_options):
    normalized = normalize(jsonld_document=jsonld_document, options=options)
    # no whitespaces with separators and sorted keys
    serialized_json = json.dumps(normalized, separators=(',', ':'), sort_keys=True)
    return serialized_json.encode('utf-8')

def hash(normalized_doc: str):
    hash1 =  sha256(normalized_doc.encode('utf-8')).digest()
    #hash2 = sha256(normalized_doc.encode('utf-8')).hexdigest()
    return hash1

def expand(doc, context = None):
    return jsonld.expand(doc)

def compact(doc, context = None, expand_context = None):
    """
    Contains also workaround for:
    https://github.com/digitalbazaar/pyld/issues/61

    context: if not given, use default_context
    expand_context: if not given, use default_context
    """
    if not context:
        context = default_context
    if not expand_context:
        expand_context = default_context
    co = jsonld.compact(doc, ctx=context, options={'expandContext': expand_context, 'compactArrays' : False, 'graph': False})
    result = co.get('@graph')[0]
    result['@context'] = co.get('@context')
    return result

# pyld https://github.com/digitalbazaar/pyld/issues/61
# if not options['graph']:
#     # isn't 'compacted' always an array here? with this assumption, we change it
#     # here as  a workaround to work with existing code
#     # https://github.com/digitalbazaar/pyld/issues/61
#     if _is_array(compacted) and len(compacted) == 1:
#         compacted = compacted[0]
