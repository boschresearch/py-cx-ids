# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from pyld import jsonld

default_context = {
    'dct': 'https://purl.org/dc/terms/',
    'tx': 'https://w3id.org/tractusx/v0.0.1/ns/',
    'edc': 'https://w3id.org/edc/v0.0.1/ns/',
    'dcat': 'https://www.w3.org/ns/dcat/',
    'odrl': 'http://www.w3.org/ns/odrl/2/',
    'dspace': 'https://w3id.org/dspace/v0.8/',
}

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
