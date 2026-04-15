#!/usr/bin/env python3
"""Launch script for the improved timer-based baby bot."""

import os
import sys
import subprocess

def main():
    """Run the improved timer-based bot."""
    print("🚀 Starting Improved Timer-Based Baby Bot...")
    print("📱 Features:")
    print("  • Simple activity timers (no more confusing cycles!)")
    print("  • Real-time duration tracking")
    print("  • Smart suggestions based on patterns")
    print("  • Cleaner, more intuitive interface")
    print()

    # Set environment variable
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        print("❌ ERROR: TELEGRAM_BOT_TOKEN environment variable not set!")
        print("Please set it in your .env file or export it manually.")
        sys.exit(1)

    try:
        # Import and run the new app
        from src.app_timer import main as timer_main
        timer_main()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped gracefully.")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()