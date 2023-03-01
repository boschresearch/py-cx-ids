# I40 PCF Demo case

This is a demo to set an EDC in front of the 'Plattform Industrie 4.0' PCF Demo case.

The system reads the AAS Registry, filters for `https://zvei.org/demo/ProductCarbonFootprint/1/0`
and calculates the `sha256` of the submodels' `endpointAddress` and uses this value as the
EDC `asset:prop:id`. The `inity.py` does the EDC asset creation.

The second part of the `init.py` creates EDC assets only for the server name, e.g. 'http://localhost:8080'.

Afterwards, the typical EDC / IDS flow can be used to query that information via EDC.

The `test_fetch_single_endpoint.py` fetches the data via individually created submodel endpoint EDC assets, whereas `test_fetch_via_server_name_assets.py` fetches only via the EDC assets created for the server names and just appends the path. The second is much faster, because not for every endpoint a negotiation process must be started.

The scripts use the api-wrapper to fetch the data.

```
pytest test_fetch_single_endpoint.py
pytest test_fetch_via_server_name_assets.py

```
