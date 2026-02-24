#!/bin/bash

COMMON_CONFIG="./assets/common_config.ini"

declare -a GALLERY_CONFIGS=(
    "config/Projects/test.ini"
    "config/Biography/biography.ini"
)

for config in "${GALLERY_CONFIGS[@]}"; do
    python3 ./gallery_generator.py $COMMON_CONFIG $config
done
