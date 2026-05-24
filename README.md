# Sensor Logging System

A Python-based system for logging physical and virtual sensors (I2C, Bluetooth Low Energy, and Web APIs) to multiple destinations, including local TSV files, a local HTTP JSON status server, and Google Sheets.

This repository contains configurations for two primary logging setups:
1. **Brew Logger (Main / Active)**: The main production setup used for fermentation tracking. It monitors ambient environment I2C sensors and a Bluetooth-based Tilt Hydrometer, logging data locally and backing up to Google Sheets.
2. **Solar Logger (2021 Archived)**: A development R&D setup for solar panels powering various sensors and data logging (currently inactive).

---

## Repository Structure

```
├── blescan.py              # Bluetooth Low Energy event parsing helpers
├── loggers.py              # Logging backend adapters (TSV, JSON Server, Google Sheets)
├── requirements.txt        # Python dependency list
├── run_brew_logger.py      # Main entrypoint for brewing telemetry
├── runner.py               # The main loop orchestration and error-recovery logic
├── sensors.py              # Class wrappers for I2C and virtual (weather) sensors
├── tilt.py                 # Tilt hydrometer BLE client wrapper
├── auth/                   # Local secrets/credentials folder (Git ignored)
├── brew-logs/              # Directory for brew logger outputs (Git ignored)
├── service/                # systemd service definitions for DietPi deployment
│   ├── README.md
│   ├── brew-logger.service
│   ├── solar-logger.service
│   └── example.service
└── solar_sensor/           # Solar-specific logging configuration
    ├── run_solar_logger.py  # Main entrypoint for solar telemetry
    └── solar-logs/         # Directory for solar logger outputs (Git ignored)
```

---

## Hardware and Integrations Supported

- **Tilt Hydrometer** (via BLE Bluetooth) for gravity and temperature.
- **I2C Ambient Sensors**:
  - **BME280**: Temperature, Humidity, Barometric Pressure.
  - **MCP9808**: Precision Temperature.
  - **SGP30**: Indoor Air Quality (TVOC and eCO2).
  - **BH1750** & **TSL2591** & **VEML7700**: Ambient / Visible Light.
  - **VEML6070**: UV Light index.
- **Power Monitors**:
  - **INA219** & **INA260**: DC Voltage, Current, and Power monitoring.
- **System Telemetry**:
  - **PiSensors**: CPU Temperature, RAM Usage, and Disk Usage for Raspberry Pi.
- **Virtual Sensors**:
  - **OpenWeatherMap API**: Current weather conditions based on GPS coordinates.

---

## Brew Logger Data Example

Below is an example snippet of the telemetry logged during a fermentation run, combining Tilt hydrometer metrics, I2C environment sensors, and OpenWeatherMap conditions:

| Timestamp | Tilt Gravity | ABV (%) | Tilt Temp | Amb Temp | Amb Hum | Amb Pres | CO2 (ppm) | Lux | Pi CPU Temp | Weather Temp | Weather Cond |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `09-29 20:30` | 1.0190 | 1.19% | 79.0°F | 72.3°F | 59.4% | 1004.6 hPa | 400 | 0.00 | 100.2°F | 58.8°F | Rain (Heavy) |
| `09-29 21:33` | 1.0160 | 1.59% | 80.0°F | 71.5°F | 62.9% | 1004.6 hPa | 453 | 0.00 | 97.3°F | 57.6°F | Clouds |
| `09-30 09:03` | 1.0090 | 2.51% | 79.0°F | 69.6°F | 57.9% | 1003.9 hPa | 400 | 1.47 | 96.4°F | 54.5°F | Clouds |

---


## Setup & Installation

### 1. Install Dependencies
Install Python dependencies via `pip`:
```bash
pip install -r requirements.txt
```
> **Note**: The **Tilt Hydrometer** sensor and its dependency `pybluez` are optional. If you are not using a Tilt sensor, you can remove `pybluez` from `requirements.txt`, and remove/comment out the `beer` entry in `run_brew_logger.py`'s `SENSOR_MAP`.
>
> `pybluez` requires system-level Bluetooth development libraries (`libbluetooth-dev` on Debian/Ubuntu). It is used for BLE scanning on Linux and will not function natively on macOS.

### 2. Google Sheets Authentication
To log data directly to Google Sheets:
1. Set up a Google Cloud project with the Sheets and Drive APIs enabled.
2. Create a Service Account and download the JSON key.
3. Save the JSON key under `auth/brew-secret.json` (or `auth/solar-secret.json` for solar monitoring).
4. Share the destination Google Sheet with the Service Account's email address.

### 3. OpenWeatherMap Authentication
To query virtual weather forecasts for your GPS coordinates:
1. Register and generate an API key on [OpenWeatherMap](https://openweathermap.org/).
2. Create a JSON credentials file under `auth/openweathermap.json` with the following structure:
   ```json
   {
     "api_key": "your_openweathermap_api_key_here"
   }
   ```

---


## Running the Loggers

### Brew Logger
Run the script as root/sudo (required for Bluetooth socket permissions):
```bash
sudo python3 run_brew_logger.py
```

## Development and Testing

A testing suite with mocked hardware/API adapters is available to verify the codebase changes locally without target hardware connectivity.

### Makefile Commands

- **Set up Environment**: Create virtual environment and install dev dependencies:
  ```bash
  make setup
  ```
- **Run Tests**: Execute the unit tests suite:
  ```bash
  make test
  ```
- **Format Code**: Check files against style guide standards (2-space indent):
  ```bash
  make format
  ```
- **Clean Cache**: Delete python cache folders:
  ```bash
  make clean
  ```

---


## Deployment (systemd Service on DietPi / Raspberry Pi Zero)

This application is designed to run 24/7 as a background systemd service on a Raspberry Pi Zero running DietPi OS.

### Target Hardware Specs

* **Device Model**: Raspberry Pi Zero W (armv6l)
* **Operating System**: DietPi v9.20 (Raspbian GNU/Linux 11 bullseye)
* **Kernel**: `Linux 5.10.103+ armv6l`
* **Python Version**: `3.9.2`
* **Memory**: 512MB RAM (~400MB system-visible, ~100MB used during run)

### Configuration Steps

0a. **Enable I2C Interface**:
   Because the system reads from physical I2C sensors, the I2C interface must be enabled on the Raspberry Pi Zero:
   * Run `sudo dietpi-config`.
   * Go to **Advanced Options** -> **I2C State** and set it to **Enabled**.
   * Reboot the Pi: `sudo reboot`.
   * Optionally install `i2c-tools` to scan the I2C bus and verify sensor connection:
     ```bash
     sudo apt-get install -y i2c-tools
     sudo i2cdetect -y 1
     ```

0b. **Enable Bluetooth/BLE (Optional, for Tilt Sensor)**:
   If you are using a Tilt Hydrometer to log fermentation gravity:
   * Run `sudo dietpi-config`.
   * Go to **Advanced Options** -> **Bluetooth** and set it to **Enabled**.
   * Reboot the Pi: `sudo reboot`.
   * Install Bluetooth development libraries:
     ```bash
     sudo apt-get install -y libbluetooth-dev
     ```

1. **Copy Service File**:
   Copy the desired service configuration to the systemd folder:
   ```bash
   sudo cp service/brew-logger.service /etc/systemd/system/
   ```

2. **Set File Permissions**:
   ```bash
   sudo chmod 644 /etc/systemd/system/brew-logger.service
   ```

3. **Reload systemd Daemon and Enable Service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable brew-logger.service
   ```

4. **Start and Test the Service**:
   ```bash
   sudo systemctl restart brew-logger.service
   # View logs:
   journalctl -f -u brew-logger.service -n 100
   ```
   *(Note: DietPi users can also use `dietpi-services restart brew-logger` to control the service).*

For developer notes, active bugs, and codebase health status, see [DEV_NOTES.md](file:///Users/jakegarrison/Downloads/projects/sensors/DEV_NOTES.md).
