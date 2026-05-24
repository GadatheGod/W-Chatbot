#!/bin/bash
# WebAI Chat Systemd Installation Script

echo "Installing WebAI Chat as a systemd service..."

# Copy service file
sudo cp webaichat.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable webaichat

# Start the service
sudo systemctl start webaichat

echo "Service installed and started!"
echo "Access WebAI Chat at: http://localhost:13700"
echo "Check status: sudo systemctl status webaichat"
echo "View logs: sudo journalctl -u webaichat -f"
