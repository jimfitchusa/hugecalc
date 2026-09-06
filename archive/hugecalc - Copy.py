"""
12 Nov 2025
Looking at hugecalc again, but now looking to convert the C program into a Python script.

I'm taking this one tiny step at a time and using Gemini AI to assist.

First, get the script to parse the command line input into operand1, operator, operand2.

Second, start with just the add operation, with the assumption that operand1 and operand2 are both nonnegative integers.


"""


import sys


helpmessage = 
"""Enter 'HC ## op ##', where op is +, -, *, /, or ^\n\
   or 'HC ## !' for factorial.\n\n\
Use decimal point with / for decimal division or no decimal points\n\
   for integer division.\n\n\
For decimal operations, the DOS environment variable, HCTOL, is used to\n\
   set the number of significant digits to display.\n\
   SET HCTOL=100 for 100 significant digits.  If HCTOL is not found a\n\
   default tolerance of 25 is used.\n
"""

global operand1, operation, operand2

def usage();
    print( helpmessage )


def checkArgs():
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)

    operand1 = sys.argv[1]
    operation = sys.argv[2]
    operand2 = sys.argv[3]


def add( operand1, operation, operand2 ):
    # todo: write add function



if __name__ == "__main__":
    checkArgs()
    add( operand1, operand2 )



