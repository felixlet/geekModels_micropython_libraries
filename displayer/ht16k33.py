import euglena_port
import ubinascii

HT16K33_CMD_BRIGHTNESS = const(0xE0)
HT16K33_BLINK_CMD      = const(0x80)
HT16K33_BLINK_DISPLAYON= const(0x01)
HT16K33_BLINK_OFF      = const(0x00)
HT16K33_BLINK_2HZ      = const(0x01)
HT16K33_BLINK_1HZ      = const(0x02)
HT16K33_BLINK_HALFHZ   = const(0x03)


"""
    ++bit0++
    +      +
   bit5   bit1
    ++bit6++
    +      +
   bit4   bit2
    ++bit3++    +bit7
"""
segment_font = [0b00111111, #0
        0b00000110, #1
        0b01011011, #2
        0b01001111, #3
        0b01100110, #4
        0b01101101, #5
        0b01111101, #6
        0b00000111, #7
        0b01111111, #8
        0b01101111, #9

        0b01110111, #A
        0b01111100, #B
        0b00111001, #C
        0b01111100, #D
        0b01111001, #E
        0b01110001, #F
        0b01000000, #Err
     ]

class ht16k33():
    def __init__(self,port,addr=0x70):
        ep = euglena_port.Euglena_port(port)
        self.i2c = ep.i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.display = bytearray(16)
        self.init()

    def write_cmd(self,cmd):
        self.temp = bytearray(1)
        self.temp[0] = cmd
        self.i2c.start()
        self.i2c.writeto(self.addr,self.temp)
        self.i2c.stop()
    
    def set_blink(self,b):
        if b >3:
            b = HT16K33_BLINK_DISPLAYON
        else:
            b = (2 * b) + HT16K33_BLINK_DISPLAYON
        self.write_cmd(HT16K33_BLINK_CMD | b)

    def set_brightness(self,b):
        b = b & 0x0f
        self.write_cmd(HT16K33_CMD_BRIGHTNESS | b)
    
    def show_display(self):
        self.temp = bytearray(17)
        self.temp[0] = 0x00
        for i in range(16):
            self.temp[i+1] = self.display[i]
        
        self.i2c.start()
        self.i2c.writeto(self.addr,self.temp)
        self.i2c.stop()

    def write_display(self,pos,int_data):
        offset = pos * 2
        self.display[offset] = int_data
        self.display[offset + 1] = 0

    def init(self):
        self.write_cmd(0x21)             ##turn on oscillator
        self.set_blink(HT16K33_BLINK_OFF)##turn off blink
        self.set_brightness(15)          ##Max brightness
        self.display = bytearray(16)      ##clean display

    def write_number(self,number,blink=0,brightness=15):
        i = 0
        number_str = str(number).upper()
        for c in number_str[:5]:
            if c == '.':
                continue

            index =  int(ubinascii.hexlify(bytearray(c))) - 30
            try: 
                font_data = segment_font[index]
            except:
                font_data = segment_font[-1]

            try:
                next_char = number_str[i+1] 
            except:
                next_char = ''
            
            if next_char == '.':
                self.write_display(i,font_data + 0x80)
            else:
                self.write_display(i,font_data)
            i  = i+1
        
        self.set_blink(blink)
        self.set_brightness(brightness)
        self.show_display()

