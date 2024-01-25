#!/bin/bash

script=$(readlink -f "$0")

base=$(dirname $script )

input_file="$base/http_binding_openapi.yaml"
output_file="$base/models.py"

echo ""
echo "Generating model from input file: $input_file"
echo "................into output file: $output_file"
echo ""

# pip install datamodel-code-generator
# --use-subclass-enum: better enum support https://github.com/koxudaxi/datamodel-code-generator/issues/697#issuecomment-1366782351

datamodel-codegen \
    --base-class=pycxids.models.base_model.MyBaseModel \
    --collapse-root-models --snake-case-field \
    --use-subclass-enum \
    --input $input_file \
    --output $output_file

ls -ltr $output_file
