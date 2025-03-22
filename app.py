import sympy
from flask import Flask, request, jsonify
from sympy import sympify, simplify, integrate, Integral, symbols, N, pi
from sympy.parsing.latex import parse_latex
from flask_cors import CORS  # Install: pip install Flask-CORS
import ast  # Import ast for safe evaluation
import re
from sympy import Matrix
from pprint import pprint
from sympy.parsing.latex import parse_latex

app = Flask(__name__)
CORS(app)


def latex_to_matrix(latex_matrix: str) -> Matrix:
    """This function convert latex matrix into sympy matrix"""

    pattern = r"\\begin\{pmatrix\}(.*?)\\end\{pmatrix\}"
    data = re.search(pattern, latex_matrix)[1]
    rows = data.split("\\\\")
    python_matrix = []
    for row in rows:
        elements_list = row.split("&")
        python_matrix.append(elements_list)
    sympy_matrix = []
    for row in python_matrix:
        sympy_row = [parse_latex(element) for element in row]
        sympy_matrix.append(sympy_row)
    return Matrix(sympy_matrix)

def my_parse_latex(latex_string):
    """Parses LaTeX and replaces log with the correct base-10 log."""
    try:
        expr = parse_latex(latex_string)
    except sympy.SympifyError:  # Handle parsing errors gracefully
        return None

    if expr is not None:
        # Correctly replace log function:
        def replace_log(expr):
            if isinstance(expr, sympy.log):  # Check if it's a log instance
                return sympy.ln(expr.args[0]) / sympy.ln(10)  # Correct replacement
            return expr  # Return the expression unchanged if it's not a log

        expr = expr.replace(lambda e: True, replace_log)  # Replace log function
        return expr
    return None

@app.route('/')
def index():
    return "Hello!"

@app.route('/check_latex', methods=['POST'])
def compare_latex():
    try:
        data = request.get_json()
        latex1 = data.get('latex1')
        latex2 = data.get('latex2')
        latexType = data.get('latexType')
        if not latexType:
            latexType = "Simple"

        if not latex1 or not latex2:
            return jsonify({'error': 'Missing latex1 or latex2'}), 400

        if "Matrix" == latexType:
            matrix1 = latex_to_matrix(latex1)
            matrix2 = latex_to_matrix(latex2)

            # 5. Compare RREF (with simplification)
            rref1 = matrix1.rref()[0]
            rref2 = matrix2.rref()[0]

            rref1_simplified = sympy.simplify(rref1)
            rref2_simplified = sympy.simplify(rref2)

            dense_rref1 = sympy.Matrix(rref1_simplified).tolist()
            dense_rref2 = sympy.Matrix(rref2_simplified).tolist()

            tolerance = 1e-9
            if len(dense_rref1) != len(dense_rref2):  # check if matrices have same dimensions
                return jsonify({"equal": False})
            for i in range(len(dense_rref1)):
                if len(dense_rref1[i]) != len(dense_rref2[i]):
                    return jsonify({"equal": False})
                for j in range(len(dense_rref1[i])):
                    if abs(dense_rref1[i][j] - dense_rref2[i][j]) > tolerance:
                        return jsonify({"equal": False})
            return jsonify({"equal": True})

        try:
            expr1 = my_parse_latex(latex1)
            expr2 = my_parse_latex(latex2)
        except Exception as e: # Catch parsing errors
           return jsonify({"error": f"Error parsing LaTeX: {e}"}), 400

        # 2. Simplify and compare
        if isinstance(expr1, Integral):
            simplified_expr1 = integrate(expr1).evalf()
            print("expr1", expr1, "simplified_expr1",    simplified_expr1)
        else:
            simplified_expr1 = simplify(expr1)
        if isinstance(expr2, Integral):
            simplified_expr2 = integrate(expr2)
            print(simplified_expr1)
        else:
            simplified_expr2 = simplify(expr2)

        is_equal = simplified_expr1 == simplified_expr2  # Careful with direct ==; consider equals()

        # More robust comparison (especially for floating-point)
        # is_equal = simplified_expr1.equals(simplified_expr2)

        return jsonify({"equal": is_equal}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Handle other errors

if __name__ == '__main__':
    app.run(debug=True)