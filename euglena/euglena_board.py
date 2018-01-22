from machine import I2C,SD
import json
from network import WLAN
import time
import os

EUGLENA_INNER_I2C =  I2C(0,pins=("G26","G16"),mode=I2C.MASTER)
class BQ_24195(object):
    def __init__(self):
        self.addr = 107
        self.i2c  = EUGLENA_INNER_I2C
    
    def is_online(self):
        return (self.addr in self.i2c.scan())
    
    def is_power_goods(self):
        reg = self.i2c.readfrom_mem(self.addr,8,1)[0]
        if reg & 0x4 == 0x4:
            return True
        else:
            return False
    
    def set_watchdog_timer(self,max_feed_second):
        reg = self.i2c.readfrom_mem(self.addr,5,1)[0]
        reg= reg & 0xcc
        if max_feed_second >=40:
            reg = reg | 0x10
        elif max_feed_second > 80:
            reg = reg | 0x20
        else:
            reg = reg | 0x30
        self.i2c.writeto_mem(self.addr,5,reg.to_bytes(1))
    
    def feed_dog(self):
        reg = self.i2c.readfrom_mem(self.addr,1,1)[0]  
        reg = reg | 0x40
        self.i2c.writeto_mem(self.addr,1,reg.to_bytes(1))
        return 
    
    def get_chage_status(self):
        reg = self.i2c.readfrom_mem(self.addr,8,1)[0]
        reg = (reg & 0x30) >> 4
        return ['Not charging','Pre-charge','Fast charge','Charge Done'][reg]

    def enable_otg(self):
        reg = self.i2c.readfrom_mem(self.addr,1,1)[0]  
        reg = reg | 0x30
        self.i2c.writeto_mem(self.addr,1,reg.to_bytes(1))
        return 

    def disable_otg(self):
        reg = self.i2c.readfrom_mem(self.addr,1,1)[0]
        reg = reg & 0xcf
        reg = reg | 0x10
        self.i2c.writeto_mem(self.addr,1,reg.to_bytes(1))
        return
    
    def reset_registers(self):
        reg = self.i2c.readfrom_mem(self.addr,1,1)[0]
        reg = reg | 0x80
        self.i2c.writeto_mem(self.addr,1,reg.to_bytes(1))
        return

class Euglena_board(object):
    def get_config_js(self):
        try:
            config_file = open('\config\euglena.config','r')
            config_str = config_file.readall()
            config_file.close()
            try:
                config_json = json.loads(config_str)
            except ValueError:
                config_json = {}
        except OSError:
            config_json = {}
        return config_json

    def save_config_js(self,config_dict):
        config_str = json.dumps(config_dict)
        config_file = open("\config\euglena.config",'wr')
        config_file.write(config_str)
        config_file.close()

    def get_mqtt_account(self):
        config_dict = self.get_config_js()
        return {'username':config_dict.get("mqtt_username"),'password':config_dict.get("mqtt_password")}

    def set_mqtt_account(self,u,p):
        config_dict = self.get_config_js()
        config_dict['mqtt_username'] = u
        config_dict['mqtt_password'] = p
        self.save_config_js(config_dict)
    
    def set_mqtt_host(self,u):
        config_dict = self.get_config_js()
        config_dict['mqtt_host'] = u
        self.save_config_js(config_dict)

    def get_mqtt_host(self):
        config_dict = self.get_config_js()
        return config_dict.get("mqtt_host","")
    
    def set_mqtt_remote_username(self,u):
        config_dict = self.get_config_js()
        config_dict['mqtt_remote_username'] = u
        self.save_config_js(config_dict)

    def get_mqtt_remote_username(self):
        config_dict = self.get_config_js()
        return config_dict.get("mqtt_remote_username","")

    def config_sta_ssid(self,o_ssid):
        config_dict = self.get_config_js()
        config_dict['sta_ssid'] = o_ssid
        self.save_config_js(config_dict)

    def config_sta_pwd(self,o_pwd,auth_type):
        if auth_type not in ['WEP','WPA','WPA2']:
            raise Exception("bad auth type.avilable values:WEP,WPA,WPA2")
        config_dict = self.get_config_js()
        config_dict['sta_pwd'] = o_pwd
        config_dict['sta_auth_type'] = auth_type
        self.save_config_js(config_dict)

    def get_sta_config(self):
        d = self.get_config_js()
        print("STA ssid:%s\npwd:%s %s" %(d.get("sta_ssid",""),d.get("sta_ssid",''),d.get("sta_auth_type")))

    def connect_sta(self,time_out = 120):
        config_dict = self.get_config_js()
        sta_ssid    = config_dict.get("sta_ssid","")
        if len(sta_ssid) <= 0:
            raise Exception("sta ssid not configed")
        sta_pwd     = config_dict.get("sta_pwd","")
        if len(sta_pwd) <= 0:
            raise Exception("sta passworld not configed")
        sta_auth_type = config_dict.get("sta_auth_type","WPA2")

        if sta_auth_type == 'WEP':
            auth_type = 1
        elif sta_auth_type == 'WPA':
            auth_type = 2
        else:
            auth_type = 3
        wlan=WLAN()
        wlan.mode(3)
        wlan.connect(ssid=sta_ssid,auth=(auth_type,sta_pwd))
    
        time_out = int(time_out)
        while not wlan.isconnected():
            if time_out < 0:
                raise Exception("Connect wifi sta timeout")
            time.sleep(1)
            time_out = time_out - 1
    
        print(wlan.ifconfig())
        return

    def get_sta_ip(self):
        wlan = WLAN()
        return wlan.ifconfig()[0]

    def get_version_info(self):
        build = os.uname()[-2][-10:]
        return 'build:' + build

    def mount_microSD(self):
        try:
            microSD = SD()
        except OSError:
            return False

        try:
            os.mount(microSD,'/microSD')
        except OSError:
            return False
        return True

reflash_count = 0
euglena_oled  = None
def Euglena_reflash_info_oled(arg):
    try:
        import ssd1306
    except ImportError:
        return False
    global reflash_count 
    global euglena_oled
    reflash_count = reflash_count + 1
    if euglena_oled == None:
        try:
            euglena_oled = ssd1306.SSD1306_I2C(128,64,EUGLENA_INNER_I2C)
        except Exception:
            return False
    if euglena_oled == None:
        return False
    
    euglena_oled.fill(0)
    euglena_oled.text(" --GeekModels--",0,0)
    euglena_oled.text("Euglena Board",0,8)
    euglena_oled.text("www.github",0,16)
    euglena_oled.text(".com/felixlet",0,24)
    build_time = os.uname()[3][-10:]
    euglena_oled.text("build:%s" % build_time,0,32)
    euglena_oled.text(Euglena_get_sta_ip(),0,40)
    time.timezone(28800)
    lt = time.localtime()
    euglena_oled.text("%d-%d-%d %d:%d" % (lt[0],lt[1],lt[2],lt[3],lt[4]),0,48)
    bq=BQ_24195()
    euglena_oled.text(bq.get_chage_status(),0,56)
    euglena_oled.show()
    return True

