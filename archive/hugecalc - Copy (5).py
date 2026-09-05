"""
12 Nov 2025
Looking at hugecalc again, but now looking to convert the C program into a Python script.

I'm taking this one tiny step at a time and using Gemini AI to assist.

First, get the script to parse the command line input into operand1, operator, operand2.
Second, implement addition and subtraction, including handling of negative inputs and results.
Third, implement result formatting (commas) and pipe/redirection detection for output.
"""

import sys

# Define the global help message
HELPMESSAGE = """\
Usage: python hugecalc.py <operand1> <operation> <operand2>
       (or use pipe: python hugecalc.py 1 + 2 | python hugecalc.py + 3)

Example: python hugecalc.py -123 + 456  (Addition with negative input)
Example: python hugecalc.py 100 - 50    (Subtraction)

Supported operations: +, -
Future support: *, /, ^, and ! (factorial)
"""

VALID_OPERATORS = {'+', '-'}

def usage():
    """Prints the usage/help message and exits."""
    print(HELPMESSAGE)
    sys.exit(1)


def _is_huge_digit(s: str) -> bool:
    """Checks if a string is a valid integer, optionally allowing a leading minus sign."""
    if not s:
        return False
    if s[0] == '-':
        # If it starts with '-', the rest must be digits
        return s[1:].isdigit()
    # Otherwise, the whole string must be digits
    return s.isdigit()


def parse_and_validate():
    """
    Parses command-line arguments and validates them against the current functionality constraints.
    Returns: (operand1: str, operation: str, operand2: str)
    """
    # We expect 4 items: [script_name, op1, op, op2]
    if len(sys.argv) != 4:
        # Check for pipe input format: py hugecalc.py + 3
        # In a pipe, op1 comes from stdin (piped data), and we only get [script_name, op, op2]
        if len(sys.argv) == 3 and sys.stdin.isatty() is False:
             # Read op1 from stdin (piped data)
            piped_input = sys.stdin.read().strip()
            
            # Check if piped input is a valid number
            if not _is_huge_digit(piped_input):
                 print("Error: Piped input must be a valid integer string.")
                 usage()
            
            # Assign piped input as op1, and shift remaining args
            operand1 = piped_input
            operation = sys.argv[1]
            operand2 = sys.argv[2]
            
        else:
            # Not enough arguments and not piped data
            print("Error: Expected three arguments (operand1, operation, operand2) or piped input.")
            usage()
    else:
        # Standard 3-argument input
        operand1 = sys.argv[1]
        operation = sys.argv[2]
        operand2 = sys.argv[3]

    # --- Validation Checks ---
    
    # 1. Operation check
    if operation not in VALID_OPERATORS:
        print(f"Error: Operation '{operation}' is not yet supported.\n"
              f"Only {VALID_OPERATORS} are implemented.")
        usage()

    # 2. Operand checks (must be integers, allowing negative)
    if not _is_huge_digit(operand1):
        print(f"Error: Operand 1 ('{operand1}') must be an integer string.")
        usage()

    if not _is_huge_digit(operand2):
        print(f"Error: Operand 2 ('{operand2}') must be an integer string.")
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


def get_sign_and_magnitude(operand: str) -> tuple[str, str]:
    """Extracts the sign and the non-negative magnitude string from an operand."""
    if operand.startswith('-'):
        return '-', operand[1:] or '0'
    return '+', operand


def calculate(op1: str, op: str, op2: str) -> tuple[str, str]:
    """
    Routes the actual huge-number operation based on input operator and operand signs.
    Returns: (operator: str, result_string: str)
    Original operator is modified if resulting operation is changed (such as 1 - -2 results in addition).
    """
    # 1. Separate signs and magnitudes
    sign1, mag1 = get_sign_and_magnitude(op1)
    sign2, mag2 = get_sign_and_magnitude(op2)
    
    result = ""

    # 2. Handle the four core cases by normalizing to ADD or SUB on magnitudes
    
    # Case A: Addition (op1 + op2)
    if op == '+':
        if sign1 == '+' and sign2 == '+':
            # (+A) + (+B) = A + B
            result = huge_add(mag1, mag2)
        
        elif sign1 == '-' and sign2 == '-':
            # (-A) + (-B) = -(A + B)
            result = '-' + huge_add(mag1, mag2)
            
        elif sign1 == '+' and sign2 == '-':
            # (+A) + (-B) = A - B
            op = '-'
            result = huge_sub(mag1, mag2)
            
        elif sign1 == '-' and sign2 == '+':
            # (-A) + (+B) = B - A
            op = '-'
            result = huge_sub(mag2, mag1)

    # Case B: Subtraction (op1 - op2)
    elif op == '-':
        if sign1 == '+' and sign2 == '+':
            # (+A) - (+B) = A - B
            result = huge_sub(mag1, mag2)
            
        elif sign1 == '-' and sign2 == '-':
            # (-A) - (-B) = -A + B = B - A
            result = huge_sub(mag2, mag1)
            
        elif sign1 == '+' and sign2 == '-':
            # (+A) - (-B) = A + B
            op = '+'
            result = huge_add(mag1, mag2)
            
        elif sign1 == '-' and sign2 == '+':
            # (-A) - (+B) = -(A + B)
            op = '+'
            result = '-' + huge_add(mag1, mag2)
    
    # Should not be reached due to validation
    return op, result if result else '0'


def _format_with_commas(number_str: str) -> str:
    """Inserts commas into the whole number part of a string representation of a number."""
    if not number_str:
        return '0'

    # Check for sign
    sign = ''
    if number_str.startswith('-'):
        sign = '-'
        number_str = number_str[1:]

    # For now, we assume no decimals
    
    # Reverse the string to insert commas from the right
    reversed_digits = number_str[::-1]
    
    parts = []
    # Iterate and slice every 3 characters
    for i in range(0, len(reversed_digits), 3):
        parts.append(reversed_digits[i:i + 3])
    
    # Re-reverse the parts and join with commas
    formatted_number = ','.join(parts)[::-1]
    
    return sign + formatted_number


if __name__ == "__main__":
    # Get the validated operands and operation
    op1, op, op2 = parse_and_validate()
    
    # Route the operation based on signs
    original_op, raw_result = calculate(op1, op, op2)
    
    # Check if the output is being redirected (piped)
    if sys.stdout.isatty():
        # Interactive Mode (or simple file redirection): print labeled and formatted result
        
        formatted_result = _format_with_commas(raw_result)
        
        if original_op == '+':
            label = "       SUM"
        elif original_op == '-':
            label = "DIFFERENCE"
        else:
            label = "RESULT" # Should not happen with current operators

        print(f"{label}: {formatted_result}")

    else:
        # Piped Mode: print only the raw, unformatted result
        # This raw result becomes the input for the next command in the pipe.
        print(raw_result)
    