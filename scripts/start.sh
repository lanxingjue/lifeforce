#!/bin/bash
# Lifeforce 启动脚本

set -e

echo "Starting Lifeforce..."

if [ -z "$APIYI_API_KEY" ]; then
    echo "Error: APIYI_API_KEY not set"
    echo "Please run: export APIYI_API_KEY='your_key'"
    exit 1
fi

if [ ! -f "config.yaml" ]; then
    echo "Initializing Lifeforce..."
    py -m lifeforce.cli.main init
fi

echo "Lifeforce is ready"
echo "Try:"
echo "  py -m lifeforce.cli.main chat 'hello'"
echo "  py -m lifeforce.cli.main status"
