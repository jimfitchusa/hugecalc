import unittest
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

    def test_001_addition_basic(self):
        out, err, code = self.run_calc("123", "+", "456")
        self.assertEqual(code, 0)
        self.assertIn("579", out)

    def test_002_subtraction_negative(self):
        out, err, code = self.run_calc("10", "-", "50")
        self.assertEqual(code, 0)
        self.assertIn("-40", out)

    def test_003_machine_epsilon_bypass(self):
        out, err, code = self.run_calc("5e50", "+", "1e-10")
        self.assertEqual(code, 0)
        self.assertIn("5e50", out)

    def test_004_exact_trig_roots(self):
        out, err, code = self.run_calc("cosd", "90")
        self.assertEqual(code, 0)
        self.assertIn("0", out)

    def test_005_sqrt_2(self):
        out, err, code = self.run_calc("2", "^^", "1/2")
        self.assertEqual(code, 0)
        self.assertIn("1.414213562373095048801689", out)

    def test_006_sqrt_2a(self):
        out, err, code = self.run_calc("2", "^", "1/2")
        self.assertEqual(code, 0)
        self.assertIn("1.414213562373095048801689", out)

    def test_007_10_power_0p511(self):
        out, err, code = self.run_calc("10", "^^", "0.511")
        self.assertEqual(code, 0)
        self.assertIn("3.243396173493492447843998", out)

    def test_008_10_power_0p511a(self):
        out, err, code = self.run_calc("10", "^", "0.511")
        self.assertEqual(code, 0)
        self.assertIn("3.243396173493492447843998", out)

    def test_009_Rational_Binary_Math(self):
        out, err, code = self.run_calc("3/4", "+", "1/4")
        self.assertEqual(code, 0)
        self.assertIn("1", out)

    def test_010_Rational_Exponents(self):
        out, err, code = self.run_calc("16", "^^", "1/2")
        self.assertEqual(code, 0)
        self.assertIn("4", out)

    def test_011_Rational_Exponentsa(self):
        out, err, code = self.run_calc("16", "^", "1/2")
        self.assertEqual(code, 0)
        self.assertIn("4", out)

    def test_012_Pi_Interception(self):
        out, err, code = self.run_calc("sin", "pi")
        self.assertEqual(code, 0)
        self.assertIn("0", out)

    def test_013_Trig_Roots_Degrees(self):
        out, err, code = self.run_calc("sind", "180")
        self.assertEqual(code, 0)
        self.assertIn("0", out)

    def test_014_Dynamic_HCTOL_Protection(self):
        out, err, code = self.run_calc("1000", "*", "1000", env_vars={"HCTOL": "2"})
        self.assertEqual(code, 0)
        self.assertIn("1,000,000", out)

    def test_015_Complex_Factorial(self):
        out, err, code = self.run_calc("1+1i", "!", env_vars={"HCTOL": "5"})
        self.assertEqual(code, 0)
        self.assertIn("0.65297+0.34307i", out)

    def test_016_complex_root_1(self):
        out, err, code = self.run_pipe("python hugecalc.py -8 ^^ 1/2 | python hugecalc.py round 25")
        self.assertEqual(code, 0)
        self.assertIn("2.828427124746190097603377i", out)

    def test_017_complex_root_2(self):
        out, err, code = self.run_calc("-8", "^", "1/2")
        self.assertEqual(code, 0)
        self.assertIn("2.828427124746190097603377i", out)

    def test_018_divide_by_zero(self):
        out, err, code = self.run_calc("10", "/", "0")
        self.assertNotEqual(code, 0)
        self.assertIn("Division by zero", err)

    def test_019_tangent_asymptote(self):
        out, err, code = self.run_calc("tand", "90")
        self.assertNotEqual(code, 0)
        self.assertIn("Tangent asymptote", err)

    def test_020_Logarithm_Domain(self):
        out, err, code = self.run_calc("ln", "-5")
        self.assertEqual(code, 0)
        self.assertIn("1.609437912434100374600759+3.141592653589793238462643i", out)

    def test_021_Logarithm_Domaina(self):
        out, err, code = self.run_calc("ln", "0")
        self.assertNotEqual(code, 0)
        self.assertIn("Logarithm is only defined for positive numbers", err)

    def test_022_chained_power_pipe(self):
        out, err, code = self.run_pipe("python hugecalc.py 19 ^^^^ 3/2 | python hugecalc.py ^^^^ 2 | python hugecalc.py ^^^^ 1/3 | python hugecalc.py round 2")
        self.assertEqual(code, 0)
        self.assertIn("19e0", out)

    def test_023_chained_power_pipea(self):
        out, err, code = self.run_pipe("python hugecalc.py 19 ^^ 3/2 | python hugecalc.py ^^ 2 | python hugecalc.py ^^ 1/3 | python hugecalc.py round 2")
        self.assertEqual(code, 0)
        self.assertIn("19e0", out)

    def test_024_Complex_Multiply(self):
        out, err, code = self.run_calc("2.5+1.5i", "*", "1.2-3.4i")
        self.assertEqual(code, 0)
        self.assertIn("8.1-6.7i", out)

    def test_025_Cmplex_Sine(self):
        out, err, code = self.run_calc("sin", "2+1i")
        self.assertEqual(code, 0)
        self.assertIn("1.403119250622040588019491-0.4890562590412936735864546i", out)

    def test_026_Inverse_Cosine(self):
        out, err, code = self.run_calc("acos", "5+2i")
        self.assertEqual(code, 0)
        self.assertIn("0.3865646425198747179443653-2.370548537317919720320337i", out)

    def test_027_legacy_divsion(self):
        out, err, code = self.run_calc("10", "//", "3")
        self.assertEqual(code, 0)
        self.assertIn("QUOTIENT: 3", out)
        self.assertIn("REMAINDER: 1", out)

    def test_028_modulo_divsion(self):
        out, err, code = self.run_calc("71", "%", "27")
        self.assertEqual(code, 0)
        self.assertIn("REMAINDER: 17", out)

    def test_029_modulo_divsiona(self):
        out, err, code = self.run_calc("71", "mod", "27")
        self.assertEqual(code, 0)
        self.assertIn("REMAINDER: 17", out)

    def test_030_hyp_sin(self):
        out, err, code = self.run_calc("sinh", "pi/2")
        self.assertEqual(code, 0)
        self.assertIn("2.30129890230729487346304", out)

    def test_031_hyp_cos(self):
        out, err, code = self.run_calc("cosh", "4.578")
        self.assertEqual(code, 0)
        self.assertIn("48.66491787204328533534201", out)

    def test_032_hyp_tan(self):
        out, err, code = self.run_calc("tanh", "22.7")
        self.assertEqual(code, 0)
        self.assertIn("0.9999999999999999999616239", out)

    def test_033_arc_hyp_sin(self):
        out, err, code = self.run_calc("asinh", "pi/2")
        self.assertEqual(code, 0)
        self.assertIn("1.233403117511217057073108", out)

    def test_034_arc_hyp_cos(self):
        out, err, code = self.run_calc("acosh", "4.578")
        self.assertEqual(code, 0)
        self.assertIn("2.202261553307189072328421", out)

    def test_035_arc_hyp_tan(self):
        out, err, code = self.run_calc("atanh", "22.7")
        self.assertEqual(code, 0)
        self.assertIn("0.04408139379733581726683686+1.570796326794896619231322i", out)

    def test_036_roots(self):
        out, err, code = self.run_calc("2", "roots", "3")
        self.assertEqual(code, 0)
        self.assertIn("ROOTS: 1.259921049894873164767211", out)
        self.assertIn("-0.6299605249474365823836053+1.091123635971721403560073i", out)
        self.assertIn("-0.6299605249474365823836053-1.091123635971721403560073i", out)

    def test_037_polar(self):
        out, err, code = self.run_calc("polar", "1+2i")
        self.assertEqual(code, 0)
        self.assertIn("POLAR: 2.236067977499789696409174 * e^(1.107148717794090503017065i)", out)

    def test_038_rect(self):
        out, err, code = self.run_calc("2.236067977499789696409174", "rect", "1.107148717794090503017065")
        self.assertEqual(code, 0)
        self.assertIn("RECT: 1.000000000000000000000001+2i", out)

    def test_039_factorial_domain(self):
        out, err, code = self.run_calc("-5", "!")
        self.assertNotEqual(code, 0)
        self.assertIn("Factorial is undefined for negative integers", err)

    def test_040_factorial_domaina(self):
        out, err, code = self.run_calc("-5.1", "!", env_vars={"HCTOL": "5"})
        self.assertEqual(code, 0)
        self.assertIn("-0.36397", out)

    def test_041_negative_power_domain(self):
        out, err, code = self.run_calc("5", "^", "-2")
        self.assertEqual(code, 0)
        self.assertIn("0.04", out)

    def test_042_negative_complex_power(self):
        out, err, code = self.run_calc("5", "^", "-i")
        self.assertEqual(code, 0)
        self.assertIn("-0.03863196993393542627161533-0.9992535068234804595112378i", out)

    def test_043_negative_complex_powera(self):
        out, err, code = self.run_calc("5", "^^", "-i")
        self.assertEqual(code, 0)
        self.assertIn("-0.03863196993393542627161533-0.9992535068234804595112378i", out)

    def test_044_arcsine_degree_domain(self):
        out, err, code = self.run_calc("asind", "2")
        self.assertNotEqual(code, 0)
        self.assertIn("Domain error: arcsine is only defined for -1 <= x <= 1", err)

    def test_045_arccos_degree_domain(self):
        out, err, code = self.run_calc("acosd", "2")
        self.assertNotEqual(code, 0)
        self.assertIn("Domain error: arccosine is only defined for -1 <= x <= 1", err)

    def test_046_Absolute_Zero_Culling(self):
        out, err, code = self.run_pipe("python hugecalc.py 1e-30 + 0 | python hugecalc.py round 25")
        self.assertEqual(code, 0)
        self.assertIn("0", out)

    def test_047_sci_threshold_trigger(self):
        out, err, code = self.run_calc("1", "*", "1e15")
        self.assertEqual(code, 0)
        self.assertIn("1e15", out)

    def test_048_sci_threshold_bypass(self):
        out, err, code = self.run_calc("1", "*", "1e14")
        self.assertEqual(code, 0)
        self.assertIn("100,000,000,000,000", out)

    def test_049_factorial_zero(self):
        out, err, code = self.run_calc("0", "!")
        self.assertEqual(code, 0)
        self.assertIn("1", out)

    def test_050_factorial_one(self):
        out, err, code = self.run_calc("1", "!")
        self.assertEqual(code, 0)
        self.assertIn("1", out)

    def test_051_zero_base_power(self):
        out, err, code = self.run_calc("0", "^", "5")
        self.assertEqual(code, 0)
        self.assertIn("0", out)

    def test_052_modulo_domain_rejection(self):
        out, err, code = self.run_calc("5e-1", "%", "2")
        self.assertNotEqual(code, 0)
        self.assertIn("Integer division requires integers", err)

    def test_053_zero_power_zero(self):
        out, err, code = self.run_calc("0", "^", "0")
        self.assertEqual(code, 0)
        self.assertIn("1", out)


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


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    expected_total = 56  # CSV tests + 3 static formatting tests

    if suite.countTestCases() != expected_total:
        print(f"ERROR: Expected {expected_total} tests, found {suite.countTestCases()}.")
        sys.exit(1)

    unittest.main()
