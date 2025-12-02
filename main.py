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

# Import MQ135 library
from mq135 import *

# Import BMP280 library
from bmp280 import *

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
        self.quality = sensors.mq135(self.temp, self.humidity)
        self.pressure = self.sensors.bmp280()

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
        return {"temp": self.DHT11.temperature(), "humidity": self.DHT11.humidity()}

    def mq135(self, temp, humidity):
        if self.MQ135 == None:
            return None
        rzero = self.MQ135.get_rzero()
        corrected_rzero = self.MQ135.get_corrected_rzero(temo, humidity)
        resistance = self.MQ135.get_resistance()
        ppm = self.MQ135.get_ppm()
        corrected_ppm = self.MQ135.get_corrected_ppm(temp, humidity)
        return corrected_ppm
    
    def bmp280(self):
        if self.BMP280 == None:
            return None
        return self.BMP280.pressure
    
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
            DHT11_object.temperature()
            print("INFO: Initialized DHT11 module")
        except:
            print("ERROR: Failed to initialize DHT11 module")
            DHT11_object = None
    else:
        print("INFO: DHT11 module is disabled")

    # MQ135 module initialization
    if MQ135_ENABLED == True:
        try:
            MQ135_object = MQ135(0)
            print("INFO: Initialized MQ135 module")
        except:
            print("ERROR: Failed to initialize MQ135 module")
    else:
        print("INFO: MQ135 module is disabled")

    # BMP280 sensor initialization
    if BMP280_ENABLED == True:
        bus = machine.I2C(sda=machine.Pin(8), scl=machine.Pin(9))
        addr = 0x76
        if addr in bus.scan():
            print("INFO: bmp280 module found at I2C address " + hex(addr))
            try:
                BMP280_object = BMP280(bus)

                BMP280_object.use_case(BMP280_CASE_WEATHER)
                BMP280_object.oversample(BMP280_OS_HIGH)
                BMP280_object.normal_measure()
                print("INFO: Initialized BMP280 module")
            except:
                print("ERROR: Failed to initialize BMP280 module")
        else:
            print("ERROR: BMP280 module not found!")
    else:
        print("INFO: BMP280 module is disabled")
    
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