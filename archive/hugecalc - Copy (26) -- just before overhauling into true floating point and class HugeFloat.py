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

VALID_OPERATORS = ('+', '-', '*', '/', '!', '^', 'sin', 'cos')

def usage():
    """Prints the usage/help message to stderr and exits."""
    # CHANGED: Print usage to stderr so it doesn't contaminate pipe output
    print(HELPMESSAGE, file=sys.stderr)
    sys.exit(1)


def _expand_scientific(s: str) -> str:
    """
    Expands scientific notation (e.g., '1.23e3', '4E-2') into a standard decimal string.
    If the string is not in scientific notation, it returns it unchanged.
    """
    # 1. Quick exit if there's no scientific notation indicator
    if 'e' not in s.lower():
        return s

    # 2. Split into mantissa and exponent
    parts = s.lower().split('e')
    if len(parts) != 2:
        return s  # Invalid format, let the parser catch it later
        
    mantissa = parts[0]
    try:
        exponent = int(parts[1])
    except ValueError:
        return s  # Invalid exponent, let the parser catch it

    if exponent == 0:
        return mantissa

    # 3. Extract the sign from the mantissa
    sign = ''
    if mantissa.startswith('-'):
        sign = '-'
        mantissa = mantissa[1:]
    elif mantissa.startswith('+'):
        mantissa = mantissa[1:]

    # 4. Locate the decimal point and remove it
    if '.' in mantissa:
        dec_index_from_right = len(mantissa) - mantissa.index('.') - 1
        pure_digits = mantissa.replace('.', '')
    else:
        dec_index_from_right = 0
        pure_digits = mantissa
        
    # 5. Calculate the new virtual position of the decimal from the right
    new_dec_index_from_right = dec_index_from_right - exponent

    # 6. Shift the decimal point
    if new_dec_index_from_right <= 0:
        # Decimal moves to the right (pad with zeros on the right)
        pure_digits += '0' * abs(new_dec_index_from_right)
        result = pure_digits
    else:
        # Decimal moves to the left
        # If the index requires it, pad with zeros on the left
        if new_dec_index_from_right >= len(pure_digits):
            pad_len = new_dec_index_from_right - len(pure_digits) + 1
            pure_digits = ('0' * pad_len) + pure_digits
        
        # Re-insert the physical decimal point
        insert_pos = len(pure_digits) - new_dec_index_from_right
        result = pure_digits[:insert_pos] + '.' + pure_digits[insert_pos:]

    # 7. Final cleanup of leading/trailing zeros
    if '.' in result:
        parts = result.split('.')
        int_part = parts[0].lstrip('0') or '0'
        frac_part = parts[1].rstrip('0')
        result = int_part + ('.' + frac_part if frac_part else '')
    else:
        result = result.lstrip('0') or '0'

    return sign + result


def _is_huge_digit(s: str) -> bool:
    """Checks if a string is a valid integer, float, rational, or 'pi', allowing a leading minus."""
    if not s:
        return False

    # Ignore the leading minus sign for the validation check
    clean_s = s[1:] if s.startswith('-') else s

    # Check for our special 'pi' constant
    if clean_s.lower() == 'pi':
        return True

    # Replace a single decimal point OR a single slash with nothing.
    # We shouldn't allow both (like 1.5/3), so we check and replace only one.
    if '/' in clean_s:
        clean_s = clean_s.replace('/', '', 1)
    else:
        clean_s = clean_s.replace('.', '', 1)

    # If it's a valid number, only digits should remain.
    return clean_s.isdigit()


def _align_decimals(mag1: str, mag2: str) -> tuple[str, str, int]:
    """
    Aligns two magnitude strings by their decimal points, padding with trailing zeros.
    Returns the decimal-stripped integer strings and the number of shared decimal places.
    """
    # 1. Split into whole and fractional parts
    parts1 = mag1.split('.')
    parts2 = mag2.split('.')

    # 2. Extract fractional parts (default to empty string if no decimal)
    frac1 = parts1[1] if len(parts1) > 1 else ""
    frac2 = parts2[1] if len(parts2) > 1 else ""

    # 3. Determine the maximum decimal length needed for alignment
    max_dec_len = max(len(frac1), len(frac2))

    # 4. Pad the fractional parts with trailing zeros (replicating rightpad0)
    padded_frac1 = frac1.ljust(max_dec_len, '0')
    padded_frac2 = frac2.ljust(max_dec_len, '0')

    # 5. Reconstruct the numbers entirely without the decimal point
    aligned_mag1 = parts1[0] + padded_frac1
    aligned_mag2 = parts2[0] + padded_frac2

    # Clean up any leading zeros (e.g., "0.5" -> "05" -> "5")
    aligned_mag1 = aligned_mag1.lstrip('0') or '0'
    aligned_mag2 = aligned_mag2.lstrip('0') or '0'

    return aligned_mag1, aligned_mag2, max_dec_len


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


def _extract_decimals(mag: str) -> tuple[str, int]:
    """
    Removes the decimal point from a magnitude string.
    Returns the pure integer string and the number of decimal places.
    """
    if '.' not in mag:
        return mag, 0

    parts = mag.split('.')
    pure_int = parts[0] + parts[1]

    # Clean up leading zeros in case of inputs like "0.05" -> "005" -> "5"
    pure_int = pure_int.lstrip('0') or '0'

    return pure_int, len(parts[1])


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


def _huge_sin(pure_x: str, dec_places: int, tol: int) -> tuple[str, str]:
    """
    Calculates sin(x) using the Maclaurin series.
    Expects x in radians. Returns a tuple (sign, pure_integer_magnitude) 
    scaled to exactly 'tol' decimal places.
    """
    # 1. Scale x to exactly 'tol' decimal places
    guard_tol_power = 5
    guard_tol = tol + guard_tol_power

    if dec_places < guard_tol:
        X = pure_x + ('0' * (guard_tol - dec_places))
    elif dec_places > guard_tol:
        X = pure_x[:-(dec_places - guard_tol)] # Truncate extra precision beyond HCTOL
    else:
        X = pure_x

    if X == '0':
        return '+', '0' + ('0' * tol)

    # 2. X_sq = X * X (will have 2*tol implied decimals)
    X_sq = huge_prod(X, X)

    # 3. Initialize dual-accumulators
    current_term = X
    sum_pos = X
    sum_neg = '0'
    
    k = 3
    is_negative_term = True
    
    iteration_count = 0

    # 4. Loop until the term shrinks to 0 within our tolerance
    while True:
        iteration_count += 1
        if iteration_count > 100000:
            raise RuntimeWarning("Maclaurin series iterations exceeded guard tolerance limits.")

        # Numerator = current_term * X_sq (Has 3*tol implied decimals)
        numerator = huge_prod(current_term, X_sq)
        
        # Denominator = k * (k-1) * 10^(2*guard_tol)
        # We append 2*tol zeros so the division brings the result back to exactly 'tol' decimals
        divisor_int = str(k * (k - 1))
        divisor = divisor_int + ('0' * (2 * guard_tol))
        
        # Calculate the next term
        next_term, _ = huge_divide(numerator, divisor)
        
        if next_term == '0':
            break
            
        # Route to the correct accumulator
        if is_negative_term:
            sum_neg = huge_add(sum_neg, next_term)
        else:
            sum_pos = huge_add(sum_pos, next_term)
            
        # Prep for next loop
        current_term = next_term
        k += 2
        is_negative_term = not is_negative_term

    # 5. Final calculation: sum_pos - sum_neg
    comp = huge_compare(sum_pos, sum_neg)
    if comp >= 0:
        final_mag = huge_sub(sum_pos, sum_neg)
        sign = '+'
    else:
        final_mag = huge_sub(sum_neg, sum_pos)
        sign = '-'
        
    # Round based on the guard digits to return exactly 'tol' decimal places
    rounded_mag = _huge_round(final_mag, guard_tol_power)
    return sign, rounded_mag


def _huge_cos(pure_x: str, dec_places: int, tol: int) -> tuple[str, str]:
    r"""
    Calculates cos(x) using the Maclaurin series.
    Expects x in radians. Returns a tuple (sign, pure_integer_magnitude) 
    scaled to exactly 'tol' decimal places.
    $$ \cos(x) = 1 - \frac{x^2}{2!} + \frac{x^4}{4!} - \frac{x^6}{6!} + \dots $$
    """
    # 1. Scale x to exactly 'tol' decimal places
    guard_tol_power = 5
    guard_tol = tol + guard_tol_power

    if dec_places < guard_tol:
        X = pure_x + ('0' * (guard_tol - dec_places))
    elif dec_places > guard_tol:
        X = pure_x[:-(dec_places - guard_tol)] # Truncate extra precision beyond HCTOL
    else:
        X = pure_x

    if X == '0':
        # cos(0) = 1
        return '+', '1' + ('0' * tol)

    # 2. X_sq = X * X (will have 2*tol implied decimals)
    X_sq = huge_prod(X, X)

    # 3. Initialize dual-accumulators
    # Tirst term of cos(x) is 1, which we scale to 'guard_tol' decimal places
    current_term = '1' + ('0' * guard_tol)
    sum_pos = current_term
    sum_neg = '0'
    
    k = 2  # Denominator starts at 2 * 1
    is_negative_term = True
    
    iteration_count = 0

    # 4. Loop until the term shrinks to 0 within our tolerance
    while True:
        iteration_count += 1
        if iteration_count > 100000:
            raise RuntimeWarning("Maclaurin series iterations exceeded guard tolerance limits.")

        # Numerator = current_term * X_sq (Has 3*tol implied decimals)
        numerator = huge_prod(current_term, X_sq)
        
        # Denominator = k * (k-1) * 10^(2*guard_tol)
        divisor_int = str(k * (k - 1))
        divisor = divisor_int + ('0' * (2 * guard_tol))
        
        # Calculate the next term
        next_term, _ = huge_divide(numerator, divisor)
        
        if next_term == '0':
            break
            
        # Route to the correct accumulator
        if is_negative_term:
            sum_neg = huge_add(sum_neg, next_term)
        else:
            sum_pos = huge_add(sum_pos, next_term)
            
        # Prep for next loop
        current_term = next_term
        k += 2
        is_negative_term = not is_negative_term

    # 5. Final calculation: sum_pos - sum_neg
    comp = huge_compare(sum_pos, sum_neg)
    if comp >= 0:
        final_mag = huge_sub(sum_pos, sum_neg)
        sign = '+'
    else:
        final_mag = huge_sub(sum_neg, sum_pos)
        sign = '-'
        
    # Round based on the guard digits to return exactly 'tol' decimal places
    rounded_mag = _huge_round(final_mag, guard_tol_power)
    return sign, rounded_mag


def _huge_arccot(x_str: str, guard_tol: int) -> tuple[str, str]:
    r"""
    Calculates arctan(1/x) using the Maclaurin series for arccotangent.
    Returns a tuple of (sum_pos, sum_neg) scaled to 'guard_tol' decimal places.
    $$ \arctan\left(\frac{1}{x}\right) = \frac{1}{x} - \frac{1}{3x^3} + \frac{1}{5x^5} - \dots $$
    """
    # 1. Initialize the scaled numerator: 10^(guard_tol)
    power_term = '1' + ('0' * guard_tol)
    
    # 2. First term: 1/x
    term_val, _ = huge_divide(power_term, x_str)
    
    sum_pos = term_val
    sum_neg = '0'
    
    # X_sq = X * X (Used to advance the powers of X)
    x_sq = huge_prod(x_str, x_str)
    
    k = 3
    is_negative = True
    
    # 3. Loop until the term shrinks to 0
    while True:
        # Advance the power: term_val = term_val / x^2
        term_val, _ = huge_divide(term_val, x_sq)
        
        if term_val == '0':
            break
            
        # Calculate the actual term to add/subtract: term_val / k
        added_term, _ = huge_divide(term_val, str(k))
        
        # Route to the correct accumulator
        if is_negative:
            sum_neg = huge_add(sum_neg, added_term)
        else:
            sum_pos = huge_add(sum_pos, added_term)
            
        k += 2
        is_negative = not is_negative
        
    return sum_pos, sum_neg


def _huge_pi(tol: int) -> str:
    r"""
    Generates pi to exactly 'tol' decimal places using Machin's Formula:
    $$ \pi = 16\arctan\left(\frac{1}{5}\right) - 4\arctan\left(\frac{1}{239}\right) $$
    
    Note on Guard Digits (guard_tol = tol + 5):
    The integer division engine truncates the remainder on every step. 
    In the Maclaurin series, this introduces a maximum error of exactly 1 
    in the final decimal place per term. Accumulating 100,000 terms would 
    shift this error up by exactly 5 decimal places (10^5). Therefore, 
    adding 5 guard digits mathematically guarantees perfect precision for 
    any series requiring up to 100,000 iterations to converge. If calculating 
    pi to hundreds of thousands of digits where the iterations exceed 100,000, 
    this guard buffer must be increased (e.g., 6 digits for 1,000,000 terms).
    """
    
    # Use 5 guard digits to prevent rounding errors from compounding
    guard_tol_power = 5
    guard_tol = tol + guard_tol_power
    
    # Calculate the arccotangents for 5 and 239
    pos5, neg5 = _huge_arccot('5', guard_tol)
    pos239, neg239 = _huge_arccot('239', guard_tol)
    
    # Multiply by their respective coefficients
    # 16 * arccot(5)
    pos5_16 = huge_prod(pos5, '16')
    neg5_16 = huge_prod(neg5, '16')
    
    # 4 * arccot(239)
    pos239_4 = huge_prod(pos239, '4')
    neg239_4 = huge_prod(neg239, '4')
    
    # Combine the equations: (16*pos5 - 16*neg5) - (4*pos239 - 4*neg239)
    # Algebraically rearranged to avoid negative string magnitudes:
    # Total Positive = 16*pos5 + 4*neg239
    # Total Negative = 16*neg5 + 4*pos239
    total_pos = huge_add(pos5_16, neg239_4)
    total_neg = huge_add(neg5_16, pos239_4)
    
    # Subtract to get the final pure integer magnitude of pi
    pi_guard_mag = huge_sub(total_pos, total_neg)
    
    # Round based on the guard digits to return exactly 'tol' decimal places
    pi_mag = _huge_round(pi_guard_mag, guard_tol_power)
    
    # Format it perfectly as a standard float string
    return _insert_decimal(pi_mag, tol)


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


def _round_decimal_string(val_str: str, target_dec: int) -> str:
    """Rounds a floating-point string to a target number of decimal places."""
    if '.' not in val_str:
        return val_str

    sign, mag = get_sign_and_magnitude(val_str)
    pure_int, current_dec = _extract_decimals(mag)

    if current_dec <= target_dec:
        return val_str

    # Calculate how many digits we need to chop off
    excess_digits = current_dec - target_dec
    
    # Use existing _huge_round to round the integer magnitude
    rounded_mag = _huge_round(pure_int, excess_digits)
    
    # Re-insert the decimal point
    final_mag = _insert_decimal(rounded_mag, target_dec)
    
    if final_mag == '0':
        return '0'
        
    return '-' + final_mag if sign == '-' else final_mag


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

        operand1 = _expand_scientific(piped_input)

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
            if sys.argv[1] in ('sin', 'cos'):
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
    operand1 = _expand_scientific(operand1)
    if operand2:
        operand2 = _expand_scientific(operand2)
    
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
    
    if operation not in ('!', 'sin', 'cos') and not _is_huge_digit(operand2):
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

    # 1. Separate signs and magnitudes
    sign1, mag1 = get_sign_and_magnitude(op1)
    sign2, mag2 = get_sign_and_magnitude(op2)

    # --- PI INTERCEPTION ---
    # Dynamically inject the value of pi if requested
    if mag1.lower() == 'pi' or mag2.lower() == 'pi':
        pi_val = _huge_pi(WORKING_TOL)
        if mag1.lower() == 'pi':
            mag1 = pi_val
        if mag2.lower() == 'pi':
            mag2 = pi_val
    # -----------------------

    result = ""
    remainder = None
    # Determine the result sign based on the operation and input signs
    result_sign = '+'

    # 2. Align decimals (NEW LOGIC)
    # We'll need a variable to track where to re-insert the decimal later
    result_decimal_places = 0

    if op in ('+', '-'):
        mag1, mag2, result_decimal_places = _align_decimals(mag1, mag2)

    # 3. Route the operation

    if op == '+':
        if sign1 == '+' and sign2 == '+':
            # (+A) + (+B) = A + B
            result = huge_add(mag1, mag2)

        elif sign1 == '-' and sign2 == '-':
            # (-A) + (-B) = -(A + B)
            result_sign = '-'
            result = huge_add(mag1, mag2)

        elif sign1 == '+' and sign2 == '-':
            # (+A) + (-B) = A - B
            op = '-' # Change effective operation for label
            result = huge_sub(mag1, mag2)

        elif sign1 == '-' and sign2 == '+':
            # (-A) + (+B) = B - A
            op = '-' # Change effective operation for label
            result = huge_sub(mag2, mag1)

    elif op == '-':
        if sign1 == '+' and sign2 == '+':
            # (+A) - (+B) = A - B
            result = huge_sub(mag1, mag2)

        elif sign1 == '-' and sign2 == '-':
            # (-A) - (-B) = -A + B = B - A
            result = huge_sub(mag2, mag1)

        elif sign1 == '+' and sign2 == '-':
            # (+A) - (-B) = A + B
            op = '+' # Change effective operation for label
            result = huge_add(mag1, mag2)

        elif sign1 == '-' and sign2 == '+':
            # (-A) - (+B) = -(A + B)
            op = '+' # Change effective operation for label
            result_sign = '-'
            result = huge_add(mag1, mag2)

    elif op == '*':
        # 1. Extract pure integers and count decimal places
        pure_mag1, dec_places1 = _extract_decimals(mag1)
        pure_mag2, dec_places2 = _extract_decimals(mag2)

        # 2. Determine the sign
        if (sign1 == '+' and sign2 == '+') or (sign1 == '-' and sign2 == '-'):
            result_sign = '+'
        else:
            result_sign = '-'

        # 3. Perform integer multiplication
        result = huge_prod(pure_mag1, pure_mag2)

        # 4. Re-insert the decimal point (sum of the decimal places)
        total_decimal_places = dec_places1 + dec_places2
        result = _insert_decimal(result, total_decimal_places)

    elif op == '/':
        # 1. Extract pure integers and count decimal places
        pure_mag1, dec_places1 = _extract_decimals(mag1)
        pure_mag2, dec_places2 = _extract_decimals(mag2)

        # 2. Determine the sign
        if (sign1 == '+' and sign2 == '+') or (sign1 == '-' and sign2 == '-'):
            result_sign = '+'
        else:
            result_sign = '-'

        try:
            # 3. Branch based on whether a decimal point is physically present
            if '.' not in mag1 and '.' not in mag2:
                # --- PURE INTEGER DIVISION ---
                result, remainder = huge_divide(pure_mag1, pure_mag2)

                # The remainder always takes the sign of the dividend (mag1)
                if remainder != '0' and sign1 == '-':
                    remainder = '-' + remainder
            else:
                # --- FLOATING-POINT DIVISION ---
                # Calculate exactly how many loops we need to hit WORKING_TOL
                required_loops = WORKING_TOL - (dec_places1 - dec_places2)

                # Prevent negative loops if the dividend has massive trailing zeros
                required_loops = max(0, required_loops)

                result, appended_decimals = _huge_dividef(pure_mag1, pure_mag2, required_loops)

                # Calculate the final decimal placement
                final_dec_places = (dec_places1 - dec_places2) + appended_decimals

                # Insert the decimal (if final_dec_places is negative, we need to right-pad zeros)
                if final_dec_places < 0:
                    result = result + ('0' * abs(final_dec_places))
                elif final_dec_places > 0:
                    result = _insert_decimal(result, final_dec_places)

                # No remainder for floating point division
                remainder = None

        except ZeroDivisionError as e:
            # Reraise the exception for the main block to handle
            raise e

    elif op == '!':
        # 1. Extract pure integer and count decimal places
        pure_mag1, dec_places1 = _extract_decimals(mag1)

        # 2. Error checking (replicating HUGECALC.C constraints)
        if sign1 == '-':
            raise ValueError("Factorial is only valid for positive numbers.")
        if dec_places1 > 0:
            raise ValueError("Factorial is only valid for integers.")

        # 3. Perform factorial calculation
        result = huge_fact(pure_mag1)
        result_sign = '+'

    elif op == '^':
        # 1. Extract pure integers and count decimal places for base
        pure_mag1, dec_places1 = _extract_decimals(mag1)

        # 2. Intercept and process rational exponents (e.g., 1/5)
        force_negative_result = False
        if '/' in mag2:
            num_str, den_str = mag2.split('/')

            # Check for negative base rules
            if sign1 == '-':
                last_den_digit = int(den_str[-1]) if den_str else 0
                if last_den_digit % 2 == 0:
                    raise ValueError("Even denominator in rational exponent results in complex root.")
                else:
                    # Odd denominator allows a real negative root
                    force_negative_result = True

            # Convert the rational to a high-precision decimal string using WORKING_TOL
            pure_quotient, appended_decimals = _huge_dividef(num_str, den_str, WORKING_TOL)
            mag2 = _insert_decimal(pure_quotient, appended_decimals)

        # 3. Standard decimal extraction for the exponent
        pure_mag2, dec_places2 = _extract_decimals(mag2)

        # Split mag2 into integer and fractional parts
        parts2 = mag2.split('.')
        exp_int_part = parts2[0] if parts2[0] else '0'
        exp_frac_part = parts2[1] if len(parts2) > 1 else '0'

        # Clean up leading/trailing zeros for the exponent parts
        exp_int_part = exp_int_part.lstrip('0') or '0'
        exp_frac_part = exp_frac_part.rstrip('0')
        if not exp_frac_part:
            exp_frac_part = '0'

        # 4. Error checking 
        if sign2 == '-':
            raise ValueError("Power is not setup for negative exponents.")

        # If it's a fractional exponent on a negative base, it MUST have come through the rational check
        if sign1 == '-' and exp_frac_part != '0' and not force_negative_result:
            raise ValueError("Power is not setup to handle complex numbers (use rational fractions like 1/3).")

        # 5. Perform integer exponentiation (Base ^ Integer_Part)
        int_result = huge_power(pure_mag1, exp_int_part)
        int_dec_places = dec_places1 * int(exp_int_part)

        # 6. Perform fractional exponentiation (Base ^ Fractional_Part)
        if exp_frac_part == '0':
            result = int_result
            final_dec_places = int_dec_places
        else:
            # Generate binary sequence (max bits = 4 * WORKING_TOL)
            binary_fraction = _dec2bin_fraction(exp_frac_part, 4 * WORKING_TOL)

            # Calculate fractional power
            frac_result, frac_dec_places = _huge_powerf(pure_mag1, dec_places1, binary_fraction, WORKING_TOL)
            
            # Multiply integer and fractional results
            result = huge_prod(int_result, frac_result)
            final_dec_places = int_dec_places + frac_dec_places

        # 7. Re-insert the decimal point
        result = _insert_decimal(result, final_dec_places)

        # 8. Determine final sign
        result_sign = '+'
        if sign1 == '-':
            # If we forced a negative result via an odd rational denominator, it stays negative
            if force_negative_result:
                result_sign = '-'
            else:
                # Standard integer odd/even check
                last_digit = int(exp_int_part[-1]) if exp_int_part != '0' else 0
                if last_digit % 2 != 0:
                    result_sign = '-'
                    
    elif op == 'sin':
        # --- RANGE REDUCTION [-pi, pi] ---
        pi_str = _huge_pi(WORKING_TOL)
        pure_pi, pi_dec = _extract_decimals(pi_str)
        two_pi_str = _insert_decimal(huge_prod(pure_pi, '2'), pi_dec)
        
        # 1. Modulo input down to [0, 2pi]
        mag1 = _huge_fmod(mag1, two_pi_str)
        
        # 2. Shift [pi, 2pi] down to [-pi, 0] for faster convergence
        pure_mag1_align, pure_pi_align, _ = _align_decimals(mag1, pi_str)
        if huge_compare(pure_mag1_align, pure_pi_align) > 0:
            pure_2pi_align, pure_mag1_align2, dec_align = _align_decimals(two_pi_str, mag1)
            mag1 = _insert_decimal(huge_sub(pure_2pi_align, pure_mag1_align2), dec_align)
            sign1 = '-' if sign1 == '+' else '+'
        # ---------------------------------
        
        # 1. Extract pure integers and count decimal places
        pure_mag1, dec_places1 = _extract_decimals(mag1)
        
        # 2. Calculate Maclaurin series
        series_sign, result = _huge_sin(pure_mag1, dec_places1, WORKING_TOL)
        
        # 3. Re-insert the decimal point
        result = _insert_decimal(result, WORKING_TOL)
        
        # 4. Determine final sign
        # Because sin(-x) = -sin(x), we flip the engine's sign if the input was negative.
        if sign1 == '-':
            result_sign = '-' if series_sign == '+' else '+'
        else:
            result_sign = series_sign
            
        # Since sin is a unary operator, remainder is always None
        remainder = None
        
    elif op == 'cos':
        # --- RANGE REDUCTION [-pi, pi] ---
        pi_str = _huge_pi(WORKING_TOL)
        pure_pi, pi_dec = _extract_decimals(pi_str)
        two_pi_str = _insert_decimal(huge_prod(pure_pi, '2'), pi_dec)
        
        # 1. Modulo input down to [0, 2pi]
        mag1 = _huge_fmod(mag1, two_pi_str)
        
        # 2. Shift [pi, 2pi] down to [-pi, 0] for faster convergence
        pure_mag1_align, pure_pi_align, _ = _align_decimals(mag1, pi_str)
        if huge_compare(pure_mag1_align, pure_pi_align) > 0:
            pure_2pi_align, pure_mag1_align2, dec_align = _align_decimals(two_pi_str, mag1)
            mag1 = _insert_decimal(huge_sub(pure_2pi_align, pure_mag1_align2), dec_align)
        # ---------------------------------
        
        # 1. Extract pure integers and count decimal places
        pure_mag1, dec_places1 = _extract_decimals(mag1)
        
        # 2. Calculate Maclaurin series
        series_sign, result = _huge_cos(pure_mag1, dec_places1, WORKING_TOL)
        
        # 3. Re-insert the decimal point
        result = _insert_decimal(result, WORKING_TOL)
        
        # 4. Determine final sign
        # Because cos(-x) = cos(x), the sign of the input is irrelevant
        result_sign = series_sign
            
        # Since cos is a unary operator, remainder is always None
        remainder = None

    # 3. Re-insert the decimal point for addition/subtraction
    if op in ('+', '-'):
        result = _insert_decimal(result, result_decimal_places)

    # 4. Apply the correct sign to the result magnitude
    if result == '0':
        return op, '0', remainder

    if result.startswith('-'):
        return op, result, remainder

    final_result = result
    if result_sign == '-':
        final_result = '-' + result

    return op, final_result, remainder


def _format_with_commas(number_str: str) -> str:
    """Inserts commas into the whole number part of a string representation of a number."""
    if not number_str:
        return '0'

    # Check for sign
    sign = ''
    if number_str.startswith('-'):
        sign = '-'
        number_str = number_str[1:]

    # Split the number into whole and fractional parts
    parts = number_str.split('.')
    whole_part = parts[0]
    fractional_part = f".{parts[1]}" if len(parts) > 1 else ""

    # Reverse the whole number string to insert commas from the right
    reversed_digits = whole_part[::-1]

    comma_parts = []
    # Iterate and slice every 3 characters
    for i in range(0, len(reversed_digits), 3):
        comma_parts.append(reversed_digits[i:i + 3])

    # Re-reverse the parts and join with commas
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
        # Interactive Mode: Round to HCTOL, format, and print
        rounded_result = _round_decimal_string(raw_result, HCTOL)
        formatted_result = _format_with_commas(rounded_result)

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
        elif original_op == 'sin':
            label = "      SINE"
        elif original_op == 'cos':
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
