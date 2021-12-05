import webbrowser


def YouTube():
    webbrowser.open("https://youtube.com",2)

def Google():
    webbrowser.open("https://google.com",2)

def Facebook():
    webbrowser.open("https://facebook.com",2)

def Twitter():
    webbrowser.open("https://twitter.com",2)
    
def Other():
    domain = input("Domain: ")
    url = f"https://{domain}"
    webbrowser.open(url,2)

if __name__=="__main__":
    print("""
    #########################################
    #Type (1) for Google                    #
    #Type (2) for YouTube                   #
    #Type (3) for Facebook                  #
    #Type (4) for Twitter                   #
    #Type (5) for Other WEBSITE to visit... #
    #########################################  
    """)
    print("You can choose more than one site.")
    try:
        #digit = int(input("Your Choices: "))
        INPUT = map(int,input("Your Choice: ").split())
        for digit in list(INPUT):
            if(digit>=1 and digit<=5):
                if(digit==1):
                    Google()
                elif(digit==2):
                    YouTube()
                elif(digit==3):
                    Facebook()
                elif(digit==4):
                    Twitter()
                elif(digit==5):
                    Other()
            else:
                print("Plase Type a number between (1) to (5)")
                break
    except TypeError:
        print("Plase Type a number between (1) to (5)")
    except ValueError:
        print("Plase Type a valid number...")



