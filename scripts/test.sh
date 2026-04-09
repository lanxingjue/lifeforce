#!/bin/bash
# 运行测试

set -e

echo "Running tests..."
py -m pytest tests/ -v
echo "All tests passed"
