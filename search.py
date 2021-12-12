import os
import sys

#Global variable
ARGU = sys.argv

def check():
    if len(ARGU)==3:
        return True
    else:
        return False

def isEsists(file):
    if (os.path.exists(file)):
        return True
    else:
        return False

def Lines(file):
    with open(file,'r') as f:
        lines = f.readlines()
    lines = ''.join(lines)
    lines = lines.split('\n')
    return lines

def create():
    r= open('result.txt','w+')
    return r


def main():
    if not check():
        sys.stderr.write(f"Error:Usage {ARGU[0]} filename word ")
        sys.stderr.flush()
    else:
        if not isEsists(ARGU[1]):
            print("file not found,check the path!")
        else:
            result = create()
            FILE = ARGU[1]
            WORD = ARGU[2]
            for line in Lines(FILE):
                for pattren in line.split():
                    if pattren==WORD:
                        result.write(''.join(line)+'\n')
            result.close()
            filesize = os.path.getsize('result.txt')
            if(filesize==0):
                print(f"{WORD} not found!")
            else:
                print(f"file created in {os.path.abspath('result.txt')}")
        

if __name__=="__main__":
    main()


