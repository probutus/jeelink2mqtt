#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# simple python server written by Karl Ranzeyer
# created: October 10, 2020
#
#  first and only mod: 2019-03-11

import time
import json
import serial
import re
import paho.mqtt.client as mqtt

output = False           # write everthing into out.dat
logoutput = False       # print out debugging messages
longoutput = True      # just print (on screen) telegram without EMS bus parameters
skipknown = True        # skip known telegram in out.dat (good to investigate unknown telegram)

serialport = '/dev/ttyUSB0'
logfile = '/home/pi/out.dat'
mqtt_broker = 'raspberrypi'
mqtt_port=1883
topic = ''
topic_base = 'home/sensor/lacrosse/'

my_list_devices = { 
   33: 'Room1',
   42: 'Room2',
   17: 'Room3'
}

ser = serial.Serial(
 port=serialport,
 baudrate = 57600,
 parity=serial.PARITY_NONE,
 stopbits=serial.STOPBITS_ONE,
 bytesize=serial.EIGHTBITS,
 timeout=1
)

def on_publish(client,userdata,result):             #create function for callback
    #print("data published \n")
    pass

if output:
    f = open(logfile, 'a+')

mqtt_client= mqtt.Client("control1",clean_session=False)                           #create client object
mqtt_client.on_publish = on_publish                          #assign function to callback
# mqtt_client.username_pw_set("user","pass") 
mqtt_client.connect(mqtt_broker,mqtt_port)                                 #establish connection


while 1:
    line = ser.readline()
    try:
        line = line.encode().decode('utf-8')
    except AttributeError:
        line = line.decode('utf-8')
    re_reading = re.compile(r'OK (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)')

    match = re_reading.match(line)
    if match:
        data = [int(c) for c in match.group().split()[1:]]
        sensorid = data[1]
        sensortype = data[2] & 0x7f
        new_battery = True if data[2] & 0x80 else False
        temperature = float(data[3] * 256 + data[4] - 1000) / 10
        humidity = data[5] & 0x7f
        low_battery = True if data[5] & 0x80 else False
        
        outstr = 'id=' + str(sensorid) + ' sensortype ' + str(sensortype) + ' temp ' + str(temperature) + ' humidity ' + str(humidity) + ' lowbat ' + str(low_battery) + ' nbat ' + str(new_battery)
        if sensorid in my_list_devices:
           sensorname = my_list_devices[sensorid]
        else:
           sensorname = "unknown" + str(sensorid)

        json_telegram = {
           'name': sensorname,
           'sensor_id': '{0:d}'.format(sensorid) + "",
           'sensortype':'{0:d}'.format(sensortype) + "",
           'temperature': '{0:0.1f}'.format(temperature) + "",
           'humidity': '{0:d}'.format(humidity) + "",
           'low_battery': '{0:0.1f}'.format(low_battery) + "",
           'new_battery': '{0:0.1f}'.format(new_battery) + "",
        }
        topic = topic_base + sensorname

        content = json.dumps(json_telegram)
#        print(topic)
#        print(json_telegram)

        if output:
            f.write(outstr + '\n')

        if logoutput:
            print (outstr)
    # after header check: Now send telegram
        ret= mqtt_client.publish(topic,content)
        topic=''
        content=''
        if ret.rc > 0:
            mqtt_client.reconnect()

