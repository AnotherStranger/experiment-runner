#!/usr/bin/env bash

DEV_MODE="--remove-output"
STATIC_MODE="no"
export CCFLAGS="-Os -pipe"

help(){
  echo "This command builds a single executable from the python project"
  echo "Usage: $(basename "$0") [-d] [-s]"
  echo "  -d:"
  echo "      Development mode. Keep build files after building"
  echo "  -s:"
  echo "      Use static-libphython attribute."
  echo "  -h:"
  echo "      Print this help and exit."
  echo "  -?:"
  echo "      Alias for -h."
  exit 0
}

while getopts 'ds?h' OPTION; do
  case "$OPTION" in
  d)
    DEV_MODE=""
  ;;
  s)
    STATIC_MODE="yes"
  ;;
  ?)
    help
  ;;
  esac
done


poetry install
poetry build

# shellcheck disable=SC2086 # We want globbing and word splitting here
poetry run python -m nuitka \
  --onefile \
  --static-libpython=$STATIC_MODE \
  --include-package=tabulate \
  --include-package=shellingham \
  --include-package=pygments \
  --lto=no \
  --product-name="experiment-runner" \
  --product-version="$(poetry version -s | grep -oE '^[0-9]+\.[0-9]+\.[0-9]+')"  \
  --output-dir=dist \
  --output-filename=experiment \
  $DEV_MODE \
  experiment_runner/cli/main.py
