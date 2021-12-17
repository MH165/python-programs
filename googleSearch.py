import sys
import webbrowser
 
ARGS = sys.argv

if(len(ARGS)<2):
    sys.stderr.write(f"Error: Usage ==> {ARGS[0]} WORD ")
    sys.stderr.flush()
else:
    query = ARGS[1]
    webbrowser.open(f"https://google.com/search?q={query}")