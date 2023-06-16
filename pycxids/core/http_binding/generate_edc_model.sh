#!/bin/bash

script=$(readlink -f "$0")

base=$(dirname $script )

# download from
# https://raw.githubusercontent.com/eclipse-edc/Connector/2ded962d1ae67184c83c3ab724852424f7292e7d/resources/openapi/openapi.yaml
input_file="$base/edc/edc_openapi_2023-05-26_changes.yaml"
output_file="$base/models_edc.py"

echo ""
echo "Generating model from input file: $input_file"
echo "................into output file: $output_file"
echo ""

# --use-subclass-enum: better enum support https://github.com/koxudaxi/datamodel-code-generator/issues/697#issuecomment-1366782351

datamodel-codegen \
    --base-class=pycxids.models.base_model.MyBaseModel \
    --collapse-root-models --snake-case-field \
    --use-subclass-enum \
    --input $input_file \
    --output $output_file

ls -ltr $output_file
