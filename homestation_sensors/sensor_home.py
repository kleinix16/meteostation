#!/usr/bin/python

###############################################################################################################
######   Description: Meranie teploty v izbe a na radiatore, zapis do DB
######   Author: Tomas Klein
######   Created: 2020/04/11 21:09:50
######   Last modified: 2020/04/12 12:48:44
###############################################################################################################

import mysql.connector
import logging
import json
import smbus
import time
import argparse

################################ PYTHON BASIC SETUP ###########################################################
#Arguments definition
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--cfg_file", required=False, default='/home/pi/meteostation/config.json',          help="Configuration file parh")
ap.add_argument("-l", "--log_file", required=False, default='/home/pi/meteostation/logs/sensor_home.log', help="Logs file path")
ap.add_argument("-m", "--measure",  required=False, action='store_true',                                  help="MEASURE MODE")
args = ap.parse_args()

#Logging to file
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
                    filemode='a',
                    filename=args.log_file
                    )

#Logging to console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
###############################################################################################################

logging.info("-------------- START --------------")

################### I2C SETUP ####################
# Get I2C bus
logging.info("I2C - init")
bus = smbus.SMBus(1)

############# Sensor SHT30 0x45 HOME #############
logging.info("------- sensor_home -------")
logging.info("sensor_home - send measure command")
# Send measurement command, 0x2C(44)
#		0x06(06)	High repeatability measurement
bus.write_i2c_block_data(0x45, 0x2C, [0x06])

time.sleep(0.5)

logging.info("sensor_home - read data")
# Read data back from 0x00(00), 6 bytes
# cTemp MSB, cTemp LSB, cTemp CRC, Humididty MSB, Humidity LSB, Humidity CRC
data = bus.read_i2c_block_data(0x45, 0x00, 6)

# Convert the data
sensor_home_temp = round(((((data[0] * 256.0) + data[1]) * 175) / 65535.0) - 45, 2)
sensor_home_humidity = round(100 * (data[3] * 256 + data[4]) / 65535.0, 2)
logging.info("sensor_home - temp: " + str(sensor_home_temp ))
logging.info("sensor_home - hum: " + str(sensor_home_humidity ))

########## Sensor BMP180 0x77 RADIATOR ###########
logging.info("------- sensor_radiator -------")
logging.info("sensor_radiator - read calibration data")
# BMP180 address, 0x77(119)
# Read data back from 0xAA(170), 22 bytes
data = bus.read_i2c_block_data(0x77, 0xAA, 22)

# Convert the data
AC1 = data[0] * 256 + data[1]
if AC1 > 32767 :
	AC1 -= 65535
AC2 = data[2] * 256 + data[3]
if AC2 > 32767 :
	AC2 -= 65535
AC3 = data[4] * 256 + data[5]
if AC3 > 32767 :
	AC3 -= 65535
AC4 = data[6] * 256 + data[7]
AC5 = data[8] * 256 + data[9]
AC6 = data[10] * 256 + data[11]
B1 = data[12] * 256 + data[13]
if B1 > 32767 :
	B1 -= 65535
B2 = data[14] * 256 + data[15]
if B2 > 32767 :
	B2 -= 65535
MB = data[16] * 256 + data[17]
if MB > 32767 :
	MB -= 65535
MC = data[18] * 256 + data[19]
if MC > 32767 :
	MC -= 65535
MD = data[20] * 256 + data[21]
if MD > 32767 :
	MD -= 65535

time.sleep(0.5)

logging.info("sensor_radiator - send temperature measure command")
# BMP180 address, 0x77(119)
# Select measurement control register, 0xF4(244)
#		0x2E(46)	Enable temperature measurement
bus.write_byte_data(0x77, 0xF4, 0x2E)

time.sleep(0.5)

logging.info("sensor_radiator - read temperature data")
# BMP180 address, 0x77(119)
# Read data back from 0xF6(246), 2 bytes
# temp MSB, temp LSB
data = bus.read_i2c_block_data(0x77, 0xF6, 2)

# Convert the data
temp = data[0] * 256 + data[1]

logging.info("sensor_radiator - send pressure measure command")
# BMP180 address, 0x77(119)
# Select measurement control register, 0xF4(244)
#		0x74(116)	Enable pressure measurement, OSS = 1
bus.write_byte_data(0x77, 0xF4, 0x74)

time.sleep(0.5)

logging.info("sensor_radiator - read pressure data")
# BMP180 address, 0x77(119)
# Read data back from 0xF6(246), 3 bytes
# pres MSB1, pres MSB, pres LSB
data = bus.read_i2c_block_data(0x77, 0xF6, 3)

# Convert the data
pres = ((data[0] * 65536) + (data[1] * 256) + data[2]) / 128

# Callibration for Temperature
X1 = (temp - AC6) * AC5 / 32768.0
X2 = (MC * 2048.0) / (X1 + MD)
B5 = X1 + X2
sensor_radiator_temp = ((B5 + 8.0) / 16.0) / 10.0

# Calibration for Pressure
B6 = B5 - 4000
X1 = (B2 * (B6 * B6 / 4096.0)) / 2048.0
X2 = AC2 * B6 / 2048.0
X3 = X1 + X2
B3 = (((AC1 * 4 + X3) * 2) + 2) / 4.0
X1 = AC3 * B6 / 8192.0
X2 = (B1 * (B6 * B6 / 2048.0)) / 65536.0
X3 = ((X1 + X2) + 2) / 4.0
B4 = AC4 * (X3 + 32768) / 32768.0
B7 = ((pres - B3) * (25000.0))
pressure = 0.0
if B7 < 2147483648 :
	pressure = (B7 * 2) / B4
else :
	pressure = (B7 / B4) * 2
X1 = (pressure / 256.0) * (pressure / 256.0)
X1 = (X1 * 3038.0) / 65536.0
X2 = ((-7357) * pressure) / 65536.0
sensor_radiator_pressure = round((pressure + (X1 + X2 + 3791) / 16.0) / 100, 2)

# Calculate Altitude
sensor_radiator_altitude = 44330 * (1 - ((sensor_radiator_pressure / 1013.25) ** 0.1903))

logging.info("sensor_radiator - Altitude: " + str(sensor_radiator_altitude))
logging.info("sensor_radiator - Pressure: " + str(sensor_radiator_pressure))
logging.info("sensor_radiator - Temperature: "+ str(sensor_radiator_temp))

if(args.measure != True):
    ############### CONFIGURATION FILE ###############
    logging.info("------- Configuration -------")
    try:
        with open(args.cfg_file) as config_file:
            config = json.load(config_file)
            config_DB = config["database"]
            logging.info("Load configuration file - SUCCESSFULL")
    except Exception as e:
        logging.exception("Load configuration file - ERROR: " + str(e))
        logging.info("-------------- END ---------------")
        exit(2)

    ##################### DATABASE ###################

    logging.info("------- Database -------")
    try:
        #Connect to DB
        connection = mysql.connector.connect(
            host = config_DB["host"],
            user=config_DB["user"],
            passwd=config_DB["passwd"],
            database=config_DB["database"],
            port= config_DB["port"]
        )
        logging.info("Connection to SQL database - SUCCESSFULL")

        cursor = connection.cursor()

        # Sensor SHT30 0x45 HOME
        logging.info("SQL: INSERT INTO meteo_sensor_home - START" ) 
        mySql_insert_query = """ INSERT INTO meteo_sensor_home (TIMESTAMP, temp, hum) VALUES (UTC_TIMESTAMP(), %s, %s) """  
        cursor.execute(mySql_insert_query, (sensor_home_temp, sensor_home_humidity))
        logging.info("SQL: INSERT INTO meteo_sensor_home - SUCCESSFULL")

        # Sensor BMP180 0x77 RADIATOR
        logging.info("SQL: INSERT INTO meteo_sensor_radiator - START" ) 
        mySql_insert_query = """ INSERT INTO meteo_sensor_radiator (TIMESTAMP, temp, press, alt) VALUES (UTC_TIMESTAMP(), %s, %s, %s) """  
        cursor.execute(mySql_insert_query, (sensor_radiator_temp, sensor_radiator_pressure, sensor_radiator_altitude))
        logging.info("SQL: INSERT INTO meteo_sensor_radiator - SUCCESSFULL")
        
        connection.commit()
        
    except Exception as e:
        logging.exception("SQL database - ERROR: " + str(e))
        if (connection.is_connected()):
            connection.close()
            logging.info("MySQL connection is closed")
        logging.info("-------------- END ---------------")
        exit(3)


    if (connection.is_connected()):
        cursor.close()
        connection.close()
        logging.info("MySQL connection is closed")


logging.info("-------------- END ---------------")
exit(1)