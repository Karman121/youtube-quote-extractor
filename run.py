#!/usr/bin/env python3
"""
YouTube Quote Extractor - Main Launcher
Professional tool for extracting quotes and transcripts from YouTube videos
"""

import sys

# Import runtime hook to set up bundled resources (ffmpeg, .env)
try:
    import runtime_hook
except ImportError:
    pass  # Runtime hook not available when running as script


def main():
    print("=" * 60)
    print("🎬 YouTube Quote Extractor")
    print("   Professional AI-Powered Quote & Transcript Tool")
    print("=" * 60)
    print()
    print("🌐 Starting Web Interface...")
    print("This will open in your web browser automatically.")
    print("Close this window to stop the application.")
    print("-" * 50)
    
    try:
        from web_gui import start_web_gui
        start_web_gui()
    except ImportError as e:
        print(f"❌ Error: Missing required modules: {e}")
        print("Please ensure all dependencies are installed.")
        print("Run: pip install -r requirements.txt")
        input("Press Enter to exit...")
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main() 