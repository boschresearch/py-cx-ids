# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

# taken from the specification
# https://github.com/International-Data-Spaces-Association/ids-specification/blob/df8095a6a102d0f4de4e86c1bc48f4397bd52036/common/schema/context.json
dsp_context = {
  "@context": {
    "odrl": "http://www.w3.org/ns/odrl/2/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "cred": "https://www.w3.org/2018/credentials#",
    "sec": "https://w3id.org/security#",
    "dct": "http://purl.org/dc/terms/",
    "dcat": "http://www.w3.org/ns/dcat#",
    "dspace": "https://w3id.org/dspace/v0.8/",
    "dct:title": { "@language": "en" },
    "dspace:timestamp": { "@type": "xsd:dateTime" },
    "dct:issued": { "@type": "xsd:dateTime" },
    "dct:modified": { "@type": "xsd:dateTime" },
    "dct:created": { "@type": "xsd:dateTime" },
    "dcat:byteSize": { "@type": "xsd:decimal" },
    "dcat:endpointURL": { "@type": "xsd:anyURI" },
    "dspace:agreementId": { "@type": "@id" },
    "dspace:dataset": { "@type": "@id" },
    "dspace:transportType": { "@type": "@id" },
    "dspace:state": { "@type": "@id" },
    "dct:publisher": { "@type": "@id" },
    "dct:format": { "@type": "@id" },
    "dct:type": { "@type": "@id" },
    "odrl:assigner": { "@type": "@id" },
    "odrl:assignee": { "@type": "@id" },
    "odrl:action": { "@type": "@id" },
    "odrl:target": { "@type": "@id" },
    "odrl:leftOperand": { "@type": "@id" },
    "odrl:operator": { "@type": "@id" },
    "odrl:rightOperandReference": { "@type": "@id" },
    "odrl:profile": { "@type": "@id" },
    "dspace:reason": { "@container": "@set" },
    "dspace:catalog": { "@container": "@set" },
    "dspace:filter": { "@container": "@set" },
    "dct:description": { "@container": "@set" },
    "dcat:keyword": { "@container": "@set" },
    "dcat:service": { "@container": "@set" },
    "dcat:dataset": { "@container": "@set" },
    "odrl:hasPolicy": {
        # "@type": "@id",
        "@container": "@index"
    },
    "odrl:permission": { "@container": "@set" },
    "odrl:prohibition": { "@container": "@set" },
    "odrl:duty": { "@container": "@set" },
    "odrl:constraint": { "@container": "@set" }
  }
}
