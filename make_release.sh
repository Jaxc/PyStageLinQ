#!/bin/bash

echo "Starting releasebuild! Last release in main branch was:"
cat current_version.txt
echo ""
echo "Which version shall next release be?"
read new_ver

echo $new_ver > current_version.txt
echo "version = \""$new_ver"\"" >> pyproject.toml

rm dist/*

python3 -m build

echo "Please enter token for upload to PyPi"
read -s PyPi_token
echo

twine upload dist/* -u __token__ -p $PyPi_token
