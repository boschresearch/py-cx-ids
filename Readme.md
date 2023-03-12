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

# CLI - command line interface
The cli uses the pycxids `core` module, meaning the one without EDC connection, but purely on the IDS protocol level.

## useful commands
```
# print the catalog
./cli.py catalog

# find all assets from a catalog
./cli.py catalog | ./cli.py assets

# fetch each asset from the catalog. Confirm each with 'y'
./cli.py catalog | ./cli.py assets | xargs --interactive -L 1 ./cli.py fetch

# fetch each asset from the catalog and save results in given output directory
./cli.py catalog | ./cli.py assets | xargs -L 1 ./cli.py fetch --out-dir ./my-out-dir
```

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