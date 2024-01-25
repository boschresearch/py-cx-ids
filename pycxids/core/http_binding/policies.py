# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4
from pycxids.core.http_binding.models import OdrlOffer, OdrlPolicy, OdrlPermission, OdrlOperand, OdrlConstraint, OdrlOperand


default_policy = OdrlPolicy(
    # workaround for EDC issue https://github.com/eclipse-edc/Connector/issues/3240
    field_id = f"{str(uuid4())}:{str(uuid4())}:{str(uuid4())}",
    odrl_permission=[
        OdrlPermission(
            # action={
            #     'odrl:type':'USE'
            # },
            odrl_action='USE',
            odrl_target='default', # TODO: provide this as a param... Overwrite when using the default policy!!!
            odrl_constraint=OdrlConstraint(
                odrl_leftOperand=OdrlOperand(value='idsc:PURPOSE'),
                odrl_rightOperand=OdrlOperand(value='R2_Traceability'),
                odrl_operator='EQ'
            )
        )
    ]
)

default_offer_policy = OdrlOffer.parse_obj(default_policy.dict())
