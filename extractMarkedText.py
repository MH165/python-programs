import fitz #pip3 install PyMuPDF
from fpdf import FPDF #pip3 install fpdf
import sys
import os
# you have to install all these module before using the program 
#note:
"""this program not working correctly with all pdf files """

# check if for the argument
def check(arg):
    if len(arg)==2:
        return True
    else:
        return False

# check if the file user specified is exists
def isEsists(file):
    if (os.path.exists(file)):
        return True
    else:
        return False

# get all co-ordenates of the hightlighted text in pdf
def getCoordenates(page):
    COOR_MARK = []
    annot = page.firstAnnot
    while annot:
        if(annot.type[0]==8):
            vertix = annot.vertices
            if(len(vertix)==4):
                COOR = fitz.Quad(vertix).rect
                COOR_MARK.append(COOR)
            else:
                vertix = [vertix[x:x+4] for x in range(0,len(vertix),4)]
                for vert in range(len(vertix)):
                    COOR = fitz.Quad(vertix[vert]).rect
                    COOR_MARK.append(COOR)
        annot = annot.next
    return COOR_MARK

# get co-ordenates of all text in the page and compares is with co-ordanates
# in hightlighted text 
def getText(coor,all_text):
    MARKED = []
    for C in coor:
        for x in all_text:
            if fitz.Rect(x[:4]).intersects(C):
                MATCH = x[4]
                MARKED.append(MATCH)
    TEXT = ' '.join(list(dict.fromkeys(MARKED)))
    return TEXT

# main function
def main():
    try:
        ARGS = sys.argv
        if not check(ARGS):
            sys.stderr.write(f"Error:Usage ==> {os.path.basename(ARGS[0])} FILE.pdf")
            sys.stderr.flush()
        else:
            if not isEsists(ARGS[1]):
                sys.stderr.write("Error:file not found check your path")
            else:
                # opend the pdf file
                doc = fitz.open(ARGS[1])
                #create pdf file to appned the result to it
                pdf = FPDF(format='a4')
                pdf.set_author('MH16')
                pdf.set_font('Arial','I',13)
                pdf.add_page()

                for page in doc:
                    all_text = page.get_text_words()
                    coor = getCoordenates(page)
                    txt = getText(coor,all_text)
                    # add all marked text to new pdf file
                    text2 = txt.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(200,9,txt=text2,align='l')

                #close and save pdf file 
                pdf.output('result.pdf')
                # check if the pdf file is empty
                if os.path.getsize('result.pdf')==0:
                    print("There is no marked text in your pdf")
                else:
                    print(f"file created in {os.path.abspath('result.pdf')} \n Thanks for using our program \
    (MH16)")
    except UnicodeEncodeError:
        print("Your pdf file not support!")
    

if __name__=='__main__':
    main()

