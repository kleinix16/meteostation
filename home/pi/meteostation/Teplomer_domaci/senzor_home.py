#!/usr/bin/python

###############################################################################################################
######   Description:
######   Author: Tomas Klein
######   Created: 2020/04/11 21:09:50
######   Last modified: 2020/04/11 22:23:48
###############################################################################################################

import mysql.connector
import logging
import json

################################ PYTHON BASIC SETUP ###########################################################
#Logging to file
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
                    filemode='a',
                    filename="../logs/senzor_home.log"
                    )

#Logging to console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
###############################################################################################################

logging.info("-------------- START --------------")

#Load confguration file 
try:
    with open('../config.json') as config_file:
        config = json.load(config_file)
        config_DB = config["database"]
        logging.info("Load configuration file - SUCCESSFULL")
except Exception as e:
    logging.exception("Load configuration file - ERROR: ")
    logging.info("-------------- END ---------------")
    exit(2)

#Connect to DB
try:
    connection = mysql.connector.connect(
        host = config_DB["host"],
        user=config_DB["user"],
        passwd=config_DB["passwd"],
        database=config_DB["database"],
        port= config_DB["port"]
    )

    mycursor = connection.cursor()
    logging.info("Connection to SQL database - SUCCESSFULL")
except Exception as e:
    logging.exception("Connection to SQL database - ERROR: ")
    if (connection.is_connected()):
        connection.close()
    logging.info("-------------- END ---------------")
    exit(3)

mycursor = connection.cursor()