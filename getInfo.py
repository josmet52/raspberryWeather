#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import Adafruit_DHT

import subprocess 
import re 
import os 
import glob
import time 
import MySQLdb as mdb 
import datetime

databaseUsername="root"
databasePassword="mablonde" 
databaseName="WordpressDB" #do not change unless you named the Wordpress database with some other name

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28-000008a123a3')[0] # id external temperature sensor
device_file = device_folder + '/w1_slave'

sensor=Adafruit_DHT.DHT22 #if not using DHT22, replace with Adafruit_DHT.DHT11 or Adafruit_DHT.AM2302
pinNum=17 #if not using pin number 4, change here

def saveToDatabase(temperature,extTemp,humidity):

        con=mdb.connect("localhost", databaseUsername, databasePassword, databaseName)
        currentDate=datetime.datetime.now().date()

        now=datetime.datetime.now()
        midnight=datetime.datetime.combine(now.date(),datetime.time())
        minutes=((now-midnight).seconds)/60 #minutes after midnight, use datead$

        
        with con:
                cur=con.cursor()
                
                cur.execute("INSERT INTO temperatures (temperature, humidity, dateMeasured, hourMeasured, pressure) \
                        VALUES (%s,%s,%s,%s, %s)",(temperature,humidity,currentDate, minutes, extTemp))

                print "Saved data"
                return "true"

def read_temp_raw():
	catdata = subprocess.Popen(['cat',device_file], 
	stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out,err = catdata.communicate()
	out_decode = out.decode('utf-8')
	lines = out_decode.split('\n')
	return lines

def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
#        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return round(temp_c,2) #, temp_f


def readInfo():

### begin of the 'added by jo area'
        
        temperatureExt = read_temp()
        
### end of the 'added by jo area'
        
        humidity, temperature = Adafruit_DHT.read_retry(sensor, pinNum)#read_retry - retry getting temperatures for 15 times
        humidity = round(humidity,1)
        temperature = round(temperature,1)
        
        print "Température bureau: %.1f °C" % temperature
        print "Température extérieure: %.1f °C" % temperatureExt
        print "Humidité bureau:    %s %%" % humidity

        if humidity is not None and temperature is not None:
                return saveToDatabase(temperature,humidity, temperatureExt) #success, save the readings
        else:
                print 'Failed to get reading. Try again!'
                sys.exit(1)


#check if table is created or if we need to create one
try:
        queryFile=file("createTable.sql","r")

        con=mdb.connect("localhost", databaseUsername,databasePassword,databaseName)
        currentDate=datetime.datetime.now().date()

        with con:
                line=queryFile.readline()
                query=""
                while(line!=""):
                        query+=line
                        line=queryFile.readline()
                
                cur=con.cursor()
                cur.execute(query)      

                #now rename the file, because we do not need to recreate the table everytime this script is run
                queryFile.close()
                os.rename("createTable.sql","createTable.sql.bkp")
        

except IOError:
        pass #table has already been created
        

status=readInfo() #get the readings
