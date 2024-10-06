Project was built with ChatGPT

This project automatically discovers and synchronizes color between a HyperCube LED light and WiZ smart bulbs on a local network, creating a cohesive, immersive lighting experience across devices.

# Features
- Automatic Discovery: Finds both the HyperCube and WiZ bulbs on the network, eliminating the need for manual IP setup.
- Real-Time Synchronization: Retrieves color data from selected WiZ bulbs and reflects it on the HyperCube.
- Efficient Subnet Scanning: Automatically detects the local subnet and searches for compatible devices.
- Error Logging: Detailed logs to an error log file provide insights into network activity, connection issues, and device responses.

# Requirements
- Python 3.7 or higher
- WiZ Smart Bulbs
- Hyperspace HyperCube
- Local Network (subnet scan enabled)

# Installation
Clone the repository using Git and navigate into the project directory.
Install the necessary dependencies listed in the requirements file.

# Usage
Run the script to start the discovery process.
Select whether you want to synchronize with a single WiZ bulb or all detected bulbs.

# Configuration
The main script automatically detects the subnet and sends HTTP requests to potential IP addresses to locate the HyperCube. Ensure that the HyperCube and WiZ bulbs are connected to the same local network.

# Logging
All requests, responses, and errors are logged in an error log file. This includes responses from discovered devices, connection errors, and any unresponsive IP addresses.

# Contributing
Contributions are welcome! Please fork the repository and create a pull request with detailed information on any changes.
