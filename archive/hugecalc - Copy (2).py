"""
12 Nov 2025
Looking at hugecalc again, but now looking to convert the C program into a Python script.

I'm taking this one tiny step at a time and using Gemini AI to assist.

First, get the script to parse the command line input into operand1, operator, operand2.

Second, start with just the add operation, with the assumption that operand1 and operand2 are both nonnegative integers.
"""

import sys

# Define the global help message
HELPMESSAGE = """\
Usage: python hugecalc.py <operand1> <operation> <operand2>

Example: python hugecalc.py 123456789 + 987654321

Supported operations in this version:
   - '+' (Addition only)

Future support: -, *, /, ^, and ! (factorial)
"""

def usage():
    """Prints the usage/help message and exits."""
    print(HELPMESSAGE)
    sys.exit(1)


def parse_and_validate():
    """
    Parses command-line arguments and validates them against the current functionality constraints.
    Returns: (operand1: str, operation: str, operand2: str)
    """
    # We expect 4 items: [script_name, op1, op, op2]
    if len(sys.argv) != 4:
        print("Error: Expected three arguments (operand1, operation, operand2).")
        usage()

    operand1 = sys.argv[1]
    operation = sys.argv[2]
    operand2 = sys.argv[3]

    # --- Validation Checks ---
    
    # 1. Operation check (currently only '+' is supported)
    if operation != '+':
        print(f"Error: Operation '{operation}' is not yet supported. Only '+' is implemented.")
        usage()

    # 2. Operand checks (must be non-negative integers)
    if not operand1.isdigit():
        print(f"Error: Operand 1 ('{operand1}') must be a non-negative integer string.")
        usage()

    if not operand2.isdigit():
        print(f"Error: Operand 2 ('{operand2}') must be a non-negative integer string.")
        usage()

    # Success
    return operand1, operation, operand2


def huge_add(op1_str: str, op2_str: str) -> str:
    """
    Performs character-by-character addition of two non-negative integer strings.
    This simulates the low-level carry logic of the original Pascal/C program.
    """
    # 1. Reverse the strings to process from the least significant digit (right to left)
    op1_rev = op1_str[::-1]
    op2_rev = op2_str[::-1]

    # 2. Determine the maximum length for iteration
    max_len = max(len(op1_rev), len(op2_rev))
    
    result_digits = []
    carry = 0

    # 3. Iterate through digits
    for i in range(max_len):
        # Get the digit from op1, default to 0 if op1 is shorter (implicit padding)
        digit1 = int(op1_rev[i]) if i < len(op1_rev) else 0
        
        # Get the digit from op2, default to 0 if op2 is shorter (implicit padding)
        digit2 = int(op2_rev[i]) if i < len(op2_rev) else 0

        # Calculate the sum of the digits and the current carry
        total_sum = digit1 + digit2 + carry

        # The new digit is the ones place of the total sum
        new_digit = total_sum % 10
        
        # The new carry is the tens place of the total sum
        carry = total_sum // 10
#        print(carry)

        # Append the resulting digit (as a string) to the result list
        result_digits.append(str(new_digit))

    # 4. Handle final carry
 #   if carry > 0:
    if carry:   # carry can only be 0 or 1
        result_digits.append(str(carry))

    # 5. Reverse the final list of digits and join them to form the result string
    # The result_digits are currently in reverse order (least significant first)
    final_result = "".join(result_digits[::-1])
    
    # Handle the special case of adding '0' + '0' resulting in '' or '0'
    return final_result if final_result else '0'
#    return final_result #if final_result else '0'


if __name__ == "__main__":
    # Get the validated operands and operation
    op1, op, op2 = parse_and_validate()
    
    # Perform the addition
    result = huge_add(op1, op2)
    
    # Print the result
    print(f"{op1} {op} {op2} = {result}")
