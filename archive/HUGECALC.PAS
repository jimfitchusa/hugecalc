{$A+,B-,D-,E-,F+,G-,I+,L-,N-,R-,S-,V-,X-}
{$M 16384, 0, 0}
PROGRAM HugeCalc;
USES Calc;
CONST Copyright : String[82] = 'HUGECALC 1.0, Copyright 1991 by '+
  'Neil J. Rubenking'#13#10'PC Magazine '#254' Neil J. Rubenking';

   FUNCTION AllNums(VAR A : String) : Boolean;
   VAR N : Byte;
   BEGIN
      AllNums := FALSE;
      FOR N := 1 to length(A) DO
         IF (A[N] < '0') OR (A[N] > '9') THEN Exit;
      AllNums := TRUE;
   END;

   FUNCTION IsDevice(VAR F : Text) : Boolean; Assembler;
   ASM
      MOV AH, 44h       {IOCTL function}
      MOV AL, 00h       {get device info subfunction}
      LES DI, F
      MOV BX, ES:[DI]   {handle in BX}
      INT 21h
      MOV AL, 0         {return value is false}
      JC @end
      TEST DX, 80h      {check is-device bit}
      JZ @end           {if NOT set, just end}
      INC AL            {return value is true}
      @end:
   END;

VAR op, opRand, result, rem : String;
    operation               : Char;

   FUNCTION GotParams : Boolean;
   {PURPOSE : Returns true if parameters are correctly passed on the
    command line -- and assigns them to the correct variables if so.}
   VAR S : String[1];
       B : Byte;
   BEGIN
      GotParams := FALSE;
      B := 2;
      IF (NOT IsDevice(Input)) AND NOT EOF(Input) THEN
         BEGIN
	    ReadLn(Op);
	    Dec(B);
	 END;
      IF Paramcount < B THEN
      BEGIN
         WriteLn(Copyright);
	 WriteLn('Enter "HC ## op ##", ',
	         'where op is +,-,*,/, or ^');
	 WriteLn('   or "HC ## !" for factorial');
	 Exit;
      END;
      IF B = 2 THEN op := ParamStr(1);
      IF NOT AllNums(op) THEN
         BEGIN
	    WriteLn(Copyright);
	    WriteLn('"',op,'" is not a positive integer.');
	    Exit;
	 END;
      S := ParamStr(B);
      operation := S[1];
      CASE operation OF
         '!' : ;
         '+', '-', '*', '/', '^' : BEGIN
            IF ParamCount < succ(B) THEN
	       BEGIN
	          WriteLn(Copyright);
	          WriteLn('The operator ', operation,
	                  'requires a second operand.');
	          Exit;
	       END;
	    Oprand := ParamStr(B+1);
	    IF NOT AllNums(OpRand) THEN
	       BEGIN
	          WriteLn(Copyright);
	          WriteLn('"',op,'" is not a positive integer.');
	          Exit;
	       END;
         END;
         ELSE
	    BEGIN
	       WriteLn(Copyright);
	       WriteLn('Valid operations are +,-,*,/, ! and ^');
	       Exit;
            END;
      END;
      GotParams := TRUE;
   END;

   FUNCTION AddComma(WW : String) : String;
   VAR posn, MinLoc : Word;
   BEGIN
      IF WW = '' THEN AddComma := '*ERROR*'
      ELSE
         BEGIN
            posn := succ(length(WW));
            MinLoc := 4;
            IF WW[1] = '-' THEN Inc(MinLoc);
            WHILE (posn > MinLoc) AND (length(WW) < 255) DO
               BEGIN
                  Dec(posn, 3);
                  Move(WW[posn],
                       WW[succ(posn)],
                       succ(length(WW) - posn));
                  WW[posn] := ',';
                  Inc(ww[0]);
               END;
            AddComma := WW;
         END;
   END;

BEGIN
   IF GotParams THEN
      BEGIN
         CASE operation OF
            '+' : BEGIN
                     IF IsDevice(Output) THEN
                        WRITE('       SUM: ');
                     result := add(op, opRand);
                     IF IsDevice(Output) THEN
                        WriteLn(AddComma(result))
                     ELSE WriteLn(Result);
                  END;
            '-' : BEGIN
                     IF IsDevice(output) THEN
                        WRITE('DIFFERENCE: ');
                     result := sub(op, opRand);
                     IF IsDevice(output) THEN
                        WriteLn(AddComma(result))
                     ELSE WriteLn(result);
                  END;
             '*' : BEGIN
                     IF IsDevice(Output) THEN
                        WRITE('   PRODUCT: ');
                     result := prod(op, opRand);
                     IF IsDevice(Output) THEN
                        WriteLn(AddComma(result))
                     ELSE WriteLn(Result);
                  END;
            '/' : BEGIN
                     IF IsDevice(output) THEN
                        WRITE('  QUOTIENT: ');
                     result := divide(op, opRand, rem);
                     IF IsDevice(output) THEN
                        BEGIN
                           WriteLn(AddComma(result));
                           Write(' REMAINDER: ');
                           WriteLn(AddComma(rem));
                        END
                     ELSE WriteLn(result);
                  END;
             '!' : BEGIN
                     IF IsDevice(Output) THEN
                        WRITE(' FACTORIAL: ');
                     result := fact(op);
                     IF IsDevice(Output) THEN
                        WriteLn(AddComma(result))
                     ELSE WriteLn(Result);
                  END;
            '^' : BEGIN
                     IF IsDevice(output) THEN
                        WRITE('     POWER: ');
                     result := power(op, opRand);
                     IF IsDevice(output) THEN
                        WriteLn(AddComma(result))
                     ELSE WriteLn(result);
                  END;
      END;
END;
END.




		
				
		
		





