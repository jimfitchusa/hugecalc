{$A+,B-,D-,E-,F+,G-,I+,L-,N-,O+,R-,S-,V-,X-}
UNIT Calc;
(**) INTERFACE (**)
   FUNCTION add(A, B : String) : String;
   FUNCTION sub(A, B : String) : String;
   FUNCTION prod(A, B : String) : String;
   FUNCTION divide(A, B : String; VAR Rm : String):String;
   FUNCTION fact(VAR A : String) : String;
   FUNCTION power(B, E : String) : String;
(**) IMPLEMENTATION (**)
   FUNCTION SubChar(C1, C2 : Char; VAR borrow : Boolean) : Char; Assembler;
   {Subtracts one digit char ('0' thru '9') from another and returns the
   result as a digit.  Sets borrow to true if appropriate.}
   ASM
      LES DI, Borrow
      MOV Byte Ptr ES:[DI], FALSE
      MOV AL, C1
      SUB AL, C2
      JGE @NoBorrow
      MOV Byte Ptr ES:[DI], TRUE
      ADD AL, 10
      @NoBorrow:
      ADD AL, 30h
   END;

   FUNCTION AddChar(C1, C2 : Char; VAR carry : Boolean) : Char; Assembler;
   {Adds one digit char ('0' thru '9') to another and reutrns the result as
    a digit.  Sets carry to true if appropriate.}
   ASM
      LES DI, Carry
      MOV Byte Ptr ES:[DI], FALSE
      MOV AL, C1
      ADD Al, C2
      SUB AL, 60h {30h for each digit}
      CMP AL, 10
      JL @NoCarry
      SUB AL, 10
      MOV Byte Ptr ES:[DI], TRUE
      @NoCarry:
      ADD AL, 30h
   END;

   FUNCTION LeftPad0(S : String; Len : Byte) : String;
   BEGIN
      IF length(S) < Len THEN
         BEGIN
            MOVE(S[1], S[succ(Len - length(S))], length(S));
            FillChar(S[1], Len - length(S), '0');
         END;
      S[0] := Char(Len);
      LeftPad0 := S;
   END;

   PROCEDURE TrimLead0(VAR S : String);
   VAR P : Byte;
   BEGIN
      P := 1;
      WHILE (S[P] = '0') AND (P <= length(S)) DO Inc(P);
      CASE P OF
         0 : S[0] := #0; {string was 255 of '0'!}
	 1 : ; {not found}
	 ELSE
	    Move(S[P], S[1], succ(length(S) - P));
	    Dec(S[0], pred(P));
      END;
   END;

   FUNCTION add(A, B : String) : String;
   VAR T     : String;
       psn   : Word;
       Len   : Byte;
       carry : Boolean;
   BEGIN
      add[0] := #0;
      IF (Length(A) >= 254) THEN Exit;
      IF (Length(B) >= 254) THEN Exit;
      IF A[0] = #0 THEN Exit;
      IF B[0] = #0 THEN Exit;
      carry := False;
      IF Length(A) > Length(B) THEN Len := Succ(Length(A))
      ELSE Len := Succ(Length(B));
      A := LeftPad0(A, Len);
      B := LeftPad0(B, Len);
      FillChar(T[1], Len, '0');
      T[0] := Char(Len);
      psn := Succ(Len);
      {add digits from right to left}
      WHILE psn > 1 DO
         BEGIN
	    Dec(psn);
	    IF carry THEN
               T[psn] := AddChar(succ(A[psn]), B[psn], carry)
	    ELSE T[psn] := AddChar(A[psn], B[psn], carry);
         END;
      IF carry THEN T[1] := '1';
      TrimLead0(T);
      IF T = '' THEN T := '0';
      add := T;
   END;

   FUNCTION Compare(X, Y : String) : ShortInt;
   {Returns -1 if X < Y, 0 if equal, 1 if X > Y}
   BEGIN
      TrimLead0(X);  { cut off any leading zeros }
      TrimLead0(Y);
      IF Length(X) = Length(Y) THEN
         BEGIN
            IF X = Y THEN Compare := 0
            ELSE IF X > Y THEN Compare := 1
            ELSE Compare := -1;
         END
      ELSE IF Length(X) > Length(Y) THEN Compare := 1
      ELSE Compare := -1;
   END;

   FUNCTION sub(A, B : String) : String;
   VAR T             : String;
       psn, Len      : Word;
       borrow, minus : Boolean;
   BEGIN
      sub[0] := #0;
      IF (Length(A) >= 254) THEN Exit;
      IF (Length(B) >= 254) THEN Exit;
      IF A[0] = #0 THEN Exit;
      IF B[0] = #0 THEN Exit;
      borrow := False;
      minus  := False;
      {subtract smaller from larger}
      IF Compare(A, B) = -1 THEN
         BEGIN
            minus := True;
            T := A; A := B; B:= T;
         END;
      IF Length(A) > Length(B) THEN Len := Succ(Length(A))
      ELSE Len := Succ(Length(B));
      A := Leftpad0(A, Len);
      B := LeftPad0(B, Len);
      FillChar(T[1], Len, '0');
      T[0] := Char(Len);
      psn := Succ(Len);
      {subtract digits from right to left}
      WHILE psn > 1 DO
         BEGIN
            Dec(psn);
            IF borrow THEN
               T[psn] := subChar(Pred(A[psn]), B[psn], borrow)
            ELSE T[psn] := subChar(A[psn], B[psn], borrow);
         END;
      TrimLead0(T);
      IF T = '' THEN T := '0';
      IF minus THEN
         BEGIN
            Move(T[1], T[2], length(T));
            T[1] := '-';
            Inc(T[0]);
            END;
      sub := T;
   END;

   FUNCTION prod(A, B : String) : String;
   VAR T1, T2         : String;
       posn, times, N : Word;
   BEGIN
      prod[0] := #0;
      IF (Length(A) + Length(B) > 254) THEN Exit;
      IF A[0] = #0 THEN Exit;
      IF B[0] = #0 THEN Exit;
      {multiply larger by smaller}
      IF Compare(A, B) = -1 THEN
         BEGIN
            T1 := A; A := B; B := T1;
         END;
      T2 := '0';
      {for each digit of multiplier, right to left, add together an
       appropriate number of copies of muliplicand, tack the right number of
       zeroes on the end, and add the result to the running total in T2}
      FOR posn := Length((B)) DOWNTO 1 DO
         BEGIN
            times := Ord(B[posn])-48;
            IF times = 0 THEN T1 := '0'
            ELSE
               BEGIN
                  T1 := A;
                  FOR N := 2 to times DO
                     T1 := add(T1, A);
               END;
            FillChar(T1[succ(length(T1))], length(B)-posn, '0');
            Inc(T1[0], length(B)-posn);
            T2 := add(T2, T1);
         END;
      prod := T2;
   END;

   FUNCTION divide(A, B : String; VAR Rm : String):String;
   VAR T1, T2, T3 : String;
   BEGIN
      divide[0] := #0;
      Rm[0] := #0;
      IF A[0] = #0 THEN Exit;
      IF B[0] = #0 THEN Exit;
      IF Compare(A, B) = 0 THEN
         BEGIN
            divide := '1';
            Rm := '0';
         END
      ELSE
         BEGIN
            T1 := B; T2 := '1'; T3 := '0';
            {While dividend is > T1, add zeroes to T1 and to T2}
            WHILE Compare(A, T1) = 1 DO
               BEGIN
                  Inc(T1[0]); T1[length(T1)] := '0';
                  Inc(T2[0]); T2[length(T2)] := '0';
               END;
            {get individual digits of quotient by repeated subtraction of T1.
             T1 is the divisor with a steadily decreasing number of zeroes
             after it.}
            WHILE Compare(T1, B) <> 0 DO
	       BEGIN
                  Dec(T1[0]);
                  Dec(T2[0]);
                  WHILE Compare(A, T1) <> -1 DO
                     BEGIN
                        A := sub(A, T1);
                        IF A[0] = #0 THEN Exit;
                        T3 := add(T3, T2);
                        IF T3[0] = #0 THEN Exit;
                     END;
               END;
            divide := T3;
            Rm := A;
         END;
   END;

   FUNCTION fact(VAR A : String) : String;
   VAR T1, T2 : String;
   BEGIN
      T1 := '1';
      T2 := '1';
      IF (A <> '1') AND (A <> '0') THEN
         WHILE (T2 <> A) AND (T1[0] <> #0) DO
            BEGIN
               T2 := add(T2, '1');
               T1 := prod(T1, T2);
            END;
      fact := T1;
   END;

   FUNCTION power(B, E : String) : String;
   VAR T1, T2, T3, Rem : String;
   BEGIN
      power[0] := #0;
      IF B[0] = #0 THEN Exit;
      IF E[0] = #0 THEN Exit;
      power := '0';
      IF B = '0' THEN Exit;
      power := '1';
      IF E = '0' THEN Exit;
      T1 := B;
      T2 := E;
      T3 := '1';
      {calculate power by halving and squaring}
      WHILE (T2 <> '0') AND (T3[0] <> #0) DO
         BEGIN
            {halve the exponet}
            T2 := divide(T2, '2', rem);
            {if it was odd, multiply T3 by current value of T1}
            IF rem = '1' THEN
            T3 := prod(T3, T1);
            {square T1}
            T1 := prod(T1, T1);
         END;
      power := T3;
   END;
END.
