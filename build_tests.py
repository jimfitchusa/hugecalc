import csv

CSV_FILE = "tests.csv"
OUTPUT_FILE = "test_hugecalc.py"

HEADER = """import unittest
import subprocess
import os
import sys

CALC_SCRIPT = "hugecalc.py"
DEFAULT_ENV = {
    "HCTOL": "25",
    "HCFORMAT": "DEC",
    "HC_BENCHMARK": "1"
}

class TestHugeCalc(unittest.TestCase):

    def run_calc(self, *args, env_vars=None):
        cmd = ["python", CALC_SCRIPT] + list(args)
        env = os.environ.copy()
        env.update(DEFAULT_ENV)

        # Force the engine to format output as if it were a human terminal
        env["HC_FORCE_TTY"] = "1"

        if env_vars:
            env.update(env_vars)
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def run_pipe(self, command_string, env_vars=None):
        env = os.environ.copy()
        env.update(DEFAULT_ENV)
        if env_vars:
            env.update(env_vars)

        # Cross-platform shell sanitation for the legacy power operator
        if os.name != 'nt':
            # Demote Windows CMD escaped carets back to literal strings for Bash/Zsh
            command_string = command_string.replace('^^^^', '^^').replace(' ^^ ', ' ^ ')

        result = subprocess.run(command_string, capture_output=True, text=True, shell=True, env=env)
        return result.stdout.strip(), result.stderr.strip(), result.returncode

"""

STATIC_TESTS = """

from hugecalc import HugeFloat, _format_with_commas

class TestHugeFloatFormatting(unittest.TestCase):

    def test_decimal_interactive_output(self):
        hf = HugeFloat("-40", 25)
        dec_string = hf.to_dec_string()
        self.assertEqual(dec_string, "-40")
        final_output = _format_with_commas(dec_string)
        self.assertEqual(final_output, "-40")

    def test_scientific_interactive_output(self):
        hf = HugeFloat("14142e-4", 25)
        sci_string = hf.to_sci_string()
        self.assertEqual(sci_string, "1.4142e0")

    def test_comma_formatter_large_numbers(self):
        formatted = _format_with_commas("-1234567.89")
        self.assertEqual(formatted, "-1,234,567.89")

"""

def generate_tests():
    test_methods = []
    test_count = 0

    with open(CSV_FILE, newline='') as csvfile:
        # 1. Swap all tabs for spaces on the fly
        clean_lines = (line.replace('\t', ' ') for line in csvfile)

        # 2. Feed the cleaned lines into the reader
        reader = csv.reader(clean_lines, skipinitialspace=True)

        for row in reader:
            # Skip empty rows or commented rows
            if not row or row[0].strip().startswith('#'):
                continue

            name = row[0].strip()
            command = row[1].strip()
            expected = row[2].strip()
            code = int(row[3].strip())

            # --- NEW: Optional Environment Variables Parsing ---
            env_vars_str = ""
            if len(row) > 4:
                env_string = row[4].strip()
                if env_string:
                    # Splits "HCTOL 2" into key="HCTOL", val="2"
                    parts = env_string.split()
                    if len(parts) >= 2:
                        key, val = parts[0], parts[1]
                        # Formats into Python kwarg: env_vars={"HCTOL": "2"}
                        env_vars_str = f', env_vars={{"{key}": "{val}"}}'
            # ---------------------------------------------------

            test_count += 1

            # Determine execution method and inject env_vars if present
            if '|' in command or '>' in command:
                exec_line = f'        out, err, code = self.run_pipe("{command}"{env_vars_str})'
            else:
                args = [f'"{arg}"' for arg in command.split()]
                exec_line = f'        out, err, code = self.run_calc({", ".join(args)}{env_vars_str})'

            # Determine assertion logic based on exit code
            if code == 0:
                if '&&' in expected:
                    parts = [e.strip() for e in expected.split('&&')]
                    assert_lines = [f'        self.assertIn("{p}", out)' for p in parts]
                    assert_line = f'        self.assertEqual(code, 0)\n' + '\n'.join(assert_lines)
                else:
                    assert_line = f'        self.assertEqual(code, 0)\n        self.assertIn("{expected}", out)'
            else:
                assert_line = f'        self.assertNotEqual(code, 0)\n        self.assertIn("{expected}", err)'

            method = f"    def test_{test_count:03d}_{name}(self):\n{exec_line}\n{assert_line}\n"
            test_methods.append(method)

    FOOTER = f"""
if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    expected_total = {test_count + 3}  # CSV tests + 3 static formatting tests

    if suite.countTestCases() != expected_total:
        print(f"ERROR: Expected {{expected_total}} tests, found {{suite.countTestCases()}}.")
        sys.exit(1)

    unittest.main()
"""

    with open(OUTPUT_FILE, 'w') as f:
        f.write(HEADER)
        f.write("\n".join(test_methods))
        f.write(STATIC_TESTS)
        f.write(FOOTER)

    print(f"Successfully generated {OUTPUT_FILE} with {test_count + 3} total tests.")


if __name__ == "__main__":
    generate_tests()
