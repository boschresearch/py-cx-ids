
```
datamodel-codegen --base-class=pycxids.models.base_model.MyBaseModel --collapse-root-models --snake-case-field --output pycxids/core/http_binding/models.py --input pycxids/core/http_binding/http_binding_openapi.yaml
```

# Implementation specific questions
- Do callbacks need to work or not in case the callback comes BEFORE the requesting call response?

# Libraries
- jwcrypto
    For generating encrypted JWT (JWE) on the Provider side
    https://jwcrypto.readthedocs.io/en/latest/jwe.html#asymmetric-keys

# EDC questions
- dataset id is different on every request. It is randomly generated!
- edc.dsp.callback.address used for callbacks, but not documented

# notes

SsiHttpConsumerPullWithProxyInMemoryTest
./gradlew compileJava compileTestJava
you may also want to look at KeycloakDispatcher and MiwDispatcher
