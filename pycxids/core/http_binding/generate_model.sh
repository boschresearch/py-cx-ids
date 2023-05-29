#!/bin/bash

script=$(readlink -f "$0")

base=$(dirname $script )

input_file="$base/http_binding_openapi.yaml"
output_file="$base/models.py"

echo ""
echo "Generating model from input file: $input_file"
echo "................into output file: $output_file"
echo ""

datamodel-codegen \
    --base-class=pycxids.models.base_model.MyBaseModel \
    --collapse-root-models --snake-case-field \
    --input $input_file \
    --output $output_file

ls -ltr $output_file
