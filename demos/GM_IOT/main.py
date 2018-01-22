# main.py -- put your code here!
import euglena_board
board = euglena_board.Euglena_board()
try:
    board.connect_sta()
    init_info = 'ready!\n%s' % board.get_sta_ip()
except Exception as ex:
    init_info = 'Please reset\n%s' % str(ex)

import euglena_script
iot = euglena_script.Euglena_pyscript()
iot.init()

import ili9341
#lcd = ili9341.get_m5_display()
import freesans20 as ff
#lcd.text(init_info,10,10,font=ff)

