import os
import sys

# Add src to sys.path to allow importing from the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

if __name__ == "__main__":
    from spot_downloader.main import main
    main()
