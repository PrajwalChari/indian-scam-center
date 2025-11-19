"""
Email Search System Launcher
Choose between GUI and Command Line interface
"""

import sys
import os

def main():
    print("=" * 70)
    print("All-in-One Sponsorship Software Suite")
    print("=" * 70)
    print("Choose your application:")
    print("1. Sponsorship Software (Complete Suite) - RECOMMENDED")
    print("2. Modern Email Search GUI")
    print("3. Basic Email Search GUI")
    print("4. Command Line Email Search")
    print("0. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (0-4): ").strip()
            
            if choice == "1":
                print("Starting All-in-One Sponsorship Software...")
                print("Features: Email Search + AI Vendor Finder + Database Management")
                import sponsorship_software
                sponsorship_software.main()
                break
            elif choice == "2":
                print("Starting Modern Email Search GUI...")
                import modern_gui
                modern_gui.main()
                break
            elif choice == "3":
                print("Starting Basic Email Search GUI...")
                import email_search_gui
                email_search_gui.main()
                break
            elif choice == "4":
                print("Starting command line interface...")
                import main_windows
                main_windows.main()
                break
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 0, 1, 2, 3, or 4.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.")

if __name__ == "__main__":
    main()