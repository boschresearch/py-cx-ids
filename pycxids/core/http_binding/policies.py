# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from pycxids.core.http_binding.models import OdrlPolicy, OdrlRule, OdrlOperand, OdrlConstraint, OdrlOperand


default_policy = OdrlPolicy(
    field_id = 'default_policy',
    permission=[
        OdrlRule(
            action='USE',
            constraint=OdrlConstraint(
                leftOperand=OdrlOperand(value='idsc:PURPOSE'),
                rightOperand=OdrlOperand(value='R2_Traceability'),
                operator='EQ'
            )
        )
    ]
)
