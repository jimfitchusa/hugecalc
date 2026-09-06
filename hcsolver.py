import subprocess
import os

def hc_eval(command_string):
    """Fires a command to hugecalc, natively supporting chained pipe '|' operations."""
    stages = [stage.strip() for stage in command_string.split('|')]

    current_input = None
    for stage in stages:
        cmd = ['python', 'hugecalc.py'] + stage.split()

        if current_input:
            # Feed the previous output into the stdin of the current hugecalc stage
            result = subprocess.run(cmd, input=current_input, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)

        if not result.stdout.strip():
            raise ValueError(f"hugecalc failed at '{stage}': {result.stderr}")

        current_input = result.stdout.strip()

    return current_input


def format_dec(raw_str):
    """Converts raw piped output (e.g., '+25e-1') to a readable decimal string."""
    if 'e' not in raw_str:
        return raw_str

    sign = '-' if raw_str.startswith('-') else ''
    core = raw_str.lstrip('+-')
    mantissa, exp_str = core.split('e')
    exp = int(exp_str)

    if exp >= 0:
        return sign + mantissa + ('0' * exp)

    dec_places = abs(exp)
    if len(mantissa) <= dec_places:
        mantissa = mantissa.zfill(dec_places + 1)

    insert_pos = len(mantissa) - dec_places
    res = mantissa[:insert_pos] + '.' + mantissa[insert_pos:]

    # Clean up trailing decimal zeros
    if '.' in res:
        res = res.rstrip('0').rstrip('.')
    return sign + (res or '0')


def format_error(raw_str):
    """Formats errors cleanly, switching to SCI if sig-figs are pushed past 35 chars."""
    if raw_str in ('0', '+0e0', '-0e0'):
        return '0'

    dec_str = format_dec(raw_str)
    truncated = dec_str[:35]

    # Check if the visible portion is entirely zeros (e.g., "0.0000000...")
    # If the truncated part is empty of non-zero digits, our data fell off the screen.
    if not truncated.lstrip('-').replace('.', '').strip('0'):
        sign = '-' if raw_str.startswith('-') else ''
        core = raw_str.lstrip('+-')

        if 'e' in core:
            mantissa, exp_str = core.split('e')
            sci_exp = int(exp_str) + len(mantissa) - 1
            sci_mantissa = mantissa[0] + '.' + mantissa[1:] if len(mantissa) > 1 else mantissa
            return f"{sign}{sci_mantissa}e{sci_exp}"

    return dec_str


def bisect_solve(equation_template, target, low_str, high_str, hctol):
    working_tol = hctol + 5
    clean_eq = equation_template.replace('{x}', 'x')
    print(f"Hunting for {clean_eq} = {target} (Targeting {hctol} digits)...")

    # Evaluate boundaries to determine function direction
    y_low = hc_eval(equation_template.format(x=low_str))
    y_high = hc_eval(equation_template.format(x=high_str))

    direction_check = hc_eval(f"{y_high} - {y_low}")
    is_increasing = not direction_check.startswith('-')

    iterations = int(working_tol * 3.4) + 10
    last_rounded = ""
    stable_count = 0

    for i in range(iterations):
        sum_val = hc_eval(f"{low_str} + {high_str}")
        mid_str = hc_eval(f"{sum_val} / 2")

        guess_res = hc_eval(equation_template.format(x=mid_str))
        error_diff = hc_eval(f"{guess_res} - {target}")

        current_rounded = hc_eval(f"{mid_str} round {hctol}")

        disp_x = format_dec(mid_str)
        disp_err = format_error(error_diff)
        print(f"Iter {i+1:02d} | x = {disp_x[:35]:<35} | Error = {disp_err[:35]}")

        if error_diff in ('0', '+0e0', '-0e0'):
            print("\nExact absolute convergence reached!")
            return format_dec(current_rounded)

        if current_rounded == last_rounded:
            stable_count += 1
            if stable_count >= 2:
                print(f"\nTolerance reached! Result stabilized at {hctol} digits.")
                return format_dec(current_rounded)
        else:
            stable_count = 0
            last_rounded = current_rounded

        if error_diff.startswith('-'):
            if is_increasing: low_str = mid_str
            else: high_str = mid_str
        else:
            if is_increasing: high_str = mid_str
            else: low_str = mid_str

    print(f"\nWARNING: Maximum iterations ({iterations}) reached without reaching stable tolerance.")
    return format_dec(current_rounded)


def newton_solve(equation_template, deriv_template, target, guess_str, hctol):
    clean_eq = equation_template.replace('{x}', 'x')
    print(f"Newton Hunting for {clean_eq} = {target} (Targeting {hctol} digits)...")

    working_tol = hctol + 5
    iterations = int(working_tol * 3.4) + 10
    last_rounded = ""
    stable_count = 0
    current_x = guess_str

    for i in range(iterations):
        f_val = hc_eval(equation_template.format(x=current_x))
        f_prime = hc_eval(deriv_template.format(x=current_x))

        error_val = hc_eval(f"{f_val} - {target}")
        step_val = hc_eval(f"{error_val} / {f_prime}")
        current_x = hc_eval(f"{current_x} - {step_val}")

        current_rounded = hc_eval(f"{current_x} round {hctol}")

        disp_x = format_dec(current_x)
        disp_err = format_error(error_val)
        print(f"Iter {i+1:02d} | x = {disp_x[:35]:<35} | Error = {disp_err[:35]}")

        if error_val in ('0', '+0e0', '-0e0'):
            print("\nExact absolute convergence reached!")
            return format_dec(current_rounded)

        if current_rounded == last_rounded:
            stable_count += 1
            if stable_count >= 2:
                print(f"\nTolerance reached! Result stabilized at {hctol} digits.")
                return format_dec(current_rounded)
        else:
            stable_count = 0
            last_rounded = current_rounded

    print(f"\nWARNING: Maximum iterations ({iterations}) reached without stable tolerance.")
    return format_dec(current_rounded)


if __name__ == "__main__":
    # Inherit HCTOL from the environment to dynamically scale the search loop
    hctol = int(os.environ.get('HCTOL', 25))

#    final_x = bisect_solve('{x} / 1000', '0', '-0.17', '0.1', hctol)
#    print(f"\nFinal Result: {final_x}")

#    final_x = bisect_solve('cos {x}', '0.9', '0.4', '0.5', hctol)
#    print(f"\nFinal Result: {final_x}")

#    final_x = bisect_solve('cos {x}', '0.9', '0.5', '0.4', hctol)
#    print(f"\nFinal Result: {final_x}")

    final_x = bisect_solve('{x} ^ 10', '10', '1', '10', hctol)
    print(f"\nFinal Result: {final_x}")

    r'''
        Calling the Newton SolverInstead of passing a low and high bracket, you pass the equation, its derivative, the target, and a single initial guess:Natural Log (Solving $\ln(x) = 1$): The derivative of $\ln(x)$ is $1/x$.newton_solve('ln {x}', '1 / {x}', '1', '2.5', hctol)Cosine (Solving $\cos(x) = 0.9$): The derivative of $\cos(x)$ is $-\sin(x)$.(Note: you'll need to multiply by -1 depending on how your hugecalc syntax parses negatives)newton_solve('cos {x}', '-1 * sin {x}', '0.9', '0.45', hctol)
    '''

#    final_x = newton_solve('cos {x}', 'sin {x} | * -1', '0.9', '0.45', hctol)
#    print(f"\nFinal Result: {final_x}")

#    final_x = newton_solve('{x} ^ 10', '{x} ^ 10 | * 10', '10', '1', hctol)
#    print(f"\nFinal Result: {final_x}")
