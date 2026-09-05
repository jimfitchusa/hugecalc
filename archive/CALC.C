/* This is calc.c which contains the functions for use with hugecalc.c */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
/* #include <alloc.h> */

#include "calc.h"

/* Gobal variables */

extern long TOL;                 /* user specified tolerance value */
extern long decimal1, decimal2;  /* decimal places of operand1 and operand2 */

extern FILE *HCFILE;             /* input/output file for binary conversion */

unsigned one_flag, one_flag_set=0;

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
void square_root(const char *c,  const long dec_c, char *ans, long *decans);
long strcmp_count(const char *a, const char *b);

   /* hugecalc functions */

int allnums(char *a);
int istolvalue(char *a);
int gotparams(int argc, char *argv[]);
int addcomma(char *s);
int decimalcheck(void);
void adddecimal(char *s, long place);

char addchar(const char a, const char b, int *carry)
{
/* Adds one digit char ('0' thru '9') to another and reutrns the result as
   a digit.  Sets carry to true if appropriate. */

   char t;

   *carry = FALSE;

   t = a + b;
   if(t>105)             /* 48 + 48 + 9 = 105 */
   {
      t -= 10;
      *carry = TRUE;
   }

   return t-48;
}

char subchar(const char a, const char b, int *borrow)
{
/* Subtracts one digit char ('0' thru '9') from another and returns the
   result as a digit.  Sets borrow to true if appropriate. */

   int t;
   char tt;

   *borrow = FALSE;

   t = a - b;
   if(t<0)
   {
      t += 58;          /* add 48 plus the 'borrowed' 10 */
      *borrow = TRUE;
   }
   else
      t += 48;

   tt = t;

   return tt;

}

void fillchar(char *s, char c, long count)
{
/* This function is very similar to strnset, but it will set characters
   in the string beyond the null terminator.  This function will set the
   count + 1 position to '\0'.
*/
   long i;

   if((strlen(s) + count) > MAXSIZE_check)
   {
      printf("MAXSIZE too small in fillchar.\n");
      exit(1);
   }

   for(i=0; i<count; ++i) *(s+i) = c;
   *(s+count) = '\0';
}

void leftpad0(char *s, long len)
{
/* This function pads zeros to the left of string s, such that the length
   of string s is equal to len.  If the initial length of s is greater
   than len, s remains unchanged.

   This function assumes addiquate memory is allocated for s.
*/

   long i, s_length, diff;

   s_length = strlen(s);

   if (s_length < len)
   {
      diff = len - s_length;

      /* shift characters in s to right */
      for(i=s_length; i>=0; i--) *(s+diff+i) = *(s+i);

      /* insert zeros */
      for(i=0; i<diff; i++) *(s+i) = '0';
   }
}

long trimlead0(char *s)
{
   long p;

   if(!(p = strspn(s,"0"))) return 0;     /* s had no zeros */
   if(p == strlen(s))
   {
      *(s+1) = '\0';    /* s was all zeros */
      return p;
   }
   memmove(s, s+p, strlen(s+p) + 1);
   return p;
}

void rightpad0(char *s, long zeros)
{
/* This function pads 'zeros' number of zeros to the right of string s */

   long i, len;
   if((strlen(s) + zeros) > MAXSIZE_check)
   {
      printf("MAXSIZE too small in rightpad0.\n");
      exit(1);
   }
   len = strlen(s);
   for(i=0; i<zeros; i++) *(s+len+i) = '0';
   *(s+len+zeros) = '\0';
}

void trimtrail0(char *s)
{
   long p;

   /* First, reverse the charaters in the string.
      Then, trim the "leading" zeros.
      Last, reverse the trimmed resulting string. */

   _strrev(s);
   if(!(p = strspn(s,"0")))
   {
      _strrev(s);  /* reverse s back */
      return;     /* s had no zeros */
   }

   if(p == strlen(s))
   {
      *(s+1) = '\0';    /* s was all zeros */
      return;
   }
   strcpy(s, s+p);
   _strrev(s);
}

int compare(char *x, char *y)
{
/* returns -1 if x<y, 0 if x=y, 1 if x>y */
/* This algorithm assumes both x and y are positve "integers".  */

   trimlead0(x);
   trimlead0(y);
   if(strlen(x) ==  strlen(y))
   {
      if(!strcmp(x, y))
	 return 0;
      else
	 if(strcmp(x, y) > 0) return 1;
      else
	 return -1;
   }
   else
      if(strlen(x) > strlen(y))
	 return 1;
      else
	 return -1;
}

void add(char *a, char *b, char *ans)
{
   long psn, len;
   int carry=FALSE;
   char *t;

   if((t = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t in add\n");
      exit(1);
   }

   if((strlen(a) == 0) || (strlen(b) == 0))
   {
      printf("Argument in add is null.\n");
      exit(1);
   }
   trimlead0(a);
   trimlead0(b);
   if(strlen(a) > strlen(b)) len = strlen(a) + 1;
   else len = strlen(b) + 1;
   if(len > MAXSIZE_check)
   {
      printf("MAXSIZE too small in add.\n");
      exit(1);
   }
   leftpad0(a, len);
   leftpad0(b, len);
   fillchar(t, '0', len);
   psn = len;
   while(psn>1)
   {
      psn--;
      if(carry) *(t+psn) = addchar(*(a+psn)+1, *(b+psn), &carry);
      else *(t+psn) = addchar(*(a+psn), *(b+psn), &carry);
   }
   if(carry)
      *t = '1';
   else
      trimlead0(t);
   strcpy(ans, t);
   trimlead0(a);
   trimlead0(b);
   free(t);
}

void sub(char *a, char *b, char *ans)
{
   char *temp, *t, *tt;
   long psn, len;
   int borrow=FALSE, minus=FALSE;

   if((t = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t in sub\n");
      exit(1);
   }
   if((tt = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for tt in sub\n");
      exit(1);
   }

   if((strlen(a) == 0) || (strlen(b) == 0))
   {
      printf("Argument in sub is null.\n");
      exit(1);
   }

   if(compare(a, b) == -1)   /* subtract smaller from larger */
   {
      minus = TRUE;
      temp=a; a=b; b=temp;
   }
   trimlead0(a);
   trimlead0(b);
   len = strlen(a) + 1;
   if(len > MAXSIZE_check)
   {
      printf("MAXSIZE too small in sub.\n");
      exit(1);
   }
   leftpad0(a, len);
   leftpad0(b, len);
   fillchar(t, '0', len);
   psn = len;
   while(psn>1)
   {
      psn--;
      if(borrow) *(t+psn) = subchar(a[psn]-1, b[psn], &borrow);
      else *(t+psn) = subchar(a[psn], b[psn], &borrow);
   }
   trimlead0(t);
   if(*t == '\0')
   {
      *t     = '0';
      *(t+1) = '\0';
   }
   if(minus)
   {
      *tt = '-';
      *(tt+1) = '\0';
      if(strlen(t) < MAXSIZE_check)
      {
	 strcat(tt, t);
	 strcpy(ans, tt);
	 trimlead0(a);
	 trimlead0(b);
	 free(t);
	 free(tt);
	 return;
      }
      else
      {
	 printf("MAXSIZE too small in sub (minus).\n");
	 exit(1);
      }
   }
   strcpy(ans, t);
   trimlead0(a);
   trimlead0(b);
   free(t);
   free(tt);
}

void prod(char *a, char *b, char *ans)
{
   char *t1, *t2, *temp;
   long psn;
   int times, n;

   if((t1 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t1 in prod\n");
      exit(1);
   }

   if((t2 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t2 in prod\n");
      exit(1);
   }

   if((strlen(a)=='\0') || (strlen(b)=='\0'))
   {
      printf("Argument in prod is null.\n");
      exit(1);
   }
   if(compare(a, b) == -1)   /* multiply larger by smaller */
   {
      temp = a; a = b; b = temp;
   }
   *t2     = '0';
   *(t2+1) = '\0';
   /* For each digit of multiplier, right to left, add together an
      appropriate number of copies of muliplicand, tack the right number of
      zeroes on the end, and add the result to the running total in t2.
   */
   psn = strlen(b);
   while(psn)
   {
      psn--;
      times = *(b+psn) - 48;    /* ascii character to integer conversion */
      if(times == 0)
      {
	 *t1     = '0';
	 *(t1+1) = '\0';
      }
      else
      {
	 strcpy(t1, a);
	 for(n=2; n<=times; n++) add(t1, a, t1);
      }
      fillchar((t1+strlen(t1)), '0', (strlen(b)-psn-1));
      add(t2, t1, t2);
   }
   strcpy(ans, t2);
   free(t1);
   free(t2);
}

void divide(char *a, char *b, char *ans, char *rm)
{
   char *t1, *t2, *t3, *t4;

   if((t1 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t1 in divide\n");
      exit(1);
   }
   if((t2 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t2 in divide\n");
      exit(1);
   }
   if((t3 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t3 in divide\n");
      exit(1);
   }
   if((t4 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t4 in divide\n");
      exit(1);
   }

   if((strlen(a) == 0) || (strlen(b) == 0))
   {
      printf("Argument in divide is null.\n");
      exit(1);
   }

   if(strspn(b,"0") == strlen(b))
   {
      printf("Divide by zero error in divide.\n");
      exit(1);
   }
   if(compare(a, b) == 0)
   {
      *rm     = '0';
      *(rm+1) = '\0';
      *ans = '1';
      *(ans+1) = '\0';
      free(t1);
      free(t2);
      free(t3);
      free(t4);
      return;
   }

   strcpy(t4, a);
   strcpy(t1, b);
   *t2     = '1';
   *(t2+1) = '\0';
   *t3     = '0';
   *(t3+1) = '\0';
   /* While dividend is > t1, add zeroes to t1 and to t2. */
   while(compare(a, t1) == 1)
   {
      strcat(t1, "0");
      strcat(t2, "0");
   }
   /* Get the individual digits of the quotient by repeated subtraction of
      t1.  t1 is the divisor with a steadily decreasing number of zeroes
      after it. */

   while(compare(t1, b) != 0)
   {
      *(t1+strlen(t1)-1) = '\0';
      *(t2+strlen(t2)-1) = '\0';
      while(compare(t4, t1) != -1)
      {
	 sub(t4, t1, t4);
	 add(t3, t2, t3);
      }
   }
   strcpy(rm, t4);
   strcpy(ans, t3);
   free(t1);
   free(t2);
   free(t3);
   free(t4);
}

void fact(char *a, char *ans)
{
   char *t1, *t2, one[5], zero[5];

   if((t1 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t1 in fact\n");
      exit(1);
   }

   if((t2 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t2 in fact\n");
      exit(1);
   }

   *one = '1'; *(one+1) = '\0';
   *zero= '0'; *(zero+1)= '\0';

   *t1 = '1';
   *(t1+1) = '\0';
   *t2 = '1';
   *(t2+1) = '\0';

   if((compare(a,one) != 0) && (compare(a,zero) != 0))
   {
      while(compare(t2,a) != 0)
      {
	 add(t2, one, t2);
	 prod(t1, t2, t1);
      }
   }
   strcpy(ans, t1);
   free(t1);
   free(t2);
}

void power(char *b, char *e, char *ans)
{
   char *t1, *t2, *t3, *rm, two[5];

   if((t1 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t1 in power\n");
      exit(1);
   }

   if((t2 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t2 in power\n");
      exit(1);
   }
   if((t3 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t3 in power\n");
      exit(1);
   }

   if((rm = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for rm in power\n");
      exit(1);
   }

   *two = '2';
   *(two+1) = '\0';

   if((strlen(b) == 0) || (strlen(e) == 0))
   {
      printf("Argument in power is null.\n");
      exit(1);
   }

   if(strcmp(b,"0") == 0)
   {
      *ans = '0';
      *(ans+1) = '\0';
      free(t1);
      free(t2);
      free(t3);
      free(rm);
      return;
   }
   if(strcmp(e,"0") == 0)
   {
      *ans = '1';
      *(ans+1) = '\0';
      free(t1);
      free(t2);
      free(t3);
      free(rm);
      return;
   }

   strcpy(t1, b);
   strcpy(t2, e);
   strcpy(t3, "1");

   /* Calculate the power by halving and squaring */
   while((strcmp(t2,"0") != 0) && (strlen(t3) != 0))
   {
      /* Halve the exponet */
      divide(t2, two, t2, rm);

      /* If it was odd, multiply t3 by the current value of t1 */
      if(strcmp(rm, "1") == 0) prod(t3, t1, t3);

      /* Square t1 */
      prod(t1, t1, t1);
   }
   strcpy(ans, t3);
   free(t1);
   free(t2);
   free(t3);
   free(rm);
}

void dividef(char *a, char *b, char *ans, long *decans)
{
   char *t1, *tans, *rm;
   long zerocount= 0;

   if((t1 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t1 in dividef\n");
      exit(1);
   }

   if((tans = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for tans in dividef\n");
      exit(1);
   }

   if((rm = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for rm in dividef\n");
      exit(1);
   }

   if(strspn(b,"0") == strlen(b))
   {
      printf("Divide by zero error in dividef.\n");
      exit(1);
   }
   *decans = 0;
   if(compare(a, b) == 0)
   {
      *ans = '1';
      *(ans+1) = '\0';
      free(t1);
      free(tans);
      free(rm);
      return;
   }

   divide(a, b, ans, rm);

   strcpy(t1, rm);

   while(compare(ans,"0") == 0)
   {
      rightpad0(t1, 1);
      divide(t1, b, ans, rm);
      strcpy(t1,rm);
      zerocount++;
   }

   while((strspn(t1,"0")!=strlen(t1)) && (*decans<=TOL))
   {
      rightpad0(t1, 1);
      divide(t1, b, tans, rm);
      strcat(ans, tans);
      strcpy(t1, rm);
      (*decans)++;
   }
   trimlead0(ans);
   *decans = *decans + zerocount;
   free(t1);
   free(tans);
   free(rm);
}

void powerf(char *b, char *e, char *ans, long *decans)
{
   char *t1, two[5];
   long dec_t1;
   long i;
   unsigned bit;

   if((t1 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t1 in powerf\n");
      exit(1);
   }

   *two = '2'; *(two+1) = '\0';

   if((strlen(b) == 0) || (strlen(e) == 0))
   {
      printf("Argument in powerf is null.\n");
      exit(1);
   }

   if(strcmp(b,"0") == 0)
   {
      *ans = '0';
      *(ans+1) = '\0';
      free(t1);
      return;
   }
   if(strcmp(e,"0") == 0)
   {
      *ans = '1';
      *(ans+1) = '\0';
      free(t1);
      return;
   }

   dec2bin(e);     /*  convert exponent into binary form */

   /*       put in the logic in here

   form a loop here and do these things:
      before loop: position file pointer at end of hcfile
		   take square_root of base = t1
      in loop:read next (previous) binary digit in hcfile
	      if it's a 0, t1 = square_root(t3)
	      if it's a 1, t1 = t1*base; t1 = square_root(t1)
	 loop
   */

   if((HCFILE=fopen("hcfile", "r")) == NULL)
   {
      printf("Cannot open ouput file, HCFILE, in powerf.\n");
      exit(1);
   }

   square_root(b, decimal1, t1, &dec_t1);        /* initial t1 = sqrt(b) */
   i = -2;
   while(fseek(HCFILE, i, SEEK_END) == 0)    /* set the file pointer */
   {
      bit = getc(HCFILE);
      if(bit)
      {
	 prod(b, t1, t1);     /* t1 = b*t1 */
	 dec_t1 += decimal1;  /* add decimals of t1 and b */
	 square_root(t1, dec_t1, t1, &dec_t1);   /* t1 = sqrt(t1) */
      }
      else
	 square_root(t1, dec_t1, t1, &dec_t1);  /* t1 = sqrt(t1) */
   i--;
   }

   strcpy(ans, t1);
   *decans = dec_t1;
   free(t1);
   remove("hcfile");
}

void dec2bin(char *d)
{
   char *t1, two[5];
   long i, lead0s;
   long len1, len2, b_digits=0, max_b_digits=4L*TOL;

   if((t1 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t1 in dec2bin\n");
      exit(1);
   }

   *two = '2'; *(two+1) = '\0';

   if((HCFILE=fopen("hcfile", "w")) == NULL)
   {
      printf("Cannot open ouput file, HCFILE, in dec2bin.\n");
      exit(1);
   }

   lead0s = trimlead0(d);

   if(lead0s > TOL)
   {
      printf("HCTOL value is too small.\nlead0s = %il\nTOL = %il\n",
	      lead0s, TOL);
      exit(1);
   }

/* This is the first section which multiplies until there are no more leading
   zeros.
*/

   strcpy(t1, d);
   len1 = strlen(t1);
   while(lead0s)
   {
      prod(t1, two, t1);
      len2 = strlen(t1);
      if(len2 > len1)
      {
	 lead0s--;
	 /* In this initial section, don't increment counter, since
	    we haven't got any significant digits yet.
	 */
	 len1 = len2;
      }
      output_binary(0);
   }

   /* Now that lead0s = 0, continue with the main section. */

   while((b_digits<max_b_digits) && (strcmp(t1,"0")!=0))
   {
      prod(t1, two, t1);
      len2 = strlen(t1);
      if(len2 > len1)
      {
	 output_binary(1);
	 b_digits++;
         /* left shift answer one place */
	 for(i=0; i<len2; i++) *(t1+i) = *(t1+i+1);
      }
      else
      {
	 output_binary(0);
	 if(one_flag_set) b_digits++;  /* start incrementing counter once a
					  one has been output */
      }
      if((lead0s = trimlead0(t1)))
      {
	 len1 = strlen(t1);
	 while(lead0s && (strcmp(t1,"0")!=0))
	 {
	    prod(t1, two, t1);
	    len2 = strlen(t1);
	    if(len2 > len1)
	    {
	       len1 = len2;
	       lead0s--;
	    }
	    output_binary(0);
	    b_digits++;
	 }
      }
   }

/* The required number of binary digits have been obtained, but now we
   must ensure the last digit ends in a one (for the root algorithm).
*/

   if(!one_flag)    /* if last output was a zero */
   {
      if((lead0s = trimlead0(t1)) && (strcmp(t1,"0")!=0))
      {
	 len1 = strlen(t1);
	 while(lead0s)       /* get rid of any leading zero condition */
	 {
	    prod(t1, two, t1);
	    len2 = strlen(t1);
	    if(len2 > len1)
	    {
	       len1 = len2;
	       lead0s--;
	    }
	    output_binary(0);
	 }
      }
      while(!one_flag)    /* output zeros until a last one is obtained */
      {
	 prod(t1, two, t1);
	 len2 = strlen(t1);
	 if(len2 > len1)
	    output_binary(1);
	 else
	    output_binary(0);
      }
   }


   /* what is set up so far does not check for max_b_digits going out of
      limits when multiplied by 4.  it's a long variable and it does have
      a limitation.

      fix this with a condition on TOL/4 be less than (largets number/4)
      when we upgrade to using unsigned long declarations

      however, the maxsize of strings is the first limitation
      at this point in the development.  this will have to be stated as part
      of the limitations or later some error checking can be put into it.
   */


   fclose(HCFILE);
   free(t1);
}

void output_binary(unsigned bit)
{
   putc(bit, HCFILE);
   one_flag = bit;
   if(bit) one_flag_set = 1;
}

void square_root(const char *c, const long dec_c, char *ans, long *decans)
{
   char *x1, *x2, *t1, *t2, *t3, *cc, *rm, two[5], ten[6];
   long dec_x, dec_t1, dec_t2, dec_t3, dec_cc, len;
   long i, tt, ttt;
   unsigned not_done_yet = TRUE, minus;
   int count=0;

   if((x1 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for x1 in square_root\n");
      exit(1);
   }

   if((x2 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for x2 in square_root\n");
      exit(1);
   }

   if((t1 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t1 in square_root\n");
      exit(1);
   }

   if((t2 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t2 in square_root\n");
      exit(1);
   }

   if((t3 = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for t3 in square_root\n");
      exit(1);
   }

   if((cc = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for cc in square_root\n");
      exit(1);
   }

   if((rm = malloc((MAXSIZE)*sizeof(char))) == NULL)
   {
      printf("Not enough memory for rm in square_root\n");
      exit(1);
   }

   *two = '2'; *(two+1) = '\0';
   *ten = '1'; *(ten+1) = '0'; *(ten+2) = '\0';

/*
   Use Newton's method to compute the square root of a.
   f(x) = x^2 - c, where c is the number you want the square root of
		   and x (the answer) is the square root of c.
   f'(x) = 2x

   x(i+1) = x(i) - f(x)/f'(x)

   Applying algebra this reduces to:
   x(i+1) = x(i) + (c - x(i)^2)/(2x(i))
*/

   strcpy(cc, c);
   dec_cc = dec_c;

   trimlead0(cc);
   if(strcmp(cc, "0") == 0)            /* check if c = 0 */
   {
      *ans = '0'; *(ans+1) = '\0';
      *decans = 0;
   }

   /* initial guess: if single digit - guess = c
		     if multiple digits - guess = c/10 */

   if(strlen(cc) > 1)
   {
      divide(cc, ten, x1, rm);       /* if we're going to use divide by 10, then just do a set of \0 at strlen(cc)-1 */
      dec_x = dec_cc - 1;
   }
   else
   {
      strcpy(x1, cc);
      dec_x = dec_cc;
   }

   while(not_done_yet)
   {
      prod(x1, x1, t1);     /* t1 = x1^2 */
      dec_t1 = dec_x*2;  /* double the decimal places from squaring */

      /* Adjust the size of c and t1 with rightpad0
	 so each has the same number of decimal places. */

      if(dec_cc > dec_t1)
      {
	 rightpad0(t1, dec_cc-dec_t1);
	 dec_t1 = dec_cc;
      }
      if(dec_t1 > dec_cc)
      {
	 rightpad0(cc, dec_t1-dec_cc);
	 dec_cc = dec_t1;
      }

      sub(cc, t1, t1);       /* t1 = c - x1^2 */

      if(*t1 == '-')
      {
	 len = strlen(t1);
	 for(i=0; i<len; i++)    /* left shift answer one place */
	 {
	    *(t1+i) = *(t1+i+1);
	 }
	    minus = TRUE;
      }

      add(x1, x1, t2);     /* t2 = 2*x1 */

      dividef(t1, t2, t3, &dec_t3);  /* t3 = (c-x1^2)/(2*x1) */

      /* Note that dec_x = decimals for t2
	 dec_x is used here for efficiency */

      if(dec_t1 < dec_x)
	 rightpad0(t3, (dec_x - dec_t1));
      else
	 dec_t3 += (dec_t1 - dec_x);

      /* Adjust the size of x1 and t3 with rightpad0
	 so each has the same number of decimal places. */

      if(dec_x > dec_t3)
      {
	 rightpad0(t3, dec_x - dec_t3);
	 dec_t3 = dec_x;
      }
      if(dec_t3 > dec_x)
      {
	 rightpad0(x1, dec_t3 - dec_x);
	 dec_x = dec_t3;
      }

      if(minus)
      {
	 sub(x1, t3, x2);
	 minus = FALSE;
      }
      else
	 add(x1, t3, x2);    /* x2 = x1 + (c-x1^2)/(2*x1) */

      /* now, compare x1 and x2 to see if tolerance is met */

      if((tt=strcmp_count(x1, x2)) > TOL) not_done_yet = FALSE;

/*      if((ttt=strlen(x2)) > (TOL+5))
      {
	 dec_x -= (ttt-TOL-5);
	 *(x2+TOL+5) = '\0';
      }
*/

/*      if ((ttt=strlen(x2)) > (tt+20)) /* && (tt != 0) ) 
      {
	 dec_x -= (ttt-tt-20);
	 *(x2+tt+20) = '\0';
      }
*/
      if( ( (ttt=strlen(x2)) > (tt*2) )  && (tt != 0) )
	 if((tt*2) < (TOL+5))
	 {
	    dec_x -= (ttt - tt*2);
	    *(x2 + tt*2) = '\0';
	 }
	 else
	 {
	    dec_x -= (ttt-TOL-5);
	    *(x2+TOL+5) = '\0';
	 }

      count++;
      strcpy(x1, x2);
   }
   strcpy(ans, x1);
   *decans = dec_x;
   free(x1);
   free(x2);
   free(t1);
   free(t2);
   free(t3);
   free(cc);
   free(rm);
}

long strcmp_count(const char *a, const char *b)
{
/* This function determines the length in characters that string a matches
   string b, character for character.
*/

   long i=0, lena, lenb;

   lena = strlen(a);
   lenb = strlen(b);

   for(i=0; i<lena && i<lenb; i++) if(*(a+i) != *(b+i)) break;

   return i;
}

