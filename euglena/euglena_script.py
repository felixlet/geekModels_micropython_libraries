import json

from machine import Timer

import mqtt
import os
import sys
import ubinascii
import time

pyscript_mqtt_client      = None
pyscript_mqtt_print_topic = None

def GM(_str):
    global pyscript_mqtt_print_topic
    global pyscript_mqtt_client 
    if pyscript_mqtt_client == None or pyscript_mqtt_print_topic == None:
        return
    _str = str(_str)
    pyscript_mqtt_client.publish(pyscript_mqtt_print_topic,_str)
    return

def sync_ntp_time():
    from machine import RTC
    rtc=RTC()
    rtc.ntp_sync('202.112.29.82')

import network
def get_lan_ip():
    wlan = network.WLAN()
    return wlan.ifconfig()[0]

class Euglena_pyscript(object):
    def __init__(self):
        import euglena_board
        global pyscript_mqtt_client
        board         = euglena_board.Euglena_board()
        mqtt_account  = board.get_mqtt_account()
        pyscript_mqtt_client = mqtt.MQTT('esp32-' + ubinascii.hexlify(os.urandom(4)).decode())
        self.mqtt = pyscript_mqtt_client
        self.mqtt.username_pw_set(mqtt_account['username'],mqtt_account['password'])
        self.mqtt_username = mqtt_account['username']
        self.remote_username = None
        
        ##self.mqtt.subscribe("pyscript/a/a/reults",0)
        self.mqtt.on_message(self.on_mqtt_message)
        self.mqtt.connect_async(board.get_mqtt_host(),port=8882)
        self.mqtt.init()
    
        Timer.Alarm(handler=self.mqtt_publish_status,s=15,ms=0,us=0,periodic=1)
        self.err = None
        self.err_count = 0

    def on_mqtt_message(self,topic,payload):
        print(topic)
        if '/script' in topic:
            self.run_pyscript(payload)
        if '/rpc' in topic:
            self.mqtt_rpc(payload)
    
    def mqtt_rpc(call_str):
        pass

    def run_pyscript(self,script):
        try:
            exec(script)
        except Exception as ex:
            GM(ex)
            self.err = ex
            self.err_count += 1

        GM("Done.\n")
        self.mqtt.publish("pyscript/%s/%s/status" %(self.mqtt_username,self.remote_username),json.dumps({"timestamp":int(time.time()),"done":True}))
        
    def mqtt_publish_status(self,arg):
        try:      
            self.mqtt.publish("pyscript/%s/%s/status"  % (self.mqtt_username,self.remote_username),json.dumps({"timestamp":int(time.time()),"lan_ip":get_lan_ip()}))
        except Exception as ex:
            self.err = str(ex)
            self.err_count += 1

    def set_owner_uuid(self,owner_uuid):   
        global pyscript_mqtt_print_topic 
        pyscript_mqtt_print_topic = 'pyscript/b/a/results'
        self.remote_username = owner_uuid
        print("pyscript/%s/%s/script" % (owner_uuid,self.mqtt_username))
        self.mqtt.subscribe("pyscript/%s/%s/script" % (owner_uuid,self.mqtt_username))

