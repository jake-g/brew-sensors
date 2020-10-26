# Set Up brew-logger DietPi Service:
```
sudo cp brew-logger.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/brew-logger.service
sudo systemctl daemon-reload
sudo systemctl enable brew-logger.service
# Test: 
dietpi-services restart brew-logger && journalctl -f -u brew-logger.service -n 100
```
