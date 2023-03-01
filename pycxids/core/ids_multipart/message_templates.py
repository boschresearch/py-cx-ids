# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

CONTRACT_REQUEST_MESSAGE = """
{
    "@type": "ids:ContractRequestMessage",
    "@id": "https://w3id.org/idsa/autogen/contractRequestMessage/$message_id",
    "ids:recipientAgent": [],
    "ids:securityToken": {
        "@type": "ids:DynamicAttributeToken",
        "@id": "https://w3id.org/idsa/autogen/dynamicAttributeToken/$security_token_id",
        "ids:tokenValue": "$daps_token",
        "ids:tokenFormat": {
            "@id": "https://w3id.org/idsa/code/JWT"
        }
    },
    "ids:transferContract": "$transfer_contract_id",
    "ids:modelVersion": "4.2.7",
    "ids:issuerConnector": "$connector_urn",
    "ids:recipientConnector": [
        "$recipient_connector"
    ],
    "ids:senderAgent": "$connector_urn",
    "idsWebhookAddress": "$webhook_url"
}
"""

# TODO: does the @id need to start with this?
# https://w3id.org/idsa/autogen/contractRequestMessage/XXX
DEFAULT_HEADER_MESSAGE = """
{
    "@type": "$msg_type",
    "@id": "$message_id",
    "ids:recipientAgent": [],
    "ids:securityToken": {
        "@type": "ids:DynamicAttributeToken",
        "@id": "https://w3id.org/idsa/autogen/dynamicAttributeToken/$security_token_id",
        "ids:tokenValue": "$daps_access_token",
        "ids:tokenFormat": {
            "@id": "https://w3id.org/idsa/code/JWT"
        }
    },
    "ids:transferContract": "$transfer_contract_id",
    "ids:modelVersion": "4.2.7",
    "ids:issuerConnector": "$connector_urn",
    "ids:recipientConnector": [
        "$recipient_connector"
    ],
    "ids:senderAgent": "$connector_urn",
    "idsWebhookAddress": "$webhook_url"
}
"""


CONTRACT_REQUEST = """
{
    "@type": "ids:ContractRequest",
    "@id": "urn:contractoffer:374d1428-5db6-49fe-b7a8-aa5ab41aea88:cfbc7ebf-bf62-49ff-9a3d-f793dceb5cf1",
    "ids:permission": [
        {
            "@type": "ids:Permission",
            "@id": "urn:permission:1779456186",
            "ids:target": "urn:artifact:urn:uuid:3720dd4a-3213-40cb-a8f2-9df4d428076e-urn:uuid:9a970543-f662-45ff-b012-60b7769e5ed3",
            "ids:description": [],
            "ids:title": [],
            "ids:assignee": [],
            "ids:assigner": [],
            "ids:action": [
                {
                    "@id": "https://w3id.org/idsa/code/USE"
                }
            ],
            "ids:constraint": [],
            "ids:postDuty": [],
            "ids:preDuty": []
        }
    ],
    "ids:provider": "urn:connector:provider",
    "ids:consumer": "urn:connector:consumer",
    "ids:obligation": [],
    "ids:prohibition": []
}
"""