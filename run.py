#!/usr/bin/env python3
"""
YouTube Quote Extractor - Launcher
Choose between CLI and Web GUI interfaces.
"""

import sys


def main():
    """Main launcher function."""
    print("🎬 YouTube Quote Extractor")
    print("=" * 40)
    print("Choose your interface:")
    print("1. 💻 Command Line Interface (CLI)")
    print("2. 🌐 Web Browser Interface (Recommended)")
    print("3. ❌ Exit")
    print()
    
    while True:
        try:
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == '1':
                print("\n🚀 Starting CLI interface...")
                import main
                main.main()
                break
                
            elif choice == '2':
                print("\n🌐 Starting web interface...")
                print("This will open in your default web browser.")
                import web_gui
                web_gui.main()
                break
                
            elif choice == '3':
                print("\n👋 Goodbye!")
                sys.exit(0)
                
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.")


if __name__ == "__main__":
    main() 