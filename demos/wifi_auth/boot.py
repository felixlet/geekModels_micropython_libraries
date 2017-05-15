# boot.py -- run on boot-up
from machine import Timer
import euglena_board
euglena_board.Euglena_connect_sta()
#Timer.Alarm(handler=euglena_board.Euglena_reflash_info_oled,s=1,ms=0,us=0,periodic=1)

#from machine import RTC
#rtc=RTC()
#rtc.ntp_sync('202.112.29.82')

