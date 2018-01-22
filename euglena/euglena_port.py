from machine import Pin,PWM,I2C,UART
import struct
import json

__EUGLENA_PORT_DEFINE = (("G5","G17","G18","G19"),("G23","G22","G33","G32"),("G23","G22","G35","G34"),("G23","G22","G27","G25"))

class Euglena_port(object):
    def __init__(self,port_nu):
        self.type = None
        self.port_number = port_nu
        if port_nu > 3:
            return
        pins = __EUGLENA_PORT_DEFINE[port_nu]

        self.S1 = Pin(pins[2],mode=Pin.IN,pull=None)
        self.S2 = Pin(pins[3],mode=Pin.IN,pull=None) 
        if port_nu == 0:
            self.S3  = Pin(pins[0],mode=Pin.IN,pull=None)
            self.S4  = Pin(pins[1],mode=Pin.IN,pull=None)
        self.i2c = I2C(port_nu,pins=(pins[1],pins[0]),mode=I2C.MASTER)
        return

import time
class Euglena_hc(Euglena_port):
    def __init__(self,port_nu):
        super().__init__(port_nu)
        self.S2.pull(Pin.PULL_UP)
        self.last = 0

    def irq_handle(self,obj):
        div=time.ticks_us()
        print(div - self.last)
        self.S2.callback(0,None)

    def disctance(self):
        self.S1.mode(Pin.OUT)
        self.S1.value(0)
        time.sleep_ms(1)
        self.S1.value(1)
        time.sleep_ms(10)
        self.S1.value(0)
        self.S2.mode(Pin.IN)
        self.last = time.ticks_us()
        ##self.S2.callback(Pin.IRQ_HIGH_LEVEL,self.irq_handle,self)

class Euglena_ameba_port(Euglena_port):
    def __init__(self):
        super(Euglena_ameba_port,self).__init__(0)
        
        self.uart = UART(1,pins=(self.S2.id(),self.S1.id()),baudrate=115200)
        
        ##receive machine
        self.buffer = []
	self.bufferIndex = 0
	self.isParseStart = False
	self.exiting = False
	self.isParseStartIndex = 0
        self.parseResult = None
    
    def float2bytes(self,fval):
        return struct.pack("f",fval)

    def short2bytes(self,sval):
	return  struct.pack("h",sval)

    def clean_buffer(self):
        self.buffer = []
	self.bufferIndex = 0
	self.isParseStart = False
	self.exiting = False
	self.isParseStartIndex = 0
        self.parseResult = None

    def onParse(self,byte):
        position = 0
	value = None	
	self.buffer+=[byte]
	bufferLength = len(self.buffer)
	if bufferLength >= 2:
            ##frame head: 0x55 0xff
	    if (self.buffer[bufferLength-1]==0x55 and self.buffer[bufferLength-2]==0xff):
	        self.isParseStart = True
		self.isParseStartIndex = bufferLength - 2
            ##frame tail: 0x0d 0x0a
	    if (self.buffer[bufferLength-1] == 0xa and self.buffer[bufferLength-2]==0xd and self.isParseStart==True):
	        self.isParseStart = False
		position = self.isParseStartIndex+2
		extID = self.buffer[position]
		position+=1
		data_type = self.buffer[position]
		position+=1
		# 1 byte 2 float 3 short 4 len+string 5 double
		if data_type == 1:
		    value = self.buffer[position]
		if data_type == 2:
		    value = self.readFloat(position)
                    if(value<-255 or value>1023):
		        value = 0
		if data_type == 3:
		    value = self.readShort(position)
		if data_type == 4:
		    data_value = self.readString(position)
		if data_type == 5:
		    value = self.readDouble(position)
		if(data_type<=5):
		    ##self.responseValue(extID,value)
		    self.buffer = []
        self.parseResult = value
    
    def readFloat(self, position):
	v = [self.buffer[position], self.buffer[position+1],self.buffer[position+2],self.buffer[position+3]]
	return struct.unpack('<f', struct.pack('4B', *v))[0]
    
    def readShort(self, position):
	v = [self.buffer[position], self.buffer[position+1]]
	return struct.unpack('<h', struct.pack('2B', *v))[0]
    
    def readString(self, position):
        l = self.buffer[position]
	position+=1
	s = ""
	for i in Range(l):
	    s += self.buffer[position+i].charAt(0)
	return s

    def getUartResponseValue(self,time_out=1200):
        for i in range(0,time_out,20):
            try:
                for o_byte in self.uart.readall():
                    self.onParse(o_byte)
                if self.parseResult != None:
                    break
            except Exception:
                pass
            time.sleep_ms(20)
        v = self.parseResult
        self.clean_buffer()
        return v

    def readDouble(self, position):
        v = [self.buffer[position], self.buffer[position+1],self.buffer[position+2],self.buffer[position+3]]
	return struct.unpack('<f', struct.pack('4B', *v))[0]

    def responseValue(self, extID, value):
	self.__selectors["callback_"+str(extID)](value)

    def __writePackage(self,pack):
        self.uart.write(pack)

    def doRGBLed(self,index,port,slot,red,green,blue):
        self.__writePackage(bytearray([0xff,0x55,0x9,0x0,0x2,0x8,port,slot,index,red,green,blue]))
    
    def doRGBLedOnBoard(self,index,red,green,blue):
        self.doRGBLed(index,0x7,0x2,red,green,blue)   
    
    def doBuzzer(self,buzzer,time=0):
	self.__writePackage(bytearray([0xff,0x55,0x7,0x0,0x2,0x22]) + self.short2bytes(buzzer) + self.short2bytes(time))
    
    def doMotor(self,port,speed):
        self.__writePackage(bytearray([0xff,0x55,0x6,0x0,0x2,0xa,port]) + self.short2bytes(speed))

    def doMove(self,leftSpeed,rightSpeed):
        self.__writePackage(bytearray([0xff,0x55,0x7,0x0,0x2,0x5]) + self.short2bytes(-leftSpeed) + self.short2bytes(rightSpeed))

    def requestLineFollower(self,extID,port):
        self.uart.read()  ##clean the uart rx buff
	self.__writePackage(bytearray([0xff,0x55,0x4,extID,0x1,0x11,port]))
        return self.getUartResponseValue()
    
    def requestBlueUltrasonicSensor(self,exitID,port):
        self.uart.read()
	self.__writePackage(bytearray([0xff,0x55,0x4,exitID,0x1,0x62,port]))
        return s
	self.uart.read()
	self.__writePackage(bytearray([0xff,0x55,0x4,exitID,0x1,0x1,port]))
        return self.getUartResponseValue()
    
    def requestJoyStick(self,exitID,port,slot):
        self.uart.read()
	self.__writePackage(bytearray([0xff,0x55,0x4,exitID,0x1,0x5,port,slot]))
        return self.getUartResponseValue()
        
class Euglena_moto_port(Euglena_port):
    def __init__(self):
        super(Euglena_moto_port,self).__init__(0)
        moto_pwm  = PWM(0,5000)
        self.moto = {}
        self.S1.mode(Pin.OUT)
        self.S2.mode(Pin.OUT)
        self.S3.mode(Pin.OUT)
        self.S4.mode(Pin.OUT)
        self.moto['left_direction'] = self.S1
        self.moto['rigth_direction'] = self.S3
        self.moto['left_pwm'] = moto_pwm.channel(0,pin=self.S2.id(),duty_cycle=0)
        self.moto['right_pwm'] = moto_pwm.channel(1,pin=self.S4.id(),duty_cycle=0)
    
    def set_moto_speed(self,r,l):
        if self.moto == None:
            return
        if r > 0:
            self.moto['rigth_direction'].value(1)
        else:
            r = 0 - r
            self.moto['rigth_direction'].value(0)
        if l > 0:
            self.moto['left_direction'].value(0)
        else:
            self.moto['left_direction'].value(1)
            l = 0 -l

        self.moto['left_pwm'].duty_cycle(l / 1000)
        self.moto['right_pwm'].duty_cycle(r / 1000)
    
    def stop(self):
        self.moto['left_pwm'].duty_cycle(0)
        self.moto['right_pwm'].duty_cycle(0)
    
    def forward(self,speed):
        self.set_moto_speed(speed,speed)

    def retreat(self,speed):
        self.set_moto_speed(0 - speed,0 - speed)
    
    def turn_left(self,speed):
        self.set_moto_speed(speed,0 - speed)

    def turn_right(self,speed):
        self.set_moto_speed(0 - speed,speed)

class Euglena_line_port(Euglena_port):
    def __init__(self,port_nu):
        super(Euglena_line_port,self).__init__(port_nu)
        self.S1.mode(Pin.IN)
        self.S1.pull(Pin.PULL_UP)
        self.S2.mode(Pin.IN)
        self.S2.pull(Pin.PULL_UP)
        return
    
    def read(self):
        return  self.S2.value() << 1 | self.S1.value()
    
    def is_right_white(self):
        return self.S2.value()

    def is_left_white(self):
        return self.S1.value()

import network
def get_lan_ip():
    wlan = network.WLAN()
    return wlan.ifconfig()[0]

import mqtt
import os
import ubinascii
class Euglena_vguang_port(Euglena_port):
    def __init__(self):
        super(Euglena_ameba_port,self).__init__(0)
        self.uart = UART(1,pins=(self.S1.id(),self.S2.id()),baudrate=115200)
        from euglena_board import BQ_24195
        self.bq = BQ_24195()
        self.mqtt = None
        self.mqtt_username = None
        #self.bq.enable_otg(0)
        self.err_count = 0
        self.err = None
        return
    
    def pp(self):
        pass

    def init_mqtt(self):
        import euglena_board
        board         = euglena_board.Euglena_board()
        mqtt_account  = board.get_mqtt_account()
        self.mqtt     = mqtt.MQTT('esp32-' + ubinascii.hexlify(os.urandom(4)).decode())
        self.mqtt.username_pw_set(mqtt_account['username'],mqtt_account['password'])
        self.mqtt_username = mqtt_account['username']
        self.mqtt.on_message(self.pp)
        self.mqtt.connect_async(board.get_mqtt_host(),port=8882)
        self.mqtt.init()
    
    def mqtt_publish_single(self,arg):
        if self.mqtt == None:
            self.init_mqtt()
        try:
            out_s = self.uart.readall()
            if out_s!= None and len(out_s) > 0:
                self.mqtt.publish("redis/set/shop-data/%s" % self.mqtt_username,json.dumps({"expire":60,"data":out_s,"type":"barcode"}))
        except Exception as ex:
            self.mqtt = None ##reInint mqtt late
            self.err_count += 1
            self.err = str(ex)
            if self.err_count > 10:
                import machine
                machine.reset()
            return
    
    def mqtt_publish_status(self,arg):
        if self.mqtt == None:
            self.init_mqtt()
        try:      
            self.mqtt.publish("redis/set/machine-status/%s" % self.mqtt_username,json.dumps({"timestamp":int(time.time()),"lan_ip":get_lan_ip(),"expire":20}))
        except Exception as ex:
            self.err = str(ex)
            self.err_count += 1

    def read_single(self):
        self.bq.enable_otg(0)
        out_s = self.uart.readall()
        return out_s
    
    def __short2bytes(self,sval):
        return  struct.pack("h",sval)
    
    def get_command_pack(self,cmd,value,cmd_len=2):
        pack = bytearray([0x55,0xaa,cmd]) + self.__short2bytes(cmd_len) + bytearray([value])
        check=pack[0]
        for c in pack[1:]:
            check = c^ check 
        pack = pack + struct.pack('b',check)
        return pack

    def init_auto_publish(self,s,ms):
        from machine import Timer
        Timer.Alarm(handler=self.mqtt_publish_single,s=s,ms=ms,us=0,periodic=1)
        Timer.Alarm(handler=self.mqtt_publish_status,s=15,ms=0,us=0,periodic=1)

