# I40 PCF Demo case

This is a demo to set an EDC in front of the 'Plattform Industrie 4.0' PCF Demo case.

The system reads the AAS Registry, filters for `https://zvei.org/demo/ProductCarbonFootprint/1/0`
and calculates the `sha256` of the submodels' `endpointAddress` and uses this value as the
EDC `asset:prop:id`. The `inity.py` does the EDC asset creation.

Afterwards, the typical EDC / IDS flow can be used to query that information via EDC.

The `test_pcf_create_and_fetch.py` does both. Creating the assets on a Provider EDC and afterwards
reading those via a Consumer EDC. It uses the `api-wrapper` and passes a `token` query param that
contains a DAPS token requested from a running `daps_token_service`.

```
pytest test_pcf_create_and_fetch.py

```
