# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from pycxids.core.http_binding.crypto_utils import decrypt

def test_encyption():
    secret = ''
    with open('./.secrets/demo_decrypt.key', 'rt') as f:
        secret = f.read()
    demo_encypted='7/Pwc4vgvj1zuMzbqUn890rYaDPa6Gt9d1YXKg4Z0uUC7EZe1Kl/utE0q6+75cYos7pBSAUN5NNuiX2gG7GzU0R8UcvjcHlXh5s3KKSjEeeVlPW0kBxl6NfsaHFHRbWG84xu42KazoHnjfdErqEM7C9IlyJTawmnDt+2n3ej8EddJTJeWImMigoR+7vJQk4Gc3ytdxlKp7JUEA/QgGBscLbvW4BtkUUnhZxIUFfCAIZxP1S5NTs0L8EqzoMRzifL818bR1+vAgOo/EJ+C2lx1tpdz0QCta4UAlfyqOXYLimFFz57UR4cnvMeSKyMJmua/r5r/FM0HhdPV2oDnNUf7FTR49/AObS7LHzQLeCISjHjIgfRgITJx5/cZlCSe5j7MvNh/XsdvrPfUt8aM+AcB/H/TZmWB+S3vMpnnXUGKGT+JkcL+afYfFVQ1OGrlH50ZVJ2hVmX6LGufR2tnCJt4AktUernA+jQIQ=='
    decrypt(b64_cipher=demo_encypted, b64_key=secret)

if __name__ == '__main__':
    pytest.main([__file__, "-s"])
