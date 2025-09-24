#!/usr/bin/env python3
"""
Development server script for Kiosk Display
Runs both Flask API backend and React frontend development server
"""

import os
import sys
import signal
import subprocess
import threading
import time
from pathlib import Path

class DevelopmentServer:
    def __init__(self):
        self.flask_process = None
        self.react_process = None
        self.running = True

        # Get project paths
        self.display_dir = Path(__file__).parent
        self.frontend_dir = self.display_dir / "frontend"

    def print_banner(self):
        print("\n" + "="*60)
        print("🚀 KIOSK DISPLAY DEVELOPMENT SERVER")
        print("="*60)
        print("Flask API:      http://localhost:5000")
        print("React Frontend: http://localhost:3000")
        print("API Endpoints:  http://localhost:5000/api/v1/*")
        print("="*60)
        print("Press Ctrl+C to stop both servers")
        print("="*60 + "\n")

    def check_requirements(self):
        """Check if required files exist"""
        print("🔍 Checking requirements...")

        # Check if frontend directory exists
        if not self.frontend_dir.exists():
            print("❌ Frontend directory not found!")
            print(f"Expected: {self.frontend_dir}")
            return False

        # Check if package.json exists
        package_json = self.frontend_dir / "package.json"
        if not package_json.exists():
            print("❌ Frontend package.json not found!")
            print("Run 'npm install' in the frontend directory first")
            return False

        # Check if Flask app exists
        app_py = self.display_dir / "app.py"
        if not app_py.exists():
            print("❌ Flask app.py not found!")
            return False

        print("✅ All requirements found")
        return True

    def install_frontend_deps(self):
        """Install frontend dependencies if node_modules doesn't exist"""
        node_modules = self.frontend_dir / "node_modules"
        if not node_modules.exists():
            print("📦 Installing frontend dependencies...")
            try:
                subprocess.run(
                    ["npm", "install"],
                    cwd=self.frontend_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                print("✅ Frontend dependencies installed")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install frontend dependencies: {e}")
                return False
        return True

    def start_flask_server(self):
        """Start Flask development server"""
        print("🐍 Starting Flask API server...")

        env = os.environ.copy()
        env["FLASK_ENV"] = "development"
        env["FLASK_DEBUG"] = "1"

        try:
            self.flask_process = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=self.display_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Start thread to handle Flask output
            flask_thread = threading.Thread(
                target=self.handle_flask_output,
                daemon=True
            )
            flask_thread.start()

            # Wait a moment for Flask to start
            time.sleep(2)
            print("✅ Flask server started on http://localhost:5000")

        except Exception as e:
            print(f"❌ Failed to start Flask server: {e}")
            return False

        return True

    def start_react_server(self):
        """Start React development server"""
        print("⚛️  Starting React development server...")

        try:
            self.react_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Start thread to handle React output
            react_thread = threading.Thread(
                target=self.handle_react_output,
                daemon=True
            )
            react_thread.start()

            # Wait a moment for React to start
            time.sleep(3)
            print("✅ React server started on http://localhost:3000")

        except Exception as e:
            print(f"❌ Failed to start React server: {e}")
            return False

        return True

    def handle_flask_output(self):
        """Handle Flask server output"""
        if not self.flask_process:
            return

        for line in iter(self.flask_process.stdout.readline, ''):
            if self.running and line.strip():
                print(f"[FLASK] {line.strip()}")

    def handle_react_output(self):
        """Handle React server output"""
        if not self.react_process:
            return

        for line in iter(self.react_process.stdout.readline, ''):
            if self.running and line.strip():
                # Filter out some verbose React output
                if any(skip in line for skip in ['webpack', 'compiled', 'asset', 'entrypoint']):
                    continue
                print(f"[REACT] {line.strip()}")

    def cleanup(self):
        """Clean up processes"""
        print("\n🛑 Shutting down servers...")
        self.running = False

        if self.react_process:
            print("⚛️  Stopping React server...")
            self.react_process.terminate()
            try:
                self.react_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.react_process.kill()

        if self.flask_process:
            print("🐍 Stopping Flask server...")
            self.flask_process.terminate()
            try:
                self.flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.flask_process.kill()

        print("✅ All servers stopped")

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C"""
        self.cleanup()
        sys.exit(0)

    def run(self):
        """Main run method"""
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)

        try:
            self.print_banner()

            # Check requirements
            if not self.check_requirements():
                sys.exit(1)

            # Install frontend dependencies if needed
            if not self.install_frontend_deps():
                sys.exit(1)

            # Start Flask server
            if not self.start_flask_server():
                sys.exit(1)

            # Start React server
            if not self.start_react_server():
                self.cleanup()
                sys.exit(1)

            print("\n🎉 Development environment ready!")
            print("Open http://localhost:3000 for the React app")
            print("API available at http://localhost:5000/api/v1/*")
            print("\nWatching for changes...")

            # Keep the main thread alive
            while self.running:
                time.sleep(1)

                # Check if processes are still running
                if self.flask_process and self.flask_process.poll() is not None:
                    print("❌ Flask server stopped unexpectedly")
                    break

                if self.react_process and self.react_process.poll() is not None:
                    print("❌ React server stopped unexpectedly")
                    break

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    server = DevelopmentServer()
    server.run()