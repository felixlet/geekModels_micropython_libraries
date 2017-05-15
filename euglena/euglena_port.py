from machine import Pin,PWM,I2C,UART

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
    def __init__(self,port_nu):
        
        if port_nu not in [1,2]:
            raise Exception("%d port can't used as uart" % port_nu)

        super(Euglena_ameba_port,self).__init__(port_nu)
        self.uart = UART(port_nu,pins=(self.S2.id(),self.S1.id()),baudrate=115200)
    
    def __writePackage(self,pack):
        self.uart.write(pack)

    def doRGBLed(self,port,slot,index,red,green,blue):
        self.__writePackage(bytearray([0xff,0x55,0x9,0x0,0x2,0x8,port,slot,index,red,green,blue]))
    
    def doRGBLedOnBoard(self,index,red,green,blue):
        self.doRGBLed(0x7,0x2,index,red,green,blue)   
    
    def requestLineFollower(self,extID,port,callback):
        self.uart.read()  ##clean the uart rx buff
	self.__writePackage(bytearray([0xff,0x55,0x4,extID,0x1,0x11,port]))

                
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


