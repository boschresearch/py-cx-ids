# Generate from AAS openapi spec

```
pip install datamodel-code-generator

datamodel-codegen --base-class=pycxids.models.base_model.MyBaseModel --collapse-root-models --snake-case-field --input aas-registry-openapi.yaml --output pycxids/models/generated/registry.py
```