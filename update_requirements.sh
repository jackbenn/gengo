#!/bin/sh
# Re-pin requirements.txt from requirements.in, resolving the newest versions
# in the same Python image the deployed containers use. Needs Docker running.
# Review the diff, run the tests, then commit requirements.txt.
set -e
cd "$(dirname "$0")"
{
    echo "# Exact versions for Python 3.11, generated $(date +%Y-%m-%d) by"
    echo "# update_requirements.sh from requirements.in. Edit requirements.in, not this file."
    docker run --rm -v "$PWD/requirements.in:/requirements.in:ro" python:3.11-slim \
        sh -c 'pip install -q --root-user-action=ignore --disable-pip-version-check -r /requirements.in && pip freeze'
} > requirements.txt.new
mv requirements.txt.new requirements.txt
git diff --stat requirements.txt
