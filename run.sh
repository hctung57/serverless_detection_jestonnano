
#!/usr/bin/env bash
echo "RUNNING DETECTION APP"
python3 jetson_detection.py
# Just a loop to keep the container running
while true; do :; done