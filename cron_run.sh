#!/bin/bash
cd /home/gordonpipa/.hermes/cache/scratch/research-monitor
python3 monitor.py
echo "---"
ls -la outputs/
echo "---"
cat outputs/report_$(date +%Y-%m-%d).md 2>/dev/null || echo "No report found"
