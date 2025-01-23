#!/bin/bash


 pytest --junitxml=unit.xml --cov-report xml:coverage.xml --cov=experiment_runner tests/
