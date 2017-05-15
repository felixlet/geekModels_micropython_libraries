# main.py -- put your code here!
import ht16k33
import euglena_board
import wifi_auth
from machine import Timer
def main():
    cl = wifi_auth.SZJCSM_WIFI_AUTH(0)
    cl.make_connection()
    Timer.Alarm(cl.reflash_numbers,s=1,ms=0,us=0,periodic=1)
    while True:
        cl.keep_online()

if __name__ == '__main__':
    main()

