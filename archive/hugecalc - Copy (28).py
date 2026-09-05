"""
12 Nov 2025
Looking at hugecalc again, but now looking to convert the C program into a Python script.

I'm taking this one tiny step at a time and using Gemini AI to assist.

First, get the script to parse the command line input into operand1, operator, operand2.
Second, implement addition and subtraction, including handling of negative inputs and results.
Third, implement result formatting (commas) and pipe/redirection detection for output.
Fourth, implement multiplication (huge_prod).
Fifth, implement integer division (huge_divide).
"""

"""
21 Aug 2026
Working to pick up something next -- perhaps floating point addition.

"""

import sys
import os

# ... HELPMESSAGE and VALID_OPERATORS ...

# Fetch the HCTOL environment variable, defaulting to 25 if not set.
# We wrap it in a try-except to ensure it falls back to 25 if the user
# accidentally sets it to something non-numeric like "apple".
try:
    HCTOL = int(os.environ.get('HCTOL', 25))
    if HCTOL < 1:
        HCTOL = 25
except ValueError:
    HCTOL = 25

# Internal working tolerance for calculation to prevent pipe drift
WORKING_TOL = HCTOL + 5

# Determine display format: 'DEC' (Decimal) or 'SCI' (Scientific)
HCFORMAT = os.environ.get('HCFORMAT', 'DEC').upper()
if HCFORMAT not in ('DEC', 'SCI'):
    HCFORMAT = 'DEC'

# Define the global help message
HELPMESSAGE = """\
Usage: python hugecalc.py <operand1> <operation> <operand2>
       (or use pipe: python hugecalc.py 1 + 2 | python hugecalc.py + 3)

Example: python hugecalc.py -123 + 456  (Addition with negative input)
Example: python hugecalc.py 100 - 50    (Subtraction)
Example: python hugecalc.py 123 * 45    (Multiplication)
Example: python hugecalc.py 100 / 3     (Integer Division)
Example: python hugecalc.py 100 !       (Integer Factorial)
Example: python hugecalc.py 3 ^ 12      (Integer Power)
Example: python hugecalc.py 3.1 ^ 0.2   (floating point power)
Example: python hugecalc.py -3.1 ^ 1/5  (Negative floating point base raised to odd rational power)
Example: python hugecalc.py sin 3.1     (sin of 3.1 radians)
Example: python hugecalc.py cos 3.1     (cos of 3.1 radians)

Supported operations: +, -, *, /, !, ^, sin, cos
"""

VALID_OPERATORS = ('+', '-', '*', '/', '!', '^', 'sin', 'cos', 'sind', 'cosd')


def usage():
    """Prints the usage/help message to stderr and exits."""
    # CHANGED: Print usage to stderr so it doesn't contaminate pipe output
    print(HELPMESSAGE, file=sys.stderr)
    sys.exit(1)


class HugeFloat:
    def __init__(self, val_str: str, sig_figs: int):
        self.sig_figs = sig_figs
        
        # Normalize the input string upon instantiation
        self.sign, self.mantissa, self.exponent = self._normalize(val_str)

    def _normalize(self, val_str: str) -> tuple[str, str, int]:
        """
        Reduces any numerical string into a sign, a pure stripped mantissa, 
        and a base-10 exponent. Limits the mantissa length to sig_figs.
        """
        val_str = val_str.lower().strip()
        
        # 1. Extract sign
        sign = '+'
        if val_str.startswith('-'):
            sign = '-'
            val_str = val_str[1:]
        elif val_str.startswith('+'):
            val_str = val_str[1:]
            
        # 2. Extract explicit scientific exponent
        explicit_exp = 0
        if 'e' in val_str:
            parts = val_str.split('e')
            val_str = parts[0]
            explicit_exp = int(parts[1])
            
        # 3. Remove decimal point and count decimal places
        dec_places = 0
        if '.' in val_str:
            parts = val_str.split('.')
            dec_places = len(parts[1]) if len(parts) > 1 else 0
            pure_digits = parts[0] + (parts[1] if len(parts) > 1 else "")
        else:
            pure_digits = val_str
            
        # 4. Strip leading zeros
        pure_digits = pure_digits.lstrip('0')
        if not pure_digits:
            return '+', '0', 0
            
        # 5. Strip trailing zeros and calculate shift
        original_len = len(pure_digits)
        mantissa = pure_digits.rstrip('0')
        trailing_zeros_removed = original_len - len(mantissa)
        
        # 6. Calculate true baseline exponent
        # Subtract decimal places (shifts decimal right)
        # Add trailing zeros removed (shifts magnitude back to the exponent)
        final_exponent = explicit_exp - dec_places + trailing_zeros_removed
        
        # 7. Apply Significant Figures limit (HCTOL)
        if len(mantissa) > self.sig_figs:
            excess_digits = len(mantissa) - self.sig_figs
            
            # Use the global _huge_round function to round the integer string
            mantissa = _huge_round(mantissa, excess_digits)
            
            # Slicing digits off the mantissa means the remaining digits represent
            # a higher magnitude, so we add the sliced count to the exponent.
            final_exponent += excess_digits
            
            # If rounding caused a cascade (e.g., 99 -> 100), strip the new trailing zeros!
            if mantissa.endswith('0'):
                new_len = len(mantissa)
                mantissa = mantissa.rstrip('0')
                final_exponent += (new_len - len(mantissa))
                
        return sign, mantissa, final_exponent

    def __mul__(self, other: 'HugeFloat') -> 'HugeFloat':
        """
        Overloads the * operator. 
        Multiplies mantissas, adds exponents, and calculates the final sign.
        """
        # 1. Handle edge case of multiplying by zero
        if self.mantissa == '0' or other.mantissa == '0':
            return HugeFloat('0', self.sig_figs)

        # 2. Determine the final sign (like an XOR gate)
        new_sign = '+' if self.sign == other.sign else '-'
        
        # 3. Multiply the pure integer mantissas using your core engine
        new_mantissa = huge_prod(self.mantissa, other.mantissa)
        
        # 4. Mathematically add the native integer exponents
        new_exponent = self.exponent + other.exponent
        
        # 5. Package as a raw scientific string to enforce normalization and sig_fig limits
        raw_val_str = f"{new_sign}{new_mantissa}e{new_exponent}"
        
        # 6. Return a brand new instantiated object
        return HugeFloat(raw_val_str, self.sig_figs)

    def __str__(self) -> str:
        """Overloads the string representation for clean printing."""
        if self.mantissa == '0':
            return '0'
            
        sign_str = '-' if self.sign == '-' else ''
        return f"{sign_str}{self.mantissa}e{self.exponent}"

    def to_sci_string(self) -> str:
        """Returns the value in standard normalized scientific notation."""
        if self.mantissa == '0':
            return '0e0'
            
        sign_str = '-' if self.sign == '-' else ''
        
        # Calculate standard scientific exponent (shift decimal to after first digit)
        sci_exp = self.exponent + len(self.mantissa) - 1
        
        if len(self.mantissa) > 1:
            sci_mantissa = self.mantissa[0] + '.' + self.mantissa[1:]
        else:
            sci_mantissa = self.mantissa
            
        return f"{sign_str}{sci_mantissa}e{sci_exp}"

    def to_dec_string(self) -> str:
        """Returns the value as a standard floating-point/integer string."""
        if self.mantissa == '0':
            return '0'
            
        sign_str = '-' if self.sign == '-' else ''
        
        if self.exponent == 0:
            return sign_str + self.mantissa
        elif self.exponent > 0:
            return sign_str + self.mantissa + ('0' * self.exponent)
        else:
            # Re-use your existing decimal insertion logic for negative exponents
            dec_places = abs(self.exponent)
            dec_mag = _insert_decimal(self.mantissa, dec_places)
            return sign_str + dec_mag

    def __truediv__(self, other: 'HugeFloat') -> 'HugeFloat':
        """
        Overloads the / operator (true division). 
        Divides mantissas, subtracts exponents, and calculates the final sign.
        """
        if other.mantissa == '0':
            raise ZeroDivisionError("Division by zero in HugeFloat.")
            
        if self.mantissa == '0':
            return HugeFloat('0', self.sig_figs)

        # 1. Determine the final sign (XOR logic)
        new_sign = '+' if self.sign == other.sign else '-'
        
        # 2. Divide mantissas using floating-point engine to get full precision
        new_mantissa, appended_decimals = _huge_dividef(self.mantissa, other.mantissa, self.sig_figs)
        
        # 3. Mathematically subtract the exponents, accounting for the appended decimals
        new_exponent = self.exponent - other.exponent - appended_decimals
        
        # 4. Package as a raw scientific string
        raw_val_str = f"{new_sign}{new_mantissa}e{new_exponent}"
        
        # 5. Return a brand new instantiated object (automatically applies HCTOL limits)
        return HugeFloat(raw_val_str, self.sig_figs)

    def __add__(self, other: 'HugeFloat') -> 'HugeFloat':
        """Overloads the + operator."""
        # 1. Machine Epsilon Shortcut: Skip math if scale difference exceeds precision
        exp_diff = self.exponent - other.exponent
        if abs(exp_diff) > self.sig_figs + 1:
            if self.exponent > other.exponent:
                return HugeFloat(f"{self.sign}{self.mantissa}e{self.exponent}", self.sig_figs)
            else:
                return HugeFloat(f"{other.sign}{other.mantissa}e{other.exponent}", self.sig_figs)
                
        # 2. Align Exponents (Pad the larger number's mantissa with zeros)
        target_exponent = min(self.exponent, other.exponent)
        pad_self = self.exponent - target_exponent
        pad_other = other.exponent - target_exponent
        
        aligned_self = self.mantissa + ('0' * pad_self)
        aligned_other = other.mantissa + ('0' * pad_other)
        
        # 3. Route the math based on signs
        if self.sign == other.sign:
            new_mantissa = huge_add(aligned_self, aligned_other)
            new_sign = self.sign
        else:
            if self.sign == '+':
                raw_sub = huge_sub(aligned_self, aligned_other)
            else:
                raw_sub = huge_sub(aligned_other, aligned_self)
                
            # huge_sub prepends a '-' if the result is negative
            if raw_sub.startswith('-'):
                new_sign = '-'
                new_mantissa = raw_sub[1:]
            else:
                new_sign = '+'
                new_mantissa = raw_sub
                
        raw_val_str = f"{new_sign}{new_mantissa}e{target_exponent}"
        return HugeFloat(raw_val_str, self.sig_figs)

    def __sub__(self, other: 'HugeFloat') -> 'HugeFloat':
        """Overloads the - operator. (Addition with the right operand's sign flipped)"""
        effective_other_sign = '+' if other.sign == '-' else '-'
        
        # 1. Machine Epsilon Shortcut
        exp_diff = self.exponent - other.exponent
        if abs(exp_diff) > self.sig_figs + 1:
            if self.exponent > other.exponent:
                return HugeFloat(f"{self.sign}{self.mantissa}e{self.exponent}", self.sig_figs)
            else:
                return HugeFloat(f"{effective_other_sign}{other.mantissa}e{other.exponent}", self.sig_figs)
                
        # 2. Align Exponents
        target_exponent = min(self.exponent, other.exponent)
        pad_self = self.exponent - target_exponent
        pad_other = other.exponent - target_exponent
        
        aligned_self = self.mantissa + ('0' * pad_self)
        aligned_other = other.mantissa + ('0' * pad_other)
        
        # 3. Route the math based on signs
        if self.sign == effective_other_sign:
            new_mantissa = huge_add(aligned_self, aligned_other)
            new_sign = self.sign
        else:
            if self.sign == '+':
                raw_sub = huge_sub(aligned_self, aligned_other)
            else:
                raw_sub = huge_sub(aligned_other, aligned_self)
                
            if raw_sub.startswith('-'):
                new_sign = '-'
                new_mantissa = raw_sub[1:]
            else:
                new_sign = '+'
                new_mantissa = raw_sub
                
        raw_val_str = f"{new_sign}{new_mantissa}e{target_exponent}"
        return HugeFloat(raw_val_str, self.sig_figs)

    def __mod__(self, other: 'HugeFloat') -> 'HugeFloat':
        """Overloads the % operator."""
        if other.mantissa == '0':
            raise ZeroDivisionError("Modulo by zero in HugeFloat.")
            
        if self.mantissa == '0':
            return HugeFloat('0', self.sig_figs)
            
        # 1. Align Exponents
        target_exponent = min(self.exponent, other.exponent)
        pad_self = self.exponent - target_exponent
        pad_other = other.exponent - target_exponent
        
        aligned_self = self.mantissa + ('0' * pad_self)
        aligned_other = other.mantissa + ('0' * pad_other)
        
        # 2. Integer division to get the floor quotient
        quotient, _ = huge_divide(aligned_self, aligned_other)
        
        # 3. Multiply quotient by divisor
        product = huge_prod(quotient, aligned_other)
        
        # 4. Subtract from original magnitude to get the remainder
        rem_pure = huge_sub(aligned_self, product)
        
        # 5. Package as HugeFloat (taking the sign of the dividend)
        raw_val_str = f"{self.sign}{rem_pure}e{target_exponent}"
        return HugeFloat(raw_val_str, self.sig_figs)

    def _cmp_mag(self, other: 'HugeFloat') -> int:
        """
        Compares absolute magnitudes: 1 if self > other, -1 if self < other, 0 if ==.
        """
        target_exponent = min(self.exponent, other.exponent)
        pad_self = self.exponent - target_exponent
        pad_other = other.exponent - target_exponent
        
        aligned_self = self.mantissa + ('0' * pad_self)
        aligned_other = other.mantissa + ('0' * pad_other)
        
        return huge_compare(aligned_self, aligned_other)

    def factorial(self) -> 'HugeFloat':
        """Calculates the factorial of a HugeFloat integer."""
        if self.sign == '-':
            raise ValueError("Factorial is only valid for positive numbers.")
        if self.exponent < 0:
            raise ValueError("Factorial is only valid for integers.")
            
        pure_int = self.mantissa + ('0' * self.exponent)
        result_mantissa = huge_fact(pure_int)
        
        return HugeFloat(f"+{result_mantissa}e0", self.sig_figs)

    def __pow__(self, other: 'HugeFloat', force_negative: bool = False) -> 'HugeFloat':
        """Overloads the ** (power) operator."""
        if other.sign == '-':
            raise ValueError("Power is not setup for negative exponents.")
            
        # 1. Format the exponent into integer and fractional string parts
        if other.exponent >= 0:
            exp_int_part = other.mantissa + ('0' * other.exponent)
            exp_frac_part = '0'
        else:
            padded = other.mantissa.zfill(abs(other.exponent) + 1)
            split_idx = len(padded) + other.exponent
            exp_int_part = padded[:split_idx].lstrip('0') or '0'
            exp_frac_part = padded[split_idx:].rstrip('0') or '0'

        # 2. Format the base
        base_mag = self.mantissa + ('0' * self.exponent) if self.exponent > 0 else self.mantissa
        base_decimals = abs(self.exponent) if self.exponent < 0 else 0
        
        # 3. Calculate Integer Power
        int_result = huge_power(base_mag, exp_int_part)
        int_dec_places = base_decimals * int(exp_int_part)
        
        # 4. Calculate Fractional Power
        if exp_frac_part == '0':
            final_mantissa, final_decimals = int_result, int_dec_places
        else:
            binary_fraction = _dec2bin_fraction(exp_frac_part, 4 * self.sig_figs)
            frac_result, frac_dec_places = _huge_powerf(base_mag, base_decimals, binary_fraction, self.sig_figs)
            final_mantissa = huge_prod(int_result, frac_result)
            final_decimals = int_dec_places + frac_dec_places
            
        # 5. Determine Final Sign
        new_sign = '+'
        if self.sign == '-':
            if force_negative:
                new_sign = '-'
            else:
                last_digit = int(exp_int_part[-1]) if exp_int_part != '0' else 0
                if last_digit % 2 != 0:
                    new_sign = '-'
                    
        return HugeFloat(f"{new_sign}{final_mantissa}e{-final_decimals}", self.sig_figs)


def _is_huge_digit(s: str) -> bool:
    """Checks if a string is a valid integer, float, rational, scientific, or 'pi'."""
    if not s:
        return False

    clean_s = s[1:] if s.startswith('-') else s
    if clean_s.lower() == 'pi':
        return True

    # Split by 'e' for scientific notation
    parts = clean_s.lower().split('e')
    if len(parts) > 2:
        return False

    # Validate Mantissa
    mantissa = parts[0]
    if '/' in mantissa:
        mantissa = mantissa.replace('/', '', 1)
    else:
        mantissa = mantissa.replace('.', '', 1)

    if not mantissa.isdigit():
        return False

    # Validate Exponent (if present)
    if len(parts) == 2:
        exponent = parts[1]
        if exponent.startswith('-') or exponent.startswith('+'):
            exponent = exponent[1:]
        if not exponent.isdigit():
            return False

    return True


def _insert_decimal(magnitude_str: str, decimal_places: int) -> str:
    """
    Inserts a decimal point into a magnitude string at the specified position from the right.
    Cleans up redundant trailing zeros after the decimal point.
    """
    if decimal_places == 0:
        return magnitude_str.lstrip('0') or '0'

    # 1. Left-pad with zeros if the number is shorter than the decimal places
    if len(magnitude_str) <= decimal_places:
        magnitude_str = magnitude_str.zfill(decimal_places + 1)

    # 2. Calculate insertion index and slice the string
    insert_pos = len(magnitude_str) - decimal_places

    # Extract the whole number part and strip leading zeros
    whole_part = magnitude_str[:insert_pos].lstrip('0') or '0'

    result = whole_part + '.' + magnitude_str[insert_pos:]

    # 3. Clean up trailing zeros (replicating trimtrail0 from the C version)
    if '.' in result:
        result = result.rstrip('0')
        # If it stripped all the way down to just the decimal, remove the decimal too
        if result.endswith('.'):
            result = result[:-1]

    return result


def _huge_dividef(dividend: str, divisor: str, tol: int) -> tuple[str, int]:
    """
    Performs floating-point division using repeated integer division with rounding.
    Calculates 1 guard digit beyond 'tol' to perform half-up rounding.
    Returns the pure integer quotient string and the number of decimal places appended.
    """
    # 1. Get the initial whole number quotient and remainder
    quotient, remainder = huge_divide(dividend, divisor)

    appended_decimals = 0

    # 2. If there's no remainder, we're done
    if remainder == '0':
        return quotient, appended_decimals

    # 3. Process remainder to get fractional digits up to (tol + 1) for rounding
    fractional_digits = []
    current_remainder = remainder
    target_digits = tol + 1

    while current_remainder != '0' and appended_decimals < target_digits:
        # Multiply remainder by 10
        current_remainder += '0'

        # Divide again to get the next decimal digit
        next_digit, current_remainder = huge_divide(current_remainder, divisor)

        fractional_digits.append(next_digit)
        appended_decimals += 1

    # 4. Construct full quotient string including guard digit
    full_quotient = quotient + "".join(fractional_digits)

    # 5. Round if we calculated the guard digit
    if appended_decimals > tol:
        guard_digit = int(full_quotient[-1])
        base_quotient = full_quotient[:-1]
        
        if guard_digit >= 5:
            full_quotient = huge_add(base_quotient, '1')
        else:
            full_quotient = base_quotient
            
        appended_decimals = tol

    return full_quotient, appended_decimals


def _dec2bin_fraction(fractional_mag: str, max_bits: int) -> str:
    """
    Converts the fractional part of a decimal magnitude into a binary string.
    Generates bits by repeatedly multiplying by 2.
    """
    if fractional_mag == '0' or not fractional_mag:
        return '0'
        
    binary_bits = []
    
    # We need to track the length to see if multiplying by 2 causes an overflow (a '1' bit)
    current_len = len(fractional_mag)
    current_val = fractional_mag
    
    # Loop until we hit our tolerance limit or the fraction resolves to exactly 0
    while current_val != '0' and len(binary_bits) < max_bits:
        # Multiply by 2 using your integer engine
        current_val = huge_prod(current_val, '2')
        
        # Check if the length increased (meaning it carried over the decimal point)
        new_len = len(current_val)
        
        if new_len > current_len:
            binary_bits.append('1')
            # "Drop" the 1 by stripping the leading digit to keep just the fractional part
            current_val = current_val[1:]
            # Clean up any resulting leading zeros
            current_val = current_val.lstrip('0') or '0'
            # Reset the target length for the next iteration
            current_len = len(current_val)
        else:
            binary_bits.append('0')
            
    # As in your C code, we ensure the last bit is a 1 for the root algorithm
    # If the loop maxed out and ended in 0s, we backtrack to the last 1.
    binary_string = "".join(binary_bits)
    binary_string = binary_string.rstrip('0')
    
    return binary_string if binary_string else '0'


def _huge_sqrt(mag: str) -> str:
    r"""
    Calculates the integer square root of a non-negative magnitude string 
    using Newton's method.
    
    Mathematical Reasoning for Decimal Precision:
    To avoid complex floating-point math, we exploit this algebraic property:
    $$ \sqrt{x} = \frac{\sqrt{x \cdot 10^{2k}}}{10^k} $$
    
    By padding the integer 'x' with '2k' zeros before passing it to this 
    engine, the returned integer square root will inherently contain 'k' 
    digits of fractional precision. The decimal point can then be manually 
    inserted 'k' places from the right.

    From Gemini:
    In your C code, you wrote the Newton-Raphson iteration like this:
  $$x_{i+1} = x_i + \frac{c - x_i^2}{2x_i}$$If we do a little bit of algebra to combine those terms by finding a common denominator ($2x_i$), watch what happens to the squared term:$$x_{i+1} = \frac{2x_i^2}{2x_i} + \frac{c - x_i^2}{2x_i}$$$$x_{i+1} = \frac{2x_i^2 + c - x_i^2}{2x_i}$$$$x_{i+1} = \frac{x_i^2 + c}{2x_i}$$$$x_{i+1} = \frac{1}{2} \left(x_i + \frac{c}{x_i} \right)$$This final simplified equation is exactly what next_x = (current_x + mag / current_x) / 2 is calculating in Python! It is the exact same mathematical curve, but by simplifying the algebra, we completely eliminate the need to calculate $x_i^2$ on every single loop, making the engine run significantly faster.
    """
    if mag == '0':
        return '0'
    if mag == '1':
        return '1'

    # 1. Generate a smart initial guess
    # A number with L digits has a square root with at most ceil(L/2) digits.
    # We MUST overestimate to ensure the sequence steps downward.
    guess_len = (len(mag) + 1) // 2
    current_x = '1' + ('0' * guess_len)

    # 2. Newton-Raphson iteration
    while True:
        # next_x = (current_x + mag / current_x) / 2
        quotient, _ = huge_divide(mag, current_x)
        sum_val = huge_add(current_x, quotient)
        next_x, _ = huge_divide(sum_val, '2')

        # 3. Termination condition
        # Integer Newton's method decreases monotonically until it hits the floor.
        # If the next guess is greater than or equal to the current, we've found the root.
        if huge_compare(next_x, current_x) >= 0:
            return current_x
            
        current_x = next_x


def _huge_powerf(base_mag: str, base_decimals: int, binary_fraction: str, tol: int) -> tuple[str, int]:
    """
    Calculates the fractional power of a base using its binary exponent string.
    Returns the pure integer representation and its fixed decimal place count.
    """
    if binary_fraction == '0':
        return '1', 0
        
    # Ensure our target tolerance is at least as large as the base decimals
    # to prevent negative padding strings.
    target_tol = max(tol, base_decimals)
    
    # The binary string (e.g., '101') was generated such that the last bit is always '1'.
    # Start by initializing our running total with the square root for that final '1' bit.
    pad = (2 * target_tol) - base_decimals
    padded_base = base_mag + ('0' * pad)
    current_t = _huge_sqrt(padded_base)
    
    # Iterate backwards through the remaining bits (excluding the last one)
    bits_to_process = binary_fraction[:-1]
    
    for bit in reversed(bits_to_process):
        if bit == '1':
            # t_next = sqrt(base * t_current)
            product = huge_prod(base_mag, current_t)
            # The product has (base_decimals + target_tol) implied decimals
            pad = (2 * target_tol) - (base_decimals + target_tol)
            padded_val = product + ('0' * pad)
            current_t = _huge_sqrt(padded_val)
        else:
            # t_next = sqrt(t_current)
            # current_t has target_tol implied decimals
            pad = target_tol  # derived from (2 * target_tol) - target_tol
            padded_val = current_t + ('0' * pad)
            current_t = _huge_sqrt(padded_val)
            
    return current_t, target_tol


def _huge_sin(x_hf: HugeFloat, guard_tol: int) -> HugeFloat:
    """Calculates sin(x) using the Maclaurin series."""
    # Initialize the sum with the first term (x)
    term_val = x_hf
    sum_val = term_val
    
    x_sq = x_hf * x_hf
    k = 3
    is_negative_term = True
    
    while True:
        # Numerator: term_val * x^2
        term_val = term_val * x_sq
        
        # Denominator: k * (k - 1)
        divisor_int = str(k * (k - 1))
        divisor_hf = HugeFloat(divisor_int, guard_tol)
        
        # Calculate the next term
        term_val = term_val / divisor_hf
        
        last_sum = sum_val
        
        # Route to addition or subtraction
        if is_negative_term:
            sum_val = sum_val - term_val
        else:
            sum_val = sum_val + term_val
            
        # Machine Epsilon Break: If the sum stopped changing, we reached precision limits
        if sum_val.mantissa == last_sum.mantissa and sum_val.exponent == last_sum.exponent:
            break
            
        k += 2
        is_negative_term = not is_negative_term

    return sum_val


def _huge_cos(x_hf: HugeFloat, guard_tol: int) -> HugeFloat:
    """Calculates cos(x) using the Maclaurin series."""
    # Initialize the sum with the first term (1)
    term_val = HugeFloat('1', guard_tol)
    sum_val = term_val
    
    x_sq = x_hf * x_hf
    k = 2
    is_negative_term = True
    
    while True:
        # Numerator: term_val * x^2
        term_val = term_val * x_sq
        
        # Denominator: k * (k - 1)
        divisor_int = str(k * (k - 1))
        divisor_hf = HugeFloat(divisor_int, guard_tol)
        
        # Calculate the next term
        term_val = term_val / divisor_hf
        
        last_sum = sum_val
        
        # Route to addition or subtraction
        if is_negative_term:
            sum_val = sum_val - term_val
        else:
            sum_val = sum_val + term_val
            
        # Machine Epsilon Break
        if sum_val.mantissa == last_sum.mantissa and sum_val.exponent == last_sum.exponent:
            break
            
        k += 2
        is_negative_term = not is_negative_term

    return sum_val


def _huge_arccot(x_hf: HugeFloat, guard_tol: int) -> HugeFloat:
    """Calculates arctan(1/x) using the Maclaurin series for arccotangent."""
    # First term: 1/x
    one = HugeFloat('1', guard_tol)
    term_val = one / x_hf
    sum_val = term_val
    
    x_sq = x_hf * x_hf
    k = 3
    is_negative = True
    
    while True:
        # Advance the power: term_val / x^2
        term_val = term_val / x_sq
        
        # Calculate the actual term to add/subtract: term_val / k
        added_term = term_val / HugeFloat(str(k), guard_tol)
        
        last_sum = sum_val
        
        if is_negative:
            sum_val = sum_val - added_term
        else:
            sum_val = sum_val + added_term
            
        # If the Machine Epsilon shortcut triggered, the sum hasn't changed!
        if sum_val.mantissa == last_sum.mantissa and sum_val.exponent == last_sum.exponent:
            break
            
        k += 2
        is_negative = not is_negative
        
    return sum_val

def _huge_pi(tol: int) -> str:
    """Generates pi to exactly 'tol' significant figures using Machin's Formula."""
    guard_tol = tol + 5
    
    x5 = HugeFloat('5', guard_tol)
    x239 = HugeFloat('239', guard_tol)
    
    arccot5 = _huge_arccot(x5, guard_tol)
    arccot239 = _huge_arccot(x239, guard_tol)
    
    sixteen = HugeFloat('16', guard_tol)
    four = HugeFloat('4', guard_tol)
    
    term1 = arccot5 * sixteen
    term2 = arccot239 * four
    
    pi_guard = term1 - term2
    
    # Passing the guarded string through a new object natively applies the final rounding
    pi_final = HugeFloat(str(pi_guard), tol)
    
    return str(pi_final)


def _huge_fmod(mag1: str, mag2: str) -> str:
    """Calculates mag1 % mag2 for positive decimal strings."""
    if mag2 == '0':
        raise ValueError("Modulo by zero.")
        
    pure1, pure2, dec_places = _align_decimals(mag1, mag2)
    
    # Integer division to get the quotient floor
    quotient, _ = huge_divide(pure1, pure2)
    
    # Multiply quotient by divisor
    product = huge_prod(quotient, pure2)
    
    # Subtract from original magnitude
    rem_pure = huge_sub(pure1, product)
    
    return _insert_decimal(rem_pure, dec_places)


def _huge_round(guarded_mag: str, guard_digits: int) -> str:
    """
    Rounds a guarded integer magnitude string based on the first guard digit.
    Assumes guarded_mag is a non-negative integer string.
    """
    if guard_digits <= 0 or len(guarded_mag) <= guard_digits:
        return '0'
        
    kept_part = guarded_mag[:-guard_digits] or '0'
    rounding_digit = int(guarded_mag[-guard_digits])
    
    if rounding_digit >= 5:
        return huge_add(kept_part, '1')
        
    return kept_part


def parse_and_validate():
    """
    Parses command-line arguments and validates them against the current functionality constraints.
    Returns: (operand1: str, operation: str, operand2: str)
    """
    # 1. Determine if we have piped input
    is_piped = not sys.stdin.isatty()

    if is_piped:
        # Read op1 from stdin (piped data)
        piped_input = sys.stdin.read().strip()

        # Check if piped input is a valid number
        if not _is_huge_digit(piped_input):
            print("Error: Piped input must be a valid integer or float string.", file=sys.stderr)
            usage()

        operand1 = piped_input

        # Determine operator and operand2 based on arg count
        if len(sys.argv) == 2:
            # Format: ... | py hugecalc.py !  OR  ... | py hugecalc.py sin
            operation = sys.argv[1]
            operand2 = ""
        elif len(sys.argv) == 3:
            # Format: ... | py hugecalc.py + 3
            operation = sys.argv[1]
            operand2 = sys.argv[2]
        else:
            print("Error: Invalid number of arguments for piped input.", file=sys.stderr)
            usage()

    else:
        # 2. Standard Interactive Mode
        if len(sys.argv) == 3:
            if sys.argv[1] in ('sin', 'cos', 'sind', 'cosd'):
                # Format: py hugecalc.py sin 14
                operation = sys.argv[1]
                operand1 = sys.argv[2]
            else:
                # Format: py hugecalc.py 10 !
                operand1 = sys.argv[1]
                operation = sys.argv[2]
            operand2 = ""
        elif len(sys.argv) == 4:
            # Format: py hugecalc.py 1 + 2
            operand1 = sys.argv[1]
            operation = sys.argv[2]
            operand2 = sys.argv[3]
        else:
            print("Error: Expected 3 arguments (op1, op, op2), 2 arguments for factorial (op1, !), or piped input.", file=sys.stderr)
            usage()

    # --- Validation Checks ---
    
    # 1. Operation check
    if operation not in VALID_OPERATORS:
        print(f"Error: Operation '{operation}' is not yet supported.\n"
              f"Only {VALID_OPERATORS} are implemented.", file=sys.stderr)
        usage()

    # 2. Operand checks
    if not _is_huge_digit(operand1):
        print(f"Error: Operand 1 ('{operand1}') must be a valid integer or float string.", file=sys.stderr)
        usage()

    # Only validate operand2 if the operation actually requires it
    if operation not in ('!', 'sin', 'cos', 'sind', 'cosd') and not _is_huge_digit(operand2):
        print(f"Error: Operand 2 ('{operand2}') must be a valid integer or float string.", file=sys.stderr)
        usage()

    # Success
    return operand1, operation, operand2


def huge_compare(a: str, b: str) -> int:
    """
    Compares the magnitude of two non-negative integer strings.
    a and b must not contain signs.
    Returns: 1 if a > b, 0 if a == b, -1 if a < b.
    """
    a = a.lstrip('0') or '0'
    b = b.lstrip('0') or '0'

    len_a = len(a)
    len_b = len(b)

    if len_a > len_b:
        return 1
    if len_a < len_b:
        return -1

    # Lengths are equal, compare lexicographically (which is numerically for magnitude strings)
    if a > b:
        return 1
    if a < b:
        return -1

    return 0


def huge_add(op1_str: str, op2_str: str) -> str:
    """
    Performs character-by-character addition of two non-negative integer strings.
    Assumes op1_str and op2_str are non-negative magnitudes (no signs).
    """
    op1_rev = op1_str[::-1]
    op2_rev = op2_str[::-1]
    max_len = max(len(op1_rev), len(op2_rev))

    result_digits = []
    carry = 0

    for i in range(max_len):
        digit1 = int(op1_rev[i]) if i < len(op1_rev) else 0
        digit2 = int(op2_rev[i]) if i < len(op2_rev) else 0

        total_sum = digit1 + digit2 + carry

        new_digit = total_sum % 10
        carry = total_sum // 10

        result_digits.append(str(new_digit))

    if carry:
        result_digits.append(str(carry))

    final_result = "".join(result_digits[::-1])

    # Clean up leading zeros
    return final_result.lstrip('0') or '0'


def huge_sub(op1_str: str, op2_str: str) -> str:
    """
    Performs character-by-character subtraction of two non-negative integer strings.
    If op1_str < op2_str, it swaps them, performs subtraction, and returns a negative result.
    Assumes op1_str and op2_str are non-negative magnitudes (no signs).
    """
    sign = ""

    # 1. Determine which number is larger (magnitude comparison)
    comparison = huge_compare(op1_str, op2_str)

    if comparison == 0:
        return '0'

    if comparison < 0:
        # op1 < op2, so swap and the result will be negative
        op1_str, op2_str = op2_str, op1_str
        sign = "-"

    # 2. Proceed with subtraction (op1_str >= op2_str is guaranteed now)
    op1_rev = op1_str[::-1]
    op2_rev = op2_str[::-1]
    max_len = len(op1_rev) # op1 is now the larger or equal magnitude

    result_digits = []
    borrow = 0

    for i in range(max_len):
        digit1 = int(op1_rev[i])

        # Get the digit from op2, default to 0 if op2 is shorter (implicit padding)
        digit2 = int(op2_rev[i]) if i < len(op2_rev) else 0

        # Calculate the difference of the digits including the current borrow
        total_diff = digit1 - digit2 - borrow

        if total_diff < 0:
            total_diff += 10
            borrow = 1
        else:
            borrow = 0

        result_digits.append(str(total_diff))

    # 3. Finalize result
    final_result = "".join(result_digits[::-1])
    # Remove leading zeros and prepend sign
    return sign + (final_result.lstrip('0') or '0')


def huge_prod(multiplicand: str, multiplier: str) -> str:
    """
    Performs character-by-character multiplication of two non-negative integer strings.
    Implements the classic long multiplication algorithm using huge_add.

    Assumes multiplicand and multiplier are non-negative magnitudes (no signs).
    """
    # 1. Handle edge case where either operand is zero
    if multiplicand == '0' or multiplier == '0':
        return '0'

    # Optimization: Ensure multiplicand is the longer number to reduce loops
    if huge_compare(multiplicand, multiplier) < 0:
        multiplicand, multiplier = multiplier, multiplicand

    final_sum = '0'

    # Iterate through the multiplier's digits from right to left (least significant)
    for i, digit_char in enumerate(multiplier[::-1]):
        digit = int(digit_char)

        if digit == 0:
            # Skip if the digit is 0, just continue to the next position (i)
            continue

        # 2. Calculate the partial product (multiplicand * current_digit)

        # Add the multiplicand 'digit' times using huge_add
        partial_product_magnitude = '0'
        for _ in range(digit):
            partial_product_magnitude = huge_add(partial_product_magnitude, multiplicand)

        # 3. Apply the positional shift (tack the right number of zeroes)
        # The shift is based on the current digit position 'i' (0 for ones place, 1 for tens, etc.)
        positional_product = partial_product_magnitude + ('0' * i)

        # 4. Add the positional product to the running total (final_sum)
        final_sum = huge_add(final_sum, positional_product)

    return final_sum


def huge_divide(dividend: str, divisor: str) -> tuple[str, str]:
    """
    Performs integer division of two non-negative integer strings.
    Returns: (quotient, remainder)

    Assumes dividend and divisor are non-negative magnitudes (no signs).
    The algorithm is based on repeated subtraction, similar to long division.
    """
    # 1. Handle edge cases
    if divisor == '0':
        # Unlike C, we can't 'exit(1)' but must handle the error gracefully.
        raise ZeroDivisionError("Division by zero error in huge_divide.")

    if dividend == '0':
        return '0', '0'

    # 2. Case: Divisor is larger than the dividend
    if huge_compare(dividend, divisor) == -1:
        return '0', dividend

    # 3. Case: Divisor equals the dividend
    if huge_compare(dividend, divisor) == 0:
        return '1', '0'

    # 4. Standard long division logic

    quotient = ''
    # The remainder starts as the first part of the dividend
    current_remainder = ''

    # Iterate through each digit of the dividend
    for digit in dividend:
        # Append the next digit of the dividend to the current remainder
        current_remainder += digit

        # Clean up leading zeros in the current remainder to keep it canonical
        current_remainder = current_remainder.lstrip('0') or '0'

        # If the current remainder is still less than the divisor, the next quotient digit is 0
        if huge_compare(current_remainder, divisor) == -1:
            # Only append '0' if the quotient is not empty (prevents leading zeros in quotient)
            if quotient or digit != '0':
                quotient += '0'
            continue

        # Find the largest digit 'q' such that divisor * q <= current_remainder
        q = 0
        temp_divisor_product = '0'

        # Iterate from 1 up to 9
        for test_q in range(1, 10):
            # Calculate divisor * test_q using huge_add (repeated addition)
            test_product = '0'
            for _ in range(test_q):
                test_product = huge_add(test_product, divisor)

            # Compare test_product with the current remainder
            if huge_compare(test_product, current_remainder) == 1:
                # The product is too large, so the quotient digit is the previous test_q (q)
                break

            # The product is acceptable, update q and the product for subtraction
            q = test_q
            temp_divisor_product = test_product

        # Append the quotient digit (q)
        quotient += str(q)

        # Calculate the new remainder: current_remainder - (divisor * q)
        # Note: huge_sub returns a magnitude if the first operand is larger.
        new_remainder = huge_sub(current_remainder, temp_divisor_product)

        # Set the current_remainder for the next iteration
        current_remainder = new_remainder.lstrip('0') or '0'

    # Clean up the final quotient (remove leading zeros)
    final_quotient = quotient.lstrip('0') or '0'

    return final_quotient, current_remainder


def huge_fact(op_str: str) -> str:
    """
    Calculates the factorial of a non-negative integer string.
    Implements a string-math counter up to the target operand.
    """
    # 0! and 1! are 1
    if op_str == '0' or op_str == '1':
        return '1'

    result = '1'
    current = '1'

    # Loop until the current counter matches the target operand
    while huge_compare(current, op_str) != 0:
        current = huge_add(current, '1')
        result = huge_prod(result, current)

    return result


def huge_power(base: str, exponent: str) -> str:
    """
    Calculates base raised to the exponent using halving and squaring.
    Assumes base and exponent are non-negative integer magnitudes.
    """
    if base == '0':
        return '0'
    if exponent == '0':
        return '1'

    t1 = base
    t2 = exponent
    t3 = '1'

    # Calculate the power by halving and squaring
    while t2 != '0':
        # Halve the exponent
        t2, remainder = huge_divide(t2, '2')

        # If it was odd (remainder is 1), multiply t3 by the current value of t1
        if remainder == '1':
            t3 = huge_prod(t3, t1)

        # Square t1 (optimization: skip squaring on the very last step)
        if t2 != '0':
            t1 = huge_prod(t1, t1)

    return t3


def get_sign_and_magnitude(operand: str) -> tuple[str, str]:
    """Extracts the sign and the non-negative magnitude string from an operand."""
    if operand.startswith('-'):
        return '-', operand[1:] or '0'
    return '+', operand


def calculate(op1: str, op: str, op2: str) -> tuple[str, str, str | None]:
    """
    Routes the actual huge-number operation based on input operator and operand signs.

    Returns: (operator: str, result_string: str, remainder_string: str | None)
    For division, remainder_string is the remainder. For others, it is None.
    """

    # --- PI INTERCEPTION ---
    def replace_pi(operand: str) -> str:
        clean = operand[1:] if operand.startswith('-') else operand
        if clean.lower() == 'pi':
            val = _huge_pi(WORKING_TOL)
            return '-' + val if operand.startswith('-') else val
        return operand
        
    op1 = replace_pi(op1)
    if op2:
        op2 = replace_pi(op2)
        
    # Keep procedural magnitude separation active for factorial (!) and power (^)
    sign1, mag1 = get_sign_and_magnitude(op1)
    sign2, mag2 = get_sign_and_magnitude(op2)
    # -----------------------

    result = ""
    remainder = None
    # Determine the result sign based on the operation and input signs
    result_sign = '+'

    # 3. Route the operation

    if op == '+':
        hf1 = HugeFloat(op1, WORKING_TOL)
        hf2 = HugeFloat(op2, WORKING_TOL)
        result = str(hf1 + hf2)
        return op, result, None

    elif op == '-':
        hf1 = HugeFloat(op1, WORKING_TOL)
        hf2 = HugeFloat(op2, WORKING_TOL)
        result = str(hf1 - hf2)
        return op, result, None

    elif op == '*':
        # Instantiate objects using the global WORKING_TOL
        hf1 = HugeFloat(op1, WORKING_TOL)
        hf2 = HugeFloat(op2, WORKING_TOL)
        
        # Execute the overloaded __mul__ method
        result_hf = hf1 * hf2
        
        # Get the final string representation
        # (We will build a proper formatting function later, but this gets it to the screen)
        result = str(result_hf)
        
        # Bypass the old sign attachment logic at the bottom of calculate()
        return op, result, None

    elif op == '/':
        hf1 = HugeFloat(op1, WORKING_TOL)
        hf2 = HugeFloat(op2, WORKING_TOL)
        
        try:
            # Execute the overloaded __truediv__ method
            result_hf = hf1 / hf2
            result = str(result_hf)
        except ZeroDivisionError as e:
            raise e
            
        return op, result, None

    elif op == '!':
        hf1 = HugeFloat(op1, WORKING_TOL)
        result_hf = hf1.factorial()
        return op, str(result_hf), None

    elif op == '^':
        hf1 = HugeFloat(op1, WORKING_TOL)
        force_neg = False
        
        # Handle rational exponents (e.g., 1/5)
        if '/' in op2:
            num_str, den_str = op2.split('/')
            if hf1.sign == '-':
                if int(den_str[-1]) % 2 == 0:
                    raise ValueError("Even denominator in rational exponent results in complex root.")
                force_neg = True
                
            num_hf = HugeFloat(num_str, WORKING_TOL)
            den_hf = HugeFloat(den_str, WORKING_TOL)
            hf2 = num_hf / den_hf
        else:
            hf2 = HugeFloat(op2, WORKING_TOL)
            
        result_hf = hf1.__pow__(hf2, force_neg)
        return op, str(result_hf), None
                    
    elif op == 'sin':
        hf1 = HugeFloat(op1, WORKING_TOL)
        orig_sign = hf1.sign
        hf1.sign = '+'  # Force positive for range reduction
        
        # --- RANGE REDUCTION [-pi, pi] ---
        pi_hf = HugeFloat(_huge_pi(WORKING_TOL), WORKING_TOL)
        two_pi_hf = pi_hf * HugeFloat('2', WORKING_TOL)
        
        # 1. Modulo input down to [0, 2pi]
        hf1_mod = hf1 % two_pi_hf
            
        # 2. Shift [pi, 2pi] down to [-pi, 0] for faster convergence
        if hf1_mod._cmp_mag(pi_hf) > 0:
            hf1_mod = hf1_mod - two_pi_hf
        # ---------------------------------
        
        # Calculate Maclaurin series natively
        result_hf = _huge_sin(hf1_mod, WORKING_TOL)
        
        # Apply final sign logic (sin(-x) = -sin(x))
        if orig_sign == '-':
            result_hf.sign = '+' if result_hf.sign == '-' else '-'
            
        return op, str(result_hf), None
        
    elif op == 'cos':
        hf1 = HugeFloat(op1, WORKING_TOL)
        hf1.sign = '+'  # cos(-x) = cos(x)
        
        # --- RANGE REDUCTION [-pi, pi] ---
        pi_hf = HugeFloat(_huge_pi(WORKING_TOL), WORKING_TOL)
        two_pi_hf = pi_hf * HugeFloat('2', WORKING_TOL)
        
        # 1. Modulo input down to [0, 2pi]
        hf1_mod = hf1 % two_pi_hf
            
        # 2. Shift [pi, 2pi] down to [-pi, 0] for faster convergence
        if hf1_mod._cmp_mag(pi_hf) > 0:
            hf1_mod = hf1_mod - two_pi_hf
        # ---------------------------------
        
        # Calculate Maclaurin series natively
        result_hf = _huge_cos(hf1_mod, WORKING_TOL)
            
        return op, str(result_hf), None

    elif op == 'sind':
        hf1 = HugeFloat(op1, WORKING_TOL)
        orig_sign = hf1.sign
        hf1.sign = '+'  # Force positive for range reduction
        
        # --- RANGE REDUCTION [-180, 180] ---
        three_sixty_hf = HugeFloat('360', WORKING_TOL)
        one_eighty_hf = HugeFloat('180', WORKING_TOL)
        
        hf1_mod = hf1 % three_sixty_hf
            
        if hf1_mod._cmp_mag(one_eighty_hf) > 0:
            hf1_mod = hf1_mod - three_sixty_hf
        # -----------------------------------
        
        # --- CONVERT TO RADIANS ---
        pi_hf = HugeFloat(_huge_pi(WORKING_TOL), WORKING_TOL)
        rad_hf = (hf1_mod * pi_hf) / one_eighty_hf
        
        # Calculate Maclaurin series natively
        result_hf = _huge_sin(rad_hf, WORKING_TOL)
        
        # Apply final sign logic (sin(-x) = -sin(x))
        if orig_sign == '-':
            result_hf.sign = '+' if result_hf.sign == '-' else '-'
            
        return op, str(result_hf), None

    elif op == 'cosd':
        hf1 = HugeFloat(op1, WORKING_TOL)
        hf1.sign = '+'  # cos(-x) = cos(x)
        
        # --- RANGE REDUCTION [-180, 180] ---
        three_sixty_hf = HugeFloat('360', WORKING_TOL)
        one_eighty_hf = HugeFloat('180', WORKING_TOL)
        
        hf1_mod = hf1 % three_sixty_hf
            
        if hf1_mod._cmp_mag(one_eighty_hf) > 0:
            hf1_mod = hf1_mod - three_sixty_hf
        # -----------------------------------
        
        # --- CONVERT TO RADIANS ---
        pi_hf = HugeFloat(_huge_pi(WORKING_TOL), WORKING_TOL)
        rad_hf = (hf1_mod * pi_hf) / one_eighty_hf
        
        # Calculate Maclaurin series natively
        result_hf = _huge_cos(rad_hf, WORKING_TOL)
            
        return op, str(result_hf), None


def _format_with_commas(number_str: str) -> str:
    """Inserts commas into the whole number part of a decimal string."""
    if not number_str:
        return '0'

    sign = ''
    if number_str.startswith('-'):
        sign = '-'
        number_str = number_str[1:]

    parts = number_str.split('.')
    whole_part = parts[0]
    fractional_part = f".{parts[1]}" if len(parts) > 1 else ""

    reversed_digits = whole_part[::-1]
    comma_parts = []
    for i in range(0, len(reversed_digits), 3):
        comma_parts.append(reversed_digits[i:i + 3])

    formatted_whole = ','.join(comma_parts)[::-1]
    return sign + formatted_whole + fractional_part


if __name__ == "__main__":
    # Get the validated operands and operation
    op1, op, op2 = parse_and_validate()

    try:
        # Route the operation based on signs
        original_op, raw_result, raw_remainder = calculate(op1, op, op2)
    except (ZeroDivisionError, ValueError) as e:
        # CHANGED: Print error to stderr
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Check if the output is being redirected (piped)
    if sys.stdout.isatty():
        # Interactive Mode: Pass raw result through HugeFloat at HCTOL to naturally round it
        final_hf = HugeFloat(raw_result, HCTOL)
        
        # Route to the requested formatting display
        if HCFORMAT == 'SCI':
            formatted_result = final_hf.to_sci_string()
        else:
            dec_string = final_hf.to_dec_string()
            formatted_result = _format_with_commas(dec_string)

        if original_op == '+':
            label = "       SUM"
        elif original_op == '-':
            label = "DIFFERENCE"
        elif original_op == '*':
            label = "   PRODUCT"
        elif original_op == '/':
            label = "  QUOTIENT"
        elif original_op == '!':
            label = " FACTORIAL"
        elif original_op == '^':
            label = "     POWER"
        elif original_op == 'sin' or original_op == 'sind':
            label = "      SINE"
        elif original_op == 'cos' or original_op == 'cosd':
            label = "    COSINE"

        else:
            label = "    RESULT" # Should not happen with current operators

        print(f"{label}: {formatted_result}")

        if raw_remainder is not None:
            # Only print remainder for division
            # Remainders from integer division are exact, no rounding needed
            formatted_remainder = _format_with_commas(raw_remainder)
            print(f" REMAINDER: {formatted_remainder}")

    else:
        # Piped Mode: print only the raw, unformatted result (quotient)
        # This raw result becomes the input for the next command in the pipe.
        # Piped Mode: print the raw, unrounded WORKING_TOL result
        print(raw_result)
