#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import threading

def start_backend():
    """Start the backend server"""
    print("🚀 Starting Backend Server...")
    try:
        # Change to imageprocessing directory
        os.chdir('imageprocessing')
        
        # Start uvicorn server
        process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 'main:app', 
            '--host', '0.0.0.0', '--port', '8000', '--reload'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print("✅ Backend server started successfully!")
        print("📡 Backend running on: http://localhost:8000")
        
        # Wait for the process
        process.wait()
        
    except Exception as e:
        print(f"❌ Error starting backend: {e}")

def start_mobile():
    """Start the mobile app"""
    print("📱 Starting Mobile App...")
    try:
        # Change to klipps_app directory
        os.chdir('klipps_app')
        
        # Start Flutter app
        process = subprocess.Popen([
            'flutter', 'run'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print("✅ Mobile app started successfully!")
        
        # Wait for the process
        process.wait()
        
    except Exception as e:
        print(f"❌ Error starting mobile app: {e}")

if __name__ == "__main__":
    print("🎯 Starting KLIPPS Project...")
    print("=" * 50)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    # Wait a bit for backend to start
    time.sleep(3)
    
    # Start mobile app
    start_mobile() 