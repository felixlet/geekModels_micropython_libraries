#encoding=utf8
import time
import socket
import json
import network
from machine import Timer
from machine import reset

import euglena_board
import ht16k33

import pycom

# (date(2000, 1, 1) - date(1970, 1, 1)).days * 24*60*60  946684800
#UX_DELTA = 946684800

class SZJCSM_WIFI_AUTH(object):
    def __init__(self,o_port):
        self.ws = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.code = ""
        self.code_expire = 0
        self.ht16k33 = ht16k33.ht16k33(o_port)
        config_dict = euglena_board.Euglena_get_board_config_js()
        self.host  = config_dict.get("wifi_auth_host","")
        self.token = config_dict.get("wifi_auth_token","")
        #self.dog = Timer(-1)
        #self.dog.init(period=45000, mode=Timer.ONE_SHOT, callback=self._dog_reset)
        #self.led = PWM(Pin(14))
    
    def config_host_ip(self,o_ip):
        config_dict = euglena_board.Euglena_get_board_config_js()
        config_dict['wifi_auth_host'] = o_ip
        euglena_board.Euglena_save_board_config_js(config_dict)

    def config_device_token(self,o_token):
        config_dict = euglena_board.Euglena_get_board_config_js()
        config_dict['wifi_auth_token'] = o_token
        euglena_board.Euglena_save_board_config_js(config_dict)

    def reflash_numbers(self,arg):
        print(self.code)
        self.ht16k33.write_number(self.code)

    def led_err(self):    
        pycom.beatcolor(0x500000)

    def led_ok(self):
        pycom.beatcolor(0x005000)

    def _get_lan_ip(self):
        return network.WLAN().ifconfig()[0]

    def make_connection(self):
        self.ws.connect((self.host,8080))
        self.ws.settimeout(15)
    
    def _dog_reset(self,t):
        print("Dog will reset the machine.")
        #reset()

    def _write_msg(self,msg):
        #self.led_ok()
        self.ws.send(msg)

    def _feed_dog(self):
        pass
        #self.dog.deinit()
        #self.dog.init(period=45000, mode=Timer.ONE_SHOT, callback=self._dog_reset)

    def send_headbeat(self):
        post_dict = {
                    "to":"hw_router",
                    "from":"hw_client",
                    "target_ip":self.host,
                    "target_token":'',
                    "origin_token":self.token,
                    "active":"headbeat",
                    'timestamp':int(time.time()),
                    "data":self._get_lan_ip(),
                }

        post_str = json.dumps(post_dict) + " END"
        try:
            self._write_msg(post_str.encode())
        except Exception as ex:
            pass
            ##self.led_err()

    def send_ack(self,msg):
        ack_dict ={
                    "to":msg['from'],
                    "from":"hw_client",
                    "target_ip":self.host,
                    "target_token":msg['origin_token'],
                    "origin_token":self.token,
                    "active":"ack",
                    'timestamp':int(time.time()),
                    "data":"",
                }
        post_str = json.dumps(ack_dict) + " END"
        try:
            self._write_msg(post_str.encode('utf-8'))
        except Exception:
            pass
            ##self.led_err()

    def keep_online(self):
        self.send_headbeat()   
        try:
            msg = self.ws.recv(1024)
            parsed = json.loads(msg[:-4].decode('utf-8'))
            if parsed['active'] == 'ack':
                timestamp = int(parsed['timestamp'])
                if  timestamp > self.code_expire:
                    mpy_time  = time.localtime(int(parsed['timestamp']) + 28800)
                    self.code = "%02d%02d0" % (mpy_time[3],mpy_time[4])
                    self.code_expire = int(parsed['timestamp'])
                ##feed dog
                self._feed_dog()
        except Exception as ex:
            print(ex)
            self.led_err()
    
        try:
            msg =  self.ws.recv(1024)
            parsed = json.loads(msg[:-4].decode('utf-8'))
            timestamp = int(parsed['timestamp'])
            if parsed['from'] == 'django_server' and parsed['active'] == 'msg':
                self.send_ack(parsed)
                msg_data = json.loads(parsed['data'])
                self.code = "%04d1" % int(msg_data['code'])
                self.code_expire = int(msg_data['expire'])
                print("code:****,delay:%s seconds" % int(self.code_expire - timestamp))
        except Exception as ex:
            print(ex)
            pass
    
        return

if __name__ == "__main__":	
    cl = wifi_auth()
    cl.make_connection()
    while True:
        cl.keep_online()
        
