# Introduction

# Project structure
## edc-dev-env
A easy developpment environment that spawns up a Consumer and Provider EDC with official 'product-edc' images.

## pycxids
### edc
To call EDC data management endpoints
### registry
To call AAS Registry
### models
Contains generated models from openapi specs or self defined models.
### core
Some core components to e.g. get a DAPS token or negotiate (without the EDC), but purely on an IDS protocol level.

# Development
## Test execution examples
Various ways to run the tests

```
# with pytest (which reads pytest.ini)
pytest tests/test_assets.py

# from file - with PYTHONPATH set
PYTHONPATH=./ python tests/test_assets.py

# as a module
python -m pytest tests/test_assets.py
python -m pytest pycxids/demo/assetstructure/test_with_registry.py

```