#!/bin/bash
# Startup script for GPTInterviewer that fixes PyTorch issues on Mac

# Set environment variables to avoid PyTorch MPS/meta tensor issues
export PYTORCH_ENABLE_MPS_FALLBACK=1
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0

# Run streamlit
streamlit run Homepage.py "$@"
