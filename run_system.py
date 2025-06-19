#!/usr/bin/env python3
"""
YouTube Quote Extractor System Launcher
Uses system Python for GUI (tkinter support) and pyenv Python for CLI.
"""

import sys
import subprocess
import os

def show_menu():
    """Display the launcher menu."""
    print("\n" + "="*50)
    print("  YouTube Quote Extractor")
    print("="*50)
    print("\nChoose your interface:")
    print("1. GUI Application (Recommended) - Uses System Python")
    print("2. Command Line Interface - Uses Current Python")
    print("3. Exit")
    print("\n" + "-"*50)

def run_gui_with_system_python():
    """Run GUI with system Python that has tkinter support."""
    try:
        # Use system Python for GUI
        result = subprocess.run([
            "/usr/bin/python3", "gui_app.py"
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running GUI: {e}")
        return False
    except FileNotFoundError:
        print("❌ System Python not found at /usr/bin/python3")
        return False

def main():
    """Main launcher function."""
    while True:
        show_menu()
        try:
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == "1":
                print("\n🚀 Starting GUI Application with System Python...")
                
                # Check if dependencies are installed for system Python
                try:
                    subprocess.run([
                        "/usr/bin/python3", "-c", 
                        "import ttkbootstrap; import google.generativeai"
                    ], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    print("⚠️  Installing dependencies for system Python...")
                    try:
                        subprocess.run([
                            "/usr/bin/python3", "-m", "pip", "install", "-r", "requirements.txt"
                        ], check=True)
                        print("✅ Dependencies installed successfully!")
                    except subprocess.CalledProcessError as e:
                        print(f"❌ Failed to install dependencies: {e}")
                        print("Try running: /usr/bin/python3 -m pip install -r requirements.txt")
                        continue
                
                if run_gui_with_system_python():
                    print("GUI application closed successfully.")
                break
                
            elif choice == "2":
                print("\n💻 Starting Command Line Interface...")
                try:
                    from main import main as cli_main
                    cli_main()
                except Exception as e:
                    print(f"❌ Error starting CLI: {e}")
                break
                
            elif choice == "3":
                print("\n👋 Goodbye!")
                sys.exit(0)
                
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
                input("Press Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main() 