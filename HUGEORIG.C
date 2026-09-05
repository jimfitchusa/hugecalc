/* This is the hugecalc program (c version) from PC Magazine 24 Sep 91) */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <io.h>

#define TRUE 1
#define FALSE 0
#define MAXSIZE 5000

/* Global variables */

char *op, *operand1 = "", *operand2= "", *result, *rem, operation;
char *helpmessage = \
"Enter 'HC ## op ##', where op is +,-,*,/,or ^\n\
   or 'HC ## !' for factorial\n";


main(int argc, char *argv[])
{
char *s, *x, *y, *rm, c;
int len, n;



/* Function declarations */

char *addchar(char c1, char c2, unsigned *carry);
char *subchar(char c1, char c2, unsigned *borrow);
void fillchar(char *s, char c, unsigned n);
void leftpad0(char *s, unsigned len);
void trimlead0(char *s);
int compare(char *x, char *y);
void add(char *a, char *b, char *ans);
void sub(char *a, char *b, char *ans);
void prod(char *a, char *b, char *ans);
void divide(char *a, char *b, char *rm, char *ans);
void fact(char *a, char *ans);
void power(char *b, char *e, char *ans);

int allnums(char *a);
int gotparams(int argc, char *argv[]);
int addcomma(char *s);

/* now add user interface */

if((op = malloc(MAXSIZE*sizeof(char))) == NULL)
{
   printf("Not enough memory for op\n");
   exit(1);
}
if((operand1 = malloc(MAXSIZE*sizeof(char))) == NULL)
{
   printf("Not enough memory for operand1\n");
   exit(1);
}
if((operand2 = malloc(MAXSIZE*sizeof(char))) == NULL)
{
   printf("Not enough memory for operand2\n");
   exit(1);
}
if((result = malloc(MAXSIZE*sizeof(char))) == NULL)
{
   printf("Not enough memory for result\n");
   exit(1);
}
if((rem = malloc(MAXSIZE*sizeof(char))) == NULL)
{
   printf("Not enough memory for rem\n");
   exit(1);
}

gotparams(argc, argv);

/* Start main program */

switch (operation)
{
   case '+':
   {
      if(_isatty(_fileno(stdout)))
      {
	 printf("       SUM: ");
	 add(operand1, operand2, result);
	 addcomma(result); printf("%s\n", result); break;
      }
      else
      {
	 add(operand1, operand2, result);
	 printf("%s\n", result); break;
      }
   }
   case '-':
   {
      if(isatty(fileno(stdout)))
      {
	 printf("DIFFERENCE: ");
	 sub(operand1, operand2, result);
	 addcomma(result); printf("%s\n", result); break;
      }
      else
      {
	 sub(operand1, operand2, result);
	 printf("%s\n", result); break;
      }
   }
   case '*':
   {
      if(isatty(fileno(stdout)))
      {
	 printf("   PRODUCT: ");
	 prod(operand1, operand2, result);
	 addcomma(result); printf("%s\n", result); break;
      }
      else
      {
	 prod(operand1, operand2, result);
	 printf("%s\n", result); break;
      }
   }
   case '/':
   {
      if(isatty(fileno(stdout)))
      {
	 printf("  QUOTIENT: ");
	 divide(operand1, operand2, rem, result);
	 addcomma(result); printf("%s\n", result);
	 printf(" REMAINDER: ");
	 addcomma(rem); printf("%s\n", rem); break;
      }
      else
      {
	 divide(operand1, operand2, rem, result);
	 printf("%s\n", result); break;
      }
   }
   case '!':
   {
      if(isatty(fileno(stdout)))
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
      if(isatty(fileno(stdout)))
      {
	 printf("     POWER: ");
	 power(operand1, operand2, result);
	 addcomma(result); printf("%s\n", result); break;
      }
      else
      {
	 power(operand1, operand2, result);
	 printf("%s\n", result); break;
      }
   }
}
return 0;
}

int allnums(char *a)
{
   char numbers[] = "0123456789";

   if(strspn(a,numbers) == strlen(a)) return 1;
   return 0;
}

int gotparams(int argc, char *argv[])

/* PURPOSE : Returns true if parameters are correctly passed on the
    command line -- and assigns them to the correct variables if so. */

{
   char *operators = "!^*-+/";
   int b, paramcount, needmore = TRUE, redir = FALSE;

   b = 2;
   paramcount = argc-1;

   if(!isatty(fileno(stdin)))    /* stdin has been redirected */
   {
      fgets(op, MAXSIZE, stdin);
      b--;
      needmore = FALSE;

      /* now deterimine if op is just a number
	 or if it is a number operand number */

      if(strcspn(op, operators) == strlen(op)) redir = TRUE;
   }
   if(needmore && !redir)
   {
      if(paramcount < b)
      {
	 printf("%s",helpmessage);
	 return 0;
      }
      strcpy(operand1, argv[1]);
      operation = *argv[b];
      strcpy(operand2, argv[b+1]);
   }
   else if(!needmore && redir)
   {
      strcpy(operand1, op);
      operation = *argv[b];
      operand2 = argv[b+1];
   }
   else   /* needmore is 0 and redir = 0 (all input is redirected) */
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
      exit(1);
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
	    printf("'%s' is not a positive integer.\n",operand2);
	    return 0;
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
   int psn, minloc = 3;

   t = ta;

   if(strlen(s) == 0) return 0;   /* something is wrong */

   psn = strlen(s);
   if(*s == '-') minloc++;
   while((psn > minloc) && (strlen(s) < MAXSIZE))
   {
      psn = psn - 3;
      strcpy(t, (s+psn));
      *(s+psn) = ',';
      *(s+psn+1) = '\0';
      strcat(s, t);
   }
   return 1;
}
