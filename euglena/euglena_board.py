from machine import I2C
class BQ_24195(object):
    def __init__(self):
        self.addr = 107
        self.i2c  = I2C(0,pins=("G26","G16"),mode=I2C.MASTER)
    
    def is_active(self):
        return (self.addr in self.i2c.scan())
    
    def is_power_goods(self):
        reg = self.i2c.readfrom_mem(self.addr,8,1)[0]
        if reg & 0x4 == 0x4:
            return True
        else:
            return False
    
    def set_watchdog_timer(self,max_feed_second):
        reg = self.i2c.readfrom_mem(self.addr,8,1)[0]
        reg= reg & 0xcc
        if max_feed_second >=40:
            reg = reg | 0x10
        elif max_feed_second > 80:
            reg = reg | 0x20
        else:
            reg = reg | 30
        self.i2c.writeto_mem(self.addr,5,reg.to_bytes(1))
    
    def feed_dog(self):
        reg = self.i2c.readfrom_mem(self.addr,1,1)[0]  
        reg = reg | 0x40
        self.i2c.writeto_mem(self.addr,1,reg.to_bytes(1))
        return 
    
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
