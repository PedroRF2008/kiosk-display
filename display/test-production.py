#!/usr/bin/env python3
"""
Production build test script
Tests that the production build works correctly
"""

import os
import time
import subprocess
import sys
import signal
from pathlib import Path

class ProductionTester:
    def __init__(self):
        self.flask_process = None
        self.display_dir = Path(__file__).parent

    def print_banner(self):
        print("\n" + "="*60)
        print("🧪 TESTING PRODUCTION BUILD")
        print("="*60)
        print("This script will:")
        print("1. Check if React build exists")
        print("2. Start Flask server in production mode")
        print("3. Test key endpoints")
        print("4. Show results")
        print("="*60 + "\n")

    def check_build_exists(self):
        """Check if React build exists"""
        build_path = self.display_dir / "static" / "build" / "index.html"

        if build_path.exists():
            print("✅ React build found")
            return True
        else:
            print("❌ React build not found")
            print("Run './build-frontend.sh' first to create the production build")
            return False

    def start_flask_server(self):
        """Start Flask server"""
        print("🐍 Starting Flask server...")

        try:
            self.flask_process = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=self.display_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for server to start
            time.sleep(3)

            if self.flask_process.poll() is None:
                print("✅ Flask server started successfully")
                return True
            else:
                print("❌ Flask server failed to start")
                stdout, stderr = self.flask_process.communicate()
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False

        except Exception as e:
            print(f"❌ Failed to start Flask server: {e}")
            return False

    def test_endpoints(self):
        """Test key endpoints"""
        print("🌐 Testing endpoints...")

        import requests

        base_url = "http://localhost:5000"
        endpoints = [
            ("/", "Main display page"),
            ("/api/v1/display", "Display API"),
            ("/api/v1/weather", "Weather API"),
            ("/api/v1/birthdays", "Birthday API"),
            ("/api/v1/media", "Media API"),
        ]

        results = []

        for endpoint, description in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                status = "✅" if response.status_code == 200 else "⚠️"
                results.append((endpoint, description, response.status_code, status))
            except requests.exceptions.RequestException as e:
                results.append((endpoint, description, f"Error: {e}", "❌"))

        return results

    def cleanup(self):
        """Clean up Flask process"""
        if self.flask_process:
            print("🛑 Stopping Flask server...")
            self.flask_process.terminate()
            try:
                self.flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.flask_process.kill()
            print("✅ Flask server stopped")

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C"""
        self.cleanup()
        sys.exit(0)

    def run(self):
        """Main test runner"""
        signal.signal(signal.SIGINT, self.signal_handler)

        try:
            self.print_banner()

            # Check if build exists
            if not self.check_build_exists():
                sys.exit(1)

            # Start Flask server
            if not self.start_flask_server():
                sys.exit(1)

            # Import requests here to avoid import error if not installed
            try:
                import requests
            except ImportError:
                print("❌ 'requests' package not found")
                print("Install with: pip install requests")
                self.cleanup()
                sys.exit(1)

            # Test endpoints
            results = self.test_endpoints()

            # Show results
            print("\n📊 TEST RESULTS")
            print("="*60)
            for endpoint, description, status, icon in results:
                print(f"{icon} {endpoint:<20} {description:<20} {status}")

            print("="*60)
            print("🎉 Production build test completed!")
            print("If all endpoints show ✅, your production build is working correctly.")
            print("\nTo stop the test server, press Ctrl+C")

            # Keep server running for manual testing
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass

        except Exception as e:
            print(f"❌ Test failed: {e}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    tester = ProductionTester()
    tester.run()