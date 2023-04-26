# Generate from openapi specs

```
pip install datamodel-code-generator

datamodel-codegen --base-class=pycxids.models.base_model.MyBaseModel --collapse-root-models --snake-case-field --input aas-registry-openapi.yaml --output pycxids/models/generated/registry.py
```

## CX
Openapi Specs for CX can be found, e.g. here:
https://github.com/eclipse-tractusx/sldt-semantic-models/blob/main/io.catenax.assembly_part_relationship/1.1.1/gen/AssemblyPartRelationship.yml

Remove some of the generated prefixes, e.g.
`urn_bamm_io.openmanufacturing_characteristic_2.0.0_` and `urn_bamm_io.catenax.assembly_part_relationship_1.1.1_` to get proper output in a single file.

datamodel-codegen --base-class=pycxids.models.base_model.MyBaseModel --collapse-root-models --snake-case-field --output pycxids/models/generated/assembly_part_relationship.py --input pycxids/models/assemblypartrelationship_1.1.1.yaml

## Swagger / Openapi Editor
```
docker run -d -p 5000:8080 swaggerapi/swagger-editor
```
