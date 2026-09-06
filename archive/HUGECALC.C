/* This is the enhanced hugecalc program (c version) originally from
   PC Magazine 24 Sep 91. */

/* to do

make a list of enhancements ...

   accept negative numbers -- done

   accept floating point numbers -- +, -, *, /, ^, /  done
      need  ^ for decimal exponets (root).    done

      / for floating point division is done, but it messes up if hctol > 1700
      there really isn't any check in dividef for the case of the variables
      like ans from being too long--i'm not sure what the problem is

      the problem with floating point division doesn't seem to be a problem
      any longer -- probably due to switching over to using malloc calls
      instead of huge arrays

   convert to BCD (refer to magazine article)

   add other functions (sin, cos, tan, etc.)

*/

/* ok, here are the current comments...
   - convert long to unsigned long (may have to change the elaborate number-
     checking done for the TOL variable

--- decided not to convert long to unsigned long, since there are some
    functions which return a long.  besides, this would only double the
    current capacity from 2^31 to 2^32.  a truly unlimited capacity would
    deal in strings only--no long or unsigned long variables.  this would
    entail an extensive overhaul.

   - convert addchar and subchar to asm funtions utilizing the command line
     option to create an assembly listing
     -- then compile these as separate functions and link them to hugecalc
	and calc
     -- do before and after checks to see improvement
   - for unlimited length of arguments and answer (unlimited hctol, for
     example), all the long variables need to be changed to strings
   - all defines and hctol should be eventually be read in from a config file
     -- this would enable the maxsize of strings to be changed without re-
	compiling
     -- it would just be better all around -- but this would entail a lot of
	coding
*/





#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <io.h>

#include "calc.h"

/* Global variables */

char *op, *operand1 = "", *operand2= "", *result, *rem, operation;
char *operand2f="", *resultf;
char *tolstr;   /* Used to store the HCTOL environment variable value */

int minus1 = FALSE, minus2 = FALSE;

long decimal1 = 0, decimal2 = 0, TOL;

FILE *HCFILE;

char *helpmessage = \
"Enter 'HC ## op ##', where op is +, -, *, /, or ^\n\
   or 'HC ## !' for factorial.\n\n\
Use decimal point with / for decimal division or no decimal points\n\
   for integer division.\n\n\
For decimal operations, the DOS environment variable, HCTOL, is used to\n\
   set the number of significant digits to display.\n\
   SET HCTOL=100 for 100 significant digits.  If HCTOL is not found a\n\
   default tolerance of 25 is used.\n";

/* Function declarations */

   /* calc functions */

char addchar(const char c1, const char c2, int *carry);
char subchar(const char c1, const char c2, int *borrow);
void fillchar(char *s, char c, long n);
void leftpad0(char *s, long len);
void rightpad0(char *s, long zeros);
long trimlead0(char *s);
void trimtrail0(char *s);
int compare(char *x, char *y);
void add(char *a, char *b, char *ans);
void sub(char *a, char *b, char *ans);
void prod(char *a, char *b, char *ans);
void divide(char *a, char *b, char *ans, char *rm);
void fact(char *a, char *ans);
void power(char *b, char *e, char *ans);
void dividef(char *a, char *b, char *ans, long *decans);
void powerf(char *b, char *e, char *ans, long *decans);
void output_binary(unsigned bit);
void dec2bin(char *d);
void square_root(const char *c, const long dec_c, char *ans, long *decans);
long strcmp_count(const char *a, const char *b);

   /* hugecalc functions */

int allnums(char *a);
int istolvalue(char *a);
int gotparams(int argc, char *argv[]);
int addcomma(char *s);
int decimalcheck(void);
void adddecimal(char *s, long place);



main(int argc, char *argv[])
{
char *opswap, *r2, *two = "2"; /* , *end; */
long i, longnumber, decans;

if((op = malloc((MAXSIZE)*sizeof(char))) == NULL)
{
   printf("Not enough memory for op\n");
   exit(1);
}
if((operand1 = malloc((MAXSIZE)*sizeof(char))) == NULL)
{
   printf("Not enough memory for operand1\n");
   exit(1);
}
if((operand2 = malloc((MAXSIZE)*sizeof(char))) == NULL)
{
   printf("Not enough memory for operand2\n");
   exit(1);
}
if((operand2f = malloc((MAXSIZE)*sizeof(char))) == NULL)
{
   printf("Not enough memory for operand2f\n");
   exit(1);
}
if((result = malloc((MAXSIZE)*sizeof(char))) == NULL)
{
   printf("Not enough memory for result\n");
   exit(1);
}
if((resultf = malloc((MAXSIZE)*sizeof(char))) == NULL)
{
   printf("Not enough memory for resultf\n");
   exit(1);
}
if((rem = malloc((MAXSIZE)*sizeof(char))) == NULL)
{
   printf("Not enough memory for rem\n");
   exit(1);
}
if((r2 = malloc((MAXSIZE)*sizeof(char))) == NULL)
{
   printf("Not enough memory for r2\n");
   exit(1);
}

if((tolstr = getenv("HCTOL")) == NULL)
   TOL = DEFAULTTOL;
else
{
   longnumber = ((long)sizeof(long)*1024*1024*256 - 1)*2 + 1;

   if(!istolvalue(tolstr))   /* Check if HCTOL is only digits and not zero */
   {
      printf("Error with DOS environment variable HCTOL.\n\
HCTOL can only be composed of digits (0-9) in the range of 1 to %li\n",\
longnumber);
      exit(1);
   }
   TOL = atol(tolstr);
}

if(!gotparams(argc, argv)) exit(1);

if(!decimalcheck())
{
   printf(helpmessage);
   exit(1);
}

start:;

switch (operation)
{
   case '+':
   {
      if(!minus1 && minus2)
      {
	 minus2 = FALSE;
	 operation = '-';
	 goto start;
      }
      if(minus1 && !minus2)
      {
	 opswap = operand1; operand1 = operand2; operand2 = opswap;
	 minus1 = FALSE;
	 operation = '-';
	 goto start;
      }
      /* Adjust the size of operand1 and operand2 with rightpad0
	 so each has the same number of decimal places. */

      if(decimal1 > decimal2) rightpad0(operand2, decimal1-decimal2);
      if(decimal2 > decimal1) rightpad0(operand1, decimal2-decimal1);

      if(_isatty(_fileno(stdout)))
      {
	 printf("       SUM: ");
	 add(operand1, operand2, result);
	 if(decimal1 > decimal2) adddecimal(result, decimal1);
	 if(decimal2 > decimal1) adddecimal(result, decimal2);
	 if(decimal1>0 && decimal1==decimal2) adddecimal(result, decimal1);
	 addcomma(result);
      }
      else
      {
	 add(operand1, operand2, result);
	 if(decimal1 > decimal2) adddecimal(result, decimal1);
	 if(decimal2 > decimal1) adddecimal(result, decimal2);
	 if(decimal1>0 && decimal1==decimal2) adddecimal(result, decimal1);
      }
      if(minus1 && minus2)
      {
	 if(strlen(result) < MAXSIZE_check)
	 {
	    for(i=strlen(result); i>=0; i--) *(result+i+1) = *(result+i);
	    *result = '-';
	 }
	 else
	 {
	    printf("MAXSIZE too small for minus sign in main.\n");
	    exit(1);
	 }
      }
      printf("%s\n", result); break;
   }
   case '-':
   {
      if(!minus1 && minus2)
      {
	 minus2 = FALSE;
	 operation = '+';
	 goto start;
      }
      if(minus1 && !minus2)
      {
	 minus2 = TRUE;
	 operation = '+';
	 goto start;
      }

      if(decimal1 > decimal2) rightpad0(operand2, decimal1-decimal2);
      if(decimal2 > decimal1) rightpad0(operand1, decimal2-decimal1);

      if(_isatty(_fileno(stdout)))
      {
	 printf("DIFFERENCE: ");
	 if(minus1 && minus2) sub(operand2, operand1, result);
	 else sub(operand1, operand2, result);
	 if(decimal1 > decimal2) adddecimal(result, decimal1);
	 if(decimal2 > decimal1) adddecimal(result, decimal2);
	 if(decimal1>0 && decimal1==decimal2) adddecimal(result, decimal1);
	 addcomma(result);
      }
      else
      {
	 if(minus1 && minus2) sub(operand2, operand1, result);
	 else sub(operand1, operand2,result);
	 if(decimal1 > decimal2) adddecimal(result, decimal1);
	 if(decimal2 > decimal1) adddecimal(result, decimal2);
	 if(decimal1>0 && decimal1==decimal2) adddecimal(result, decimal1);
      }
      printf("%s\n", result); break;
   }
   case '*':
   {
      if(_isatty(_fileno(stdout)))
      {
	 printf("   PRODUCT: ");
	 prod(operand1, operand2, result);
	 if(decimal1>0 || decimal2>0) adddecimal(result, decimal1+decimal2);
	 addcomma(result);
      }
      else
      {
	 prod(operand1, operand2, result);
	 if(decimal1>0 || decimal2>0) adddecimal(result, decimal1+decimal2);
      }
      if((!minus1 && minus2) || (minus1 && !minus2))
      {
	 if(strlen(result) < MAXSIZE_check)
	 {
	    for(i=strlen(result); i>=0; i--) *(result+i+1) = *(result+i);
	    *result = '-';
	 }
	 else
	 {
	    printf("MAXSIZE too small for minus sign in main.\n");
	    exit(1);
	 }
      }
      printf("%s\n", result); break;
   }
   case '/':
   {
      if(_isatty(_fileno(stdout)))
      {
	 printf(" QUOTIENT: ");
	 if(decimal1>0 || decimal2>0)
	 {
	    dividef(operand1, operand2, result, &decans);
	    if(decimal1<decimal2) rightpad0(result,(decimal2-decimal1));
	    else decans += (decimal1-decimal2);
	    adddecimal(result, decans);
	 }
	 else
	 {
	    divide(operand1, operand2, result, rem);
	 }
	 if((!minus1 && minus2) || (minus1 && !minus2))
	 {
	    if(strlen(result) < MAXSIZE_check)
	    {
	       for(i=strlen(result); i>=0; i--) *(result+i+1) = *(result+i);
	       *result = '-';
	    }
	    else
	    {
	       printf("MAXSIZE too small for minus sign in main.\n");
	       exit(1);
	    }
	 }
	 if(decimal1>0 || decimal2>0)
	 {
	    addcomma(result); printf("%s\n", result); break;
	 }
	 else
	 {
	    addcomma(result); printf("%s\n", result);
	    printf(" REMAINDER: ");
	    addcomma(rem); printf("%s\n", rem); break;
	 }
      }
      else
      {
	 if(decimal1>0 || decimal2>0)
	 {
	    dividef(operand1, operand2, result, &decans);
	    if(decimal1<decimal2) rightpad0(result,(decimal2-decimal1));
	    if(decimal1>decimal2) decans = decans + (decimal1-decimal2);
	 }
	 else
	 {
	    divide(operand1, operand2, result, rem);
	 }
	 adddecimal(result, decans);
	 if((!minus1 && minus2) || (minus1 && !minus2))
	 {
	    if(strlen(result) < MAXSIZE_check)
	    {
	       for(i=strlen(result); i>=0; i--) *(result+i+1) = *(result+i);
	       *result = '-';
	    }
	    else
	    {
	       printf("MAXSIZE too small for minus sign in main.\n");
	       exit(1);
	    }
	 }
	 printf("%s\n", result); break;
      }
   }
   case '!':
   {
      if(minus1)
      {
	 printf("Factorial is only valid for positive numbers.\n");
	 exit(1);
      }
      if(decimal1)
      {
	 printf("Factorial is only valid for integers.\n");
	 exit(1);
      }
      if(_isatty(_fileno(stdout)))
      {
	 printf(" FACTORIAL: ");
	 fact(operand1, result);
	 addcomma(result); printf("%s\n", result); break;
      }
      else
      {
	 fact(operand1, result);
	 printf("%s\n", result); break;
      }
   }
   case '^':
   {
      if(minus2)
      {
	 printf("Power is not setup for negative exponets.\n");
	 exit(1);
      }
      if(minus1 && decimal2)
      {
	 printf("Power is not setup to handle complex numbers.\n");
	 exit(1);
      }
      if(_isatty(_fileno(stdout)))
      {
	 printf("     POWER: ");
	 if(decimal2>0)
	 {
	    power(operand1, operand2, result);
	    powerf(operand1, operand2f, resultf, &decans);
	    prod(result, resultf, result);
	    if((decimal1 > 0) || decans)
	     adddecimal(result, decimal1*atol(operand2) + decans);
	 }
	 else
	 {
	    power(operand1, operand2, result);
	    if(decimal1 > 0)
	       adddecimal(result, decimal1*atol(operand2));
	 }
	 addcomma(result);
      }
      else
      {
	 if(decimal2>0)
	 {
	    power(operand1, operand2, result);
	    powerf(operand1, operand2f, resultf, &decans);
	    prod(result, resultf, result);
	    if((decimal1 > 0) || decans)
	     adddecimal(result, decimal1*atol(operand2) + decans);
	 }
	 else
	 {
	    power(operand1, operand2, result);
	    if(decimal1 > 0)
	       adddecimal(result, decimal1*atol(operand2));
	 }
      }
      if(minus1)
      {
	 divide(operand2, two, r2, rem);
	 if(*rem != '0')
	 {
	    if(strlen(result) < MAXSIZE_check)
	    {
	       for(i=strlen(result); i>=0; i--) *(result+i+1) = *(result+i);
	       *result = '-';
	    }
	    else
	    {
	       printf("MAXSIZE too small for minus sign in main.\n");
	       exit(1);
	    }
	 }
      }
      printf("%s\n", result); break;
   }
}
return 0;
}


/*  Hugecalc functions */

int allnums(char *a)
{
   char numbers[] = ".-0123456789";

   if(strspn(a,numbers) == strlen(a)) return 1;
   return 0;
}

int istolvalue(char *a)
{
/* This function checks to see if HCTOL (tolstr) is composed only of digits
   0-9 and is in the range of 1 to 2,147,483,647 */

   char numbers[] = "0123456789";

   if(strspn(a,numbers) == strlen(a))    /* just numbers */
      if(strlen(a) != strspn(a,"0"))     /* not zero */
	if(strlen(a) <= 9) return 1;
	else if(strlen(a) > 10) return 0;
	else
	   if((strncmp((a+0),"2",1) <= 0) &&
	      (strncmp((a+1),"1",1) <= 0) &&
	      (strncmp((a+2),"4",1) <= 0) &&
	      (strncmp((a+3),"7",1) <= 0) &&
	      (strncmp((a+4),"4",1) <= 0) &&
	      (strncmp((a+5),"8",1) <= 0) &&
	      (strncmp((a+6),"3",1) <= 0) &&
	      (strncmp((a+7),"6",1) <= 0) &&
	      (strncmp((a+8),"4",1) <= 0) &&
	      (strncmp((a+9),"7",1) <= 0)) return 1;
   return 0;
}

int gotparams(int argc, char *argv[])

/* PURPOSE : Returns true if parameters are correctly passed on the
    command line -- and assigns them to the correct variables if so. */

{
   char *operators = "!^*-+/";
   int b, paramcount, redir1 = FALSE, redir2 = FALSE;

   b = 2;
   paramcount = argc - 1;

   if(!_isatty(_fileno(stdin)))    /* stdin has been redirected */
   {
      fgets(op, MAXSIZE, stdin);
      if(*op == '-')
      {
	 minus1 = TRUE;
	 op++;
      }
      b--;

      /* now deterimine if op is just a number
	 or if it is a number operand number */

      if(strcspn(op, operators) == strlen(op))
      {
	 redir1 = TRUE;
	 redir2 = FALSE;
      }
      else
      {
	 redir1 = TRUE;
	 redir2 = TRUE;
      }
   }
   if(!redir1 && !redir2)     /* no redirect at all */
   {
      if(paramcount < b)
      {
	 printf("%s",helpmessage);
	 return 0;
      }
      strcpy(operand1, argv[1]);
      operation = *argv[b];
      
      // Only attempt to copy a second operand if one was provided
      if (paramcount > b) 
      {
          strcpy(operand2, argv[b+1]);
      }
   }
   else if(redir1 && !redir2)    /* operand1 is redirected, */
   {                             /* rest is from command line */
      strcpy(operand1, op);
      operation = *argv[b];
      strcpy(operand2, argv[b+1]);
   }
   else   /* all input is redirected */
   {
      b = 2;        /* reset b */

      strcpy(operand1, strtok(op, " "));
      if(strlen(operand1) != 0)
      {
	 if((operation = *strtok(NULL, " ")) !=  NULL)
	 {
	    if(operation == '!')
	    {
	       paramcount = 2;
	    }
	    else
	    {
	       paramcount = 3;
	       if((strcpy(operand2, strtok(NULL, "\n"))) == NULL)
	       {
		  printf("%s",helpmessage);
		  return 0;
	       }
	    }
	 }
	 else
	 {
	    printf("%s",helpmessage);
	    return 0;
	 }
      }
      else
      {
	 printf("%s",helpmessage);
	 return 0;
      }
   }
   if(!allnums(operand1))
   {
      printf("'%s' is not a positive integer.\n",operand1);
      return 0;
   }
   if(*operand1 == '-')
   {
      minus1 = TRUE;
      operand1++;
   }
   switch (operation)
   {
      case '!': break;
      case '^': ;
      case '*': ;
      case '-': ;
      case '+': ;
      case '/': ;
      {
	 if(paramcount < (b+1))
	 {
	    printf("The operator %c requires a second operand.", operation);
	    return 0;
	 }
	 if(!allnums(operand2))
	 {
	    printf("'%s' is not a valid number.\n",operand2);
	    return 0;
	 }
	 if(*operand2 == '-')
	 {
	    minus2 = TRUE;
	    operand2++;
	 }
	 break;
      }
      default :
      {
	 printf("Valid operations are +,-,*,/,^ and !\n");
	 return 0;
      }
   }
   return 1;
}

int addcomma(char *s)
{
   char ta[MAXSIZE], *t;
   long psn, minloc = 3;

   t = ta;

   if(strlen(s) == 0) return 0;   /* something is wrong */

   psn = strcspn(s, ".");
   if(*s == '-') minloc++;
   while((psn > minloc) && (strlen(s) < MAXSIZE_check))
   {
      psn = psn - 3;
      strcpy(t, (s+psn));
      *(s+psn) = ',';
      *(s+psn+1) = '\0';
      strcat(s, t);
   }
   return 1;
}

int decimalcheck(void)
{
   /* Check for decimal points in operand1 and operand2. */

   long d1=0, d2=0, len1, len2;
   register long i;

   len1 = strlen(operand1);
   len2 = strlen(operand2);

   d1 = strcspn(operand1, ".");
   d2 = strcspn(operand2, ".");

   if((d1+1) == len1)
   {
      rightpad0(operand1, 1);
      len1++;
   }
   if((d2+1) == len2)
   {
      rightpad0(operand2, 1);
      len2++;
   }

   decimal1 = len1 - d1 - 1;
   decimal2 = len2 - d2 - 1;

   if(operation == '^' && decimal2>0)
   {
/*      separate the two parts */
      strcpy(operand2f, operand2);
      *(operand2 + d2) = '\0';
      if(*operand2 == '\0')
	 *operand2 = '0'; *(operand2+1) = '\0';     /* set it equal to 0 */
   }

   /* now remove decimal point from operand1 and operand2
      and left shift the string (including the null character) */

   for(i=0; i<=decimal1; i++)
      *(operand1+len1-decimal1+i-1) = *(operand1+len1-decimal1+i);

   if((decimal2>0) && (operation=='^'))
      for(i=0; i<=decimal2; i++)
	 *(operand2f+i) = *(operand2f+i+d2+1);
   else
      for(i=0; i<=decimal2; i++)
	 *(operand2+len2-decimal2+i-1) = *(operand2+len2-decimal2+i);

   if(decimal1 == -1) decimal1 = 0;
   if(decimal2 == -1) decimal2 = 0;

   return 1;
}

void adddecimal(char *s, long place)
{
/* This function inserts a decimal point into the string s, place characters
   from the right. */

   long i;
   long len;

   len = strlen(s);

   if(place > len)
   {
      leftpad0(s, place);
      len = place;
   }

   for(i=0; i<=place; i++)
      *(s+len-i+1) = *(s+len-i);
   *(s+len-place) = '.';

   trimtrail0(s);  /* This function's purpose is to remove the trailing
		      zeros that sometimes occur due to the multiplication
		      method used in the hugecalc algorithm.  */
}
