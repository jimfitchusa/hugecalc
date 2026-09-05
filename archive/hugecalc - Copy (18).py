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

Supported operations: +, -, *, /, !, ^
Future support: ^ with decimals
"""

VALID_OPERATORS = ('+', '-', '*', '/', '!', '^')

def usage():
    """Prints the usage/help message to stderr and exits."""
    # CHANGED: Print usage to stderr so it doesn't contaminate pipe output
    print(HELPMESSAGE, file=sys.stderr)
    sys.exit(1)


def _is_huge_digit(s: str) -> bool:
    """Checks if a string is a valid integer or float, allowing a leading minus."""
    if not s:
        return False

    # Ignore the leading minus sign for the validation check
    clean_s = s[1:] if s.startswith('-') else s

    # Replace a single decimal point with nothing.
    # If it's a valid number, only digits should remain.
    return clean_s.replace('.', '', 1).isdigit()


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
    Performs floating-point division using repeated integer division.
    Returns the pure integer quotient string and the number of decimal places appended.
    """
    # 1. Get the initial whole number quotient and remainder
    quotient, remainder = huge_divide(dividend, divisor)

    appended_decimals = 0

    # 2. If there's no remainder, we're done
    if remainder == '0':
        return quotient, appended_decimals

    # 3. Process the remainder to get fractional digits up to HCTOL
    fractional_digits = []
    current_remainder = remainder

    while current_remainder != '0' and appended_decimals < tol:
        # Multiply remainder by 10 (by tacking on a zero)
        current_remainder += '0'

        # Divide again to get the next decimal digit
        next_digit, current_remainder = huge_divide(current_remainder, divisor)

        fractional_digits.append(next_digit)
        appended_decimals += 1

    # 4. Append the fractional digits to the main quotient
    final_quotient = quotient + "".join(fractional_digits)

    return final_quotient, appended_decimals


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
            print("Error: Piped input must be a valid integer string.", file=sys.stderr)
            usage()

        operand1 = piped_input

        # Determine operator and operand2 based on arg count
        if len(sys.argv) == 2:
            # Format: ... | py hugecalc.py !
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
    if operation != '!' and not _is_huge_digit(operand2):
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
                # Calculate exactly how many loops we need to hit HCTOL
                required_loops = HCTOL - (dec_places1 - dec_places2)

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
        # 1. Extract pure integers and count decimal places
        pure_mag1, dec_places1 = _extract_decimals(mag1)
        
        # Split mag2 into integer and fractional parts
        parts2 = mag2.split('.')
        exp_int_part = parts2[0] if parts2[0] else '0'
        exp_frac_part = parts2[1] if len(parts2) > 1 else '0'
        
        # Clean up leading/trailing zeros for the exponent parts
        exp_int_part = exp_int_part.lstrip('0') or '0'
        exp_frac_part = exp_frac_part.rstrip('0')
        if not exp_frac_part:
            exp_frac_part = '0'
        
        # 2. Error checking (replicating HUGECALC.C constraints)
        if sign2 == '-':
            raise ValueError("Power is not setup for negative exponents.")
        if sign1 == '-' and exp_frac_part != '0':
            raise ValueError("Power is not setup to handle complex numbers.")
            
        # 3. Perform integer exponentiation (Base ^ Integer_Part)
        int_result = huge_power(pure_mag1, exp_int_part)
        int_dec_places = dec_places1 * int(exp_int_part)
        
        # 4. Perform fractional exponentiation (Base ^ Fractional_Part)
        if exp_frac_part == '0':
            result = int_result
            final_dec_places = int_dec_places
        else:
            # Generate binary sequence (max bits = 4 * HCTOL, replicating C logic)
            binary_fraction = _dec2bin_fraction(exp_frac_part, 4 * HCTOL)
            
            # Calculate fractional power
            frac_result, frac_dec_places = _huge_powerf(pure_mag1, dec_places1, binary_fraction, HCTOL)
            
            # Multiply integer and fractional results
            result = huge_prod(int_result, frac_result)
            final_dec_places = int_dec_places + frac_dec_places
            
        # 5. Re-insert the decimal point
        result = _insert_decimal(result, final_dec_places)
        
        # 6. Determine sign (negative base ^ odd exponent = negative result)
        result_sign = '+'
        if sign1 == '-':
            last_digit = int(exp_int_part[-1]) if exp_int_part != '0' else 0
            if last_digit % 2 != 0:
                result_sign = '-'

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
        # Interactive Mode (or simple file redirection): print labeled and formatted result

        formatted_result = _format_with_commas(raw_result)

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

        else:
            label = "    RESULT" # Should not happen with current operators

        print(f"{label}: {formatted_result}")

        if raw_remainder is not None:
            # Only print remainder for division
            formatted_remainder = _format_with_commas(raw_remainder)
            print(f" REMAINDER: {formatted_remainder}")

    else:
        # Piped Mode: print only the raw, unformatted result (quotient)
        # This raw result becomes the input for the next command in the pipe.
        print(raw_result)
