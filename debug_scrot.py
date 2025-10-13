#!/usr/bin/env python3
import subprocess
import tempfile
import os
import cv2

# Test scrot directly
tmp_fd, tmp_path = tempfile.mkstemp(suffix=".png")
os.close(tmp_fd)

print(f"Temp file: {tmp_path}")

cmd = ["scrot", tmp_path]
print(f"Command: {' '.join(cmd)}")

result = subprocess.run(cmd, capture_output=True, timeout=5.0)

print(f"Return code: {result.returncode}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")

if os.path.exists(tmp_path):
    size = os.path.getsize(tmp_path)
    print(f"File exists, size: {size} bytes")
    
    if size > 0:
        img = cv2.imread(tmp_path)
        if img is not None:
            print(f"OpenCV loaded image: {img.shape}")
        else:
            print("OpenCV failed to load image")
    
    os.unlink(tmp_path)
else:
    print("File does not exist")