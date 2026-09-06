import unittest
import subprocess
import os

# Define the path to your script
CALC_SCRIPT = "hugecalc.py"

class TestHugeCalc(unittest.TestCase):
    
    def run_calc(self, *args, env_vars=None):
        """Helper method to execute hugecalc.py and capture the exact terminal output."""
        cmd = ["python", CALC_SCRIPT] + list(args)
        
        # Merge custom environment variables (like HCTOL) with the system environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
            
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        # Clean up whitespace and newlines from the output
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        
        return stdout, stderr, result.returncode

    # --- 1. STANDARD OPERATIONS ---
    def test_addition_basic(self):
        out, err, code = self.run_calc("123", "+", "456")
        self.assertEqual(code, 0)
        self.assertIn("579e0", out)

    def test_subtraction_negative_result(self):
        out, err, code = self.run_calc("10", "-", "50")
        self.assertEqual(code, 0)
        self.assertEqual("-4e1", out)

    # --- 2. EDGE CASES & PRECISION ---
    def test_machine_epsilon_bypass(self):
        # 5e50 + 1e-10 should bypass math and return exactly 5e50
        out, err, code = self.run_calc("5e50", "+", "1e-10")
        self.assertEqual(code, 0)
        self.assertEqual("5e50", out)
        
    def test_exact_trig_roots(self):
        out, err, code = self.run_calc("cosd", "90")
        self.assertEqual(code, 0)
        self.assertEqual("0", out)

    def test_sqrt_2(self):
        out, err, code = self.run_calc("2", "^", "1/2")
        self.assertEqual(code, 0)
        self.assertEqual("141421356237309504880168872421e-29", out)

    def test_10_power_0p511(self):
        out, err, code = self.run_calc("10", "^", "0.511")
        self.assertEqual(code, 0)
        self.assertEqual("324339617349349244784399841334e-29", out)

    # other tests
    def test_Rational_Binary_Math(self):
        out, err, code = self.run_calc("3/4", "+", "1/4")
        self.assertEqual(code, 0)
        self.assertEqual("1e0", out)

    def test_Rational_Exponents(self):
        out, err, code = self.run_calc("16", "^", "1/2")
        self.assertEqual(code, 0)
        self.assertEqual("4e0", out)

    def test_Pi_Interception(self):
        out, err, code = self.run_calc("sin", "pi")
        self.assertEqual(code, 0)
        self.assertEqual("0", out)

    def test_Trig_Roots_Degrees(self):
        out, err, code = self.run_calc("sind", "180")
        self.assertEqual(code, 0)
        self.assertEqual("0", out)

    def test_Dynamic_HCTOL_Protection(self):
        out, err, code = self.run_calc("1000", "*", "1000", env_vars={"HCTOL": "2"})
        self.assertEqual(code, 0)
        self.assertEqual("1e6", out)

    # --- 3. ERROR HANDLING ---
    def test_divide_by_zero(self):
        out, err, code = self.run_calc("10", "/", "0")
        self.assertNotEqual(code, 0)  # Expecting a failure code
        self.assertIn("Division by zero", err) # Error should route to stderr

    def test_tangent_asymptote(self):
        out, err, code = self.run_calc("tand", "90")
        self.assertNotEqual(code, 0)
        self.assertIn("Tangent asymptote", err)

    def test_Complex_Root_Trap(self):
        out, err, code = self.run_calc("-8", "^", "1/2")
        self.assertNotEqual(code, 0)
        self.assertIn("complex root", err)

    def test_Logarithm_Domain(self):
        out, err, code = self.run_calc("ln", "-5")
        self.assertNotEqual(code, 0)
        self.assertIn("Logarithm is only defined", err)

    def test_zz_expected_test_count(self):
        # You must manually update this integer every time you add a new test to this class!
        expected_tests = 16
        loaded_tests = unittest.TestLoader().loadTestsFromTestCase(TestHugeCalc).countTestCases()
        
        self.assertEqual(loaded_tests, expected_tests, "Count mismatch! Did you forget a 'test_' prefix?")


# Import your specific classes and functions directly from your script# (Assuming your file is named hugecalc.py)
from hugecalc import HugeFloat, _format_with_commas

class TestHugeFloatFormatting(unittest.TestCase):
    
    def test_decimal_interactive_output(self):
        """Tests the exact logic pipeline for HCFORMAT=DEC"""
        # 1. Instantiate the object exactly like calculate() does
        # 10 - 50 = -40. Let's pass the raw result in.
        hf = HugeFloat("-40", 25) 
        
        # 2. Call the decimal conversion method
        dec_string = hf.to_dec_string()
        self.assertEqual(dec_string, "-40")
        
        # 3. Pass it through the comma formatter
        final_output = _format_with_commas(dec_string)
        self.assertEqual(final_output, "-40")

    def test_scientific_interactive_output(self):
        """Tests the exact logic pipeline for HCFORMAT=SCI"""
        # Testing a square root result like 2 ^^ 1/2
        hf = HugeFloat("14142e-4", 25)
        
        # Call the scientific conversion method
        sci_string = hf.to_sci_string()
        
        # Validate the decimal shifts exactly 1 position after the leading digit
        self.assertEqual(sci_string, "1.4142e0")

    def test_comma_formatter_large_numbers(self):
        """Tests the standalone comma formatter directly"""
        formatted = _format_with_commas("-1234567.89")
        self.assertEqual(formatted, "-1,234,567.89")


if __name__ == '__main__':
    unittest.main()
