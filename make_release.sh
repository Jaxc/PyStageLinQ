#!/bin/bash

echo "Starting releasebuild!"

new_ver=$(git tag --points-at HEAD)

echo "Version detected from git tag: $new_ver"

echo "Updating pyproject.toml"
sed -i 's/version = "0.0.0"/version = "'$new_ver'"/' pyproject.toml
sed -i 's/release = "0.0.0"/release = "'$new_ver'"/' docs/conf.py


rm dist/* -f

python3 -m build

twine upload dist/* -u __token__ -p $1
