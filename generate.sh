#!/bin/bash

COMMON_CONFIG="./assets/common_config.ini"

declare -a GALLERY_CONFIGS=(
    "config/Projects/hfvttc1.ini"
    "config/Biography/Biography.ini"
)

for config in "${GALLERY_CONFIGS[@]}"; do
    python3 ./gallery_generator.py $COMMON_CONFIG $config
done
