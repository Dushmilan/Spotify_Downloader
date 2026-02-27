import sys
from .gui.app import App
from .config import app_config
from .utils.logger import setup_logging, get_logger

logger = get_logger(__name__)

def main():
    """
    Main entry point for the Spot-Downloader package.
    """
    try:
        # Setup logging
        setup_logging(app_config.log_level)
        
        logger.info(f"Starting Spot-Downloader v{app_config.get('version', '1.0.0')}")
        logger.debug(f"Config: download_path={app_config.download_path}, quality={app_config.download_quality}")
        
        app = App()
        app.mainloop()
    except KeyboardInterrupt:
        logger.info("Application closed by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
