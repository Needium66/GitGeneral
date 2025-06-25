#!/usr/bin/env python3
import os
import sys
import subprocess

# Change to python_server directory
os.chdir('python_server')

# Run the FastAPI server
subprocess.run([sys.executable, 'main.py'])