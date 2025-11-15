#!/usr/bin/env python3
"""
Setup script for Spotify Downloader
"""

import subprocess
import sys


def install_dependencies():
    """
    Install all required dependencies from requirements.txt
    """
    try:
        # Install using pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)


if __name__ == "__main__":
    install_dependencies()