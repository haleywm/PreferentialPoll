#!/bin/bash

# Create venv
if [ -d "venv" ]; then
    python -m venv venv
fi

# Source venv
source venv/bin/activate

# Install updates
pip install -U -r requirements.txt
