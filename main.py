#
# Fetch The Weather: Weather stations
# Version dev
# Copyright (c) 2025 FetchTheWeather
#

#
# LICENSED UNDER THE MIT LICENSE
#

# Import core libraries
import network, time, json, urequests, random, machine

# Import DHT11 library
import dht

# Global variables
MODE = "OFFLINE"
URL = "https://ftw.pietr.dev/ws/weather/data"
CONFIG_FILE = "/config.json"
sta_if = network.WLAN(network.WLAN.IF_STA)
START_MSG = """
Fetch The Weather: Weather stations
Copyright (c) 2025 Fetch The Weather
"""

# SENSORS
DHT11_ENABLED = True
MQ135_ENABLED = True
BMP280_ENABLED = True

# Define classes
class Data:
    def __init__(self, sensors, config):
        self.sensors = sensors
        self.config = config
        self.time = None
        self.temp = None
        self.humidity = None
        self.quality = None
        self.pressure = None
    
    def collect(self):
        dht11_data = self.sensors.dht11()
        self.time = time.time()
        self.temp = dht11_data["temp"]
        self.humidity = dht11_data["humidity"]
        self.quality = None
        self.pressure = None
        
    def get_dict(self):
        if self.temp == None:
            temp = 0
        else:
            temp = self.temp
        if self.humidity == None:
            humidity = 0
        else:
            humidity = self.humidity
        if self.quality == None:
            quality = 0
        else:
            quality = self.quality
        if self.pressure == None:
            pressure = 0
        else:
            pressure = self.pressure
        return {"weatherStationId": str(self.config.config["id"]), "temperatureCelsius": temp, "airPressureHpa": pressure, "airQualityPpm": quality, "humidityPercent": humidity, "timestamp": str(self.time)}

class Sensors:
    def __init__(self, dht11, mq135, bmp280):
        self.DHT11 = dht11
        self.MQ135 = mq135
        self.BMP280 = bmp280
    
    def dht11(self):
        if self.DHT11 == None:
            return {"temp": None, "humidity": None}
        self.DHT11.measure()
        return {"temp": self.DHT11.temperature(), "humidity": self.DHT11.humidity()}
    
class Config:
    def __init__(self):
        self.config = {"id": 0, "network": {"ssid": "", "psk": ""}, "logfile": "/log.txt"}
        
    def load(self):
        f = open(CONFIG_FILE)
        conf = json.load(f)
        f.close()
        if self.valid(conf) == False:
            print("ERROR: Invalid configuration file")
            print("INFO: Sticking with default configuration")
        else:
            self.config = conf
            # Check if ID != 0
            if self.config["id"] == 0:
                print("INFO: Detected default ID, setting a new ID...")
                self.config["id"] = random.randint(1, 999999999)
                self.write()
                print("INFO: ID: 0 => " + str(self.config["id"]))
    
    def write(self):
        f = open(CONFIG_FILE, "w")
        json.dump(self.config, f)
        f.close()
    
    def valid(self, conf):
        if (("id" and "network" and "ssid" and "psk" and "logfile") in conf.keys()) == False:
            return False
        if (("ssid" and "psk") in conf["network"].keys()) == False:
            return False
        return True
        

def connect(config):
    global MODE
    if sta_if.active() == False:
        sta_if.active(True)
    sta_if.connect(config["network"]["ssid"], config["network"]["psk"]) # Connects to network
    i = 0
    connected = False
    while i < 10: # Checks for a connection during a 10 second period
        if sta_if.isconnected() == True:
            connected = True
            break
        time.sleep(1)
        i = i + 1
    if connected == False:
        print("ERROR: Failed to connect to network, running in offline mode")
    else:
        print(f"INFO: Connected to network {config['network']['ssid']}")
        MODE = "ONLINE"

def get_time():
    return time.time()

def log():
    f = open(config.config["logfile"], "a")
    f.write(str(data.get_dict()) + "\n")
    f.close()
    print("LOG: " + str(data.get_dict()))
        
# Main program loop
if __name__ == "__main__":
    print(START_MSG)
    print("INFO: Initializing system...")
    config = Config()
    config.load()
    
    DHT11_object = None
    MQ135_object = None
    BMP280_object = None
    
    # Sensor initialization goes here
    
    # DHT11 sensor initialization
    if DHT11_ENABLED == True:
        try:
            DHT11_object = dht.DHT11(machine.Pin(4))
            try: DHT11_object.measure() # First time always fails to pull data due to a checksum error
            except: DHT11_object.measure() # Second time should work if the sensor is available
            print("INFO: Initialized DHT11 module")
        except:
            print("ERROR: Failed to initialize DHT11 module")
            DHT11_object = None
    else:
        print("INFO: DHT11 module is disabled")
    
    sensors = Sensors(dht11=DHT11_object, mq135=MQ135_object, bmp280=BMP280_object) # Add sensor objects here
    data = Data(sensors, config)
    connect(config.config)
    print("INFO: Initialized system")
    print("INFO: Running main loop")
    while True: # Infinite loop
        data.collect()
        if MODE == "ONLINE":
            response = urequests.request("POST", URL, json=data.get_dict())
            if response.status_code == 200:
                print("INFO: 200 from " + URL + ": " + response.text)
            else:
                print("WARNING: An error occured when sending request. Falling back to logfile...")
                log()
        else:
            log()
        time.sleep(60)