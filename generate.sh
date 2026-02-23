#!/bin/bash

COMMON_CONFIG="./assets/common_config.ini"

declare -a GALLERY_CONFIGS=(
    "config/main/test.ini"
    "config/main/test2.ini"
)

for config in "${GALLERY_CONFIGS[@]}"; do
    python3 ./gallery_generator.py $COMMON_CONFIG $config
done
