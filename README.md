# HugeCalc: Arbitrary-Precision Scientific Calculator

HugeCalc is a command-line scientific calculator that bypasses standard hardware memory limits by representing numbers as strings of ASCII digits. Originally conceived in 1991 as an integer-based string-math engine, the project has evolved over 35 years into a modern Python framework capable of executing continuous complex mathematics and Newton-Raphson root solving out to 40 digits of precision.

## The History & Evolution

### 1991: The Turbo Pascal Origins
Having cut my teeth on early home computers like the TRS-80 a decade prior, the concept of bypassing strict hardware variable limits using pure algorithmic string mathematics was fascinating. This project began by manually typing Neil J. Rubenking's original Turbo Pascal code by hand, directly from the pages of the September 1991 issue of *PC Magazine*. The original engine utilized inline assembler and raw DOS memory interrupts to perform mathematics using the exact same step-by-step techniques a human would use on paper. 

### 1991–2000: The C Port
To keep the engine alive beyond the DOS era, I ported the original Turbo Pascal architecture to C. Applying my limited knowledge of C, this era of the project focused on translating the original Turbo Pascal and inline assembler into a standard C environment, preserving the string-math engine while making the utility portable.

### 2025–2026: Python Modernization & Continuous Math
Today, rigorous modeling and simulation environments require robust, high-precision continuous mathematics. This latest iteration ports the engine to Python, achieving a massive expansion in capability while preserving the legacy integer operations. 

**Modern Features:**
*   **Exact Integer Logic:** Full restoration of the 1991 exact integer quotient and remainder string logic.
*   **Continuous Mathematics:** Implementation of Maclaurin series expansions for high-speed transcendental operations (trigonometry, natural logarithms, exponentials).
*   **Complex Plane Support:** Spouge's approximation and Gamma functions for continuous factorials and complex mathematics.
*   **Arbitrary-Precision Root Finding (`hcsolver.py`):** Quadratic-convergence Newton-Raphson solvers capable of targeting extreme geometric curves (e.g., $x^{10} = 10$) seamlessly out to 40 significant digits.

## Usage

HugeCalc operates directly from the command line, supporting binary, prefix, postfix, and pipeline chaining:

```bash
# True rational division
python hugecalc.py 100 / 3

# Legacy exact square root cascade
python hugecalc.py 16 ^^ 1/2

# Continuous Gamma Factorial
python hugecalc.py 52 !

# Piped pipeline formatting
python hugecalc.py exp 2 | python hugecalc.py round 15
```

## Repository Structure
*   **Root (`/`)**: The core Python 3 string-math engine (`hugecalc.py`), the advanced root-finding module (`hcsolver.py`), and the validation test suite (`test_hugecalc.py`).
*   **`/archive`**: A historical time capsule containing the original 1991 `.pas` files, the 1990s `.c` and `.h` adaptations, and the iterative file history of the Python port.

## License
MIT License. See the `LICENSE` file for details.
*Original HUGECALC Turbo Pascal architecture Copyright (c) 1991 Neil J. Rubenking.* 
