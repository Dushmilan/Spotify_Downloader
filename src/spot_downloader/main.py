import sys
from .gui.app import App

def main():
    """
    Main entry point for the Spot-Downloader package.
    """
    try:
        app = App()
        app.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
