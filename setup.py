#!/usr/bin/env python3
"""
Setup script for Spotify Downloader
"""

from setuptools import setup, find_packages


setup(
    name="spotify-downloader",
    version="1.0.0",
    description="A tool to download Spotify tracks, albums, and playlists as audio files",
    author="Qwen",
    packages=find_packages(),
    install_requires=[
        "spotifyscraper",
        "yt-dlp",
        "ffmpeg-python",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "spotify-dl=spotify_downloader.cli.main:main",  # This creates the 'spotify-dl' command
        ],
    },
    python_requires=">=3.6",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)