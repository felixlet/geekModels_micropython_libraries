# main.py -- put your code here!
import euglena_board
board = euglena_board.Euglena_board()
board.connect_sta()

import euglena_script
iot = euglena_script.Euglena_pyscript()
iot.set_owner_uuid('a')

import ili9341
lcd = ili9341.get_m5_display()
import freesans20 as ff
lcd.text('ready!%s' % board.get_sta_ip(),10,10,font=ff)
#import euglena_port
#vg=euglena_port.Euglena_vguang_port()
#vg.init_auto_publish(0,600)
