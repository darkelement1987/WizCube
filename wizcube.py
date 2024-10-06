import socket
import json
import requests
import time
import logging
import sys
import ipaddress

# Configure logging
logging.basicConfig(filename='error.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Port for WiZ discovery and HyperCube discovery
WIZ_PORT = 38899
HYPERCUBE_URL_TEMPLATE = "http://{}/json/state"  # Template for HyperCube IP

# Message to be sent to discover WiZ lamps
DISCOVERY_MESSAGE = json.dumps({
    "method": "getSystemConfig",
    "params": {}
})

def get_broadcast_ip():
    nets = socket.getaddrinfo(socket.gethostname(), None)
    for net in nets:
        if net[0] == socket.AF_INET:
            broadcast_ip = '.'.join(net[4][0].split('.')[:-1]) + '.255'
            return broadcast_ip
    raise Exception("No suitable network found.")

def get_local_ip():
    """Get the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Verbinding maken met een externe host (deze verbinding wordt niet echt gebruikt)
        s.connect(("8.8.8.8", 80))  # Google DNS
        return s.getsockname()[0]  # Return the local IP address
    finally:
        s.close()

def discover_wiz_lamps():
    print("Discovering WiZ lamps on the network...")  # Meldingen voor ontdekking
    broadcast_ip = get_broadcast_ip()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(3)

    sock.sendto(DISCOVERY_MESSAGE.encode('utf-8'), (broadcast_ip, WIZ_PORT))

    wiz_lamps = []
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            response = json.loads(data.decode('utf-8'))
            if 'result' in response and 'mac' in response['result']:
                wiz_lamps.append(addr[0])
    except socket.timeout:
        pass
    except Exception as e:
        logging.error(f"Error during WiZ lamp discovery: {e}")
    finally:
        sock.close()

    if wiz_lamps:
        print(f"WiZ lamps discovered: {', '.join(wiz_lamps)}")
    else:
        print("No WiZ lamps found.")

    return wiz_lamps

def discover_hypercube():
    print("Discovering HyperCube on the network...")  # Meldingen voor ontdekking
    
    local_ip = get_local_ip()
    logging.info(f"Local IP address detected: {local_ip}")
    
    # Bepaal het subnet
    subnet = ipaddress.ip_network(local_ip + '/24', strict=False)  # Gebruik een /24 subnet mask
    
    for ip in subnet.hosts():
        try:
            response = requests.get(f"http://{ip}/json/info", timeout=1)  # Timeout voor snelle checks
            if response.status_code == 200:
                info = response.json()
                if info.get("brand") == "Hyperspace":
                    print(f"HyperCube discovered at: {ip}")
                    return str(ip)
        except (requests.RequestException, json.JSONDecodeError) as e:
            logging.debug(f"Failed to reach {ip}: {e}")
            continue

    print("No HyperCube found.")
    return None

def get_lamp_status(ip):
    data = json.dumps({"method": "getPilot", "params": {}})
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    sock.sendto(data.encode('utf-8'), (ip, WIZ_PORT))

    try:
        response, _ = sock.recvfrom(1024)
        response_decoded = response.decode('utf-8')
        logging.info(f"Received response from lamp {ip}: {response_decoded}")
        return response_decoded
    except socket.timeout:
        logging.error(f"Timeout while getting status from lamp {ip}.")
        return None
    except Exception as e:
        logging.error(f"Error getting status from lamp {ip}: {e}")
        return None
    finally:
        sock.close()

def update_hypercube_color(hypercube_ip, r, g, b, dimmer):
    bri = int((dimmer / 100) * 255)
    data = {
        "on": True,
        "bri": bri,
        "seg": [{
            "start": 0,
            "stop": 88,
            "col": [[r, g, b]],
            "fx": 103,
            "pal": 0,
        }]
    }

    try:
        response = requests.post(HYPERCUBE_URL_TEMPLATE.format(hypercube_ip), json=data)
        response.raise_for_status()
        logging.info(f"Successfully updated HyperCube with color: R={r}, G={g}, B={b}, Brightness={bri}")
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred while communicating with HyperCube: {err}")
    except Exception as e:
        logging.error(f"Error communicating with HyperCube: {e}")

def main():
    print("Starting discovery process for WiZ lamps and HyperCube...")  # Algemene melding voor start proces
    wiz_lamps = discover_wiz_lamps()
    hypercube_ip = discover_hypercube()

    if hypercube_ip:
        print(f"HyperCube found at: {hypercube_ip}")
    else:
        print("No HyperCube found.")
        return

    choice = input("Would you like to read from a single lamp or all? (single/all): ").strip().lower()
    if choice == "single":
        print("Choose a lamp from the following:")
        for index, lamp in enumerate(wiz_lamps):
            print(f"{index + 1}: {lamp}")

        selected_index = int(input("Enter the number of the lamp you want to select: ")) - 1
        if selected_index < 0 or selected_index >= len(wiz_lamps):
            print("Invalid lamp selected. Exiting.")
            return
        selected_lamps = [wiz_lamps[selected_index]]
    elif choice == "all":
        selected_lamps = wiz_lamps
    else:
        print("Invalid choice. Exiting.")
        return

    last_colors = {}

    try:
        while True:
            for ip in selected_lamps:
                status = get_lamp_status(ip)
                if status is None:
                    continue

                status_json = json.loads(status)
                if 'result' in status_json:
                    scene_id = status_json['result'].get('sceneId', None)
                    if scene_id is not None and scene_id != 0:
                        continue

                    r = status_json['result'].get('r')
                    g = status_json['result'].get('g')
                    b = status_json['result'].get('b')
                    dimmer = status_json['result'].get('dimming', 100)

                    if r is None or g is None or b is None:
                        continue
                    
                    if (r, g, b, dimmer) != last_colors.get(ip):
                        print(f"Updating color to: R={r}, G={g}, B={b}, Dimmer={dimmer}")
                        update_hypercube_color(hypercube_ip, r, g, b, dimmer)
                        last_colors[ip] = (r, g, b, dimmer)

            if choice == "single":
                time.sleep(0.1)  # 0.1 to not spam the network
            else:
                time.sleep(0.7)  # Longer delay for multiple lamps
    except KeyboardInterrupt:
        print("Shutting down the application...")
        sys.exit(0)

if __name__ == "__main__":
    main()
