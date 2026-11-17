#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
mkdir -p results/computational_audit
python3 scripts/test_computational_study.py > results/computational_audit/test_computational_study.log 2>&1
python3 scripts/results_audit.py > results/computational_audit/run_summary.log
python3 scripts/verify_outputs.py
