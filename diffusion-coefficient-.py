from numpy import log as Ln
from numpy import exp as e
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Constantes
CONSTANTS = {
    'V_exp': 1.33e-05,
    'aBA': 194.5302,
    'aAB': -10.7575,
    'lambda_A': 1.127,
    'lambda_B': 0.973,
    'qA': 1.432,
    'qB': 1.4,
    'D_AB': 2.1e-5,
    'D_BA': 2.67e-5
}


def calcul_diffusion(Xa, T):
    """Calcule les paramètres de diffusion avec gestion d'erreurs détaillée"""
    if not (0 <= Xa <= 1):
        raise ValueError("La fraction Xa doit être entre 0 et 1")
    if T <= 0:
        raise ValueError("La température doit être positive")

    Xb = 1 - Xa

    # Calculs intermédiaires
    phiA = (Xa * CONSTANTS['lambda_A']) / (Xa * CONSTANTS['lambda_A'] + Xb * CONSTANTS['lambda_B'])
    phiB = 1 - phiA

    tauxAB = e(-CONSTANTS['aAB'] / T)
    tauxBA = e(-CONSTANTS['aBA'] / T)

    tetaA = (Xa * CONSTANTS['qA']) / (Xa * CONSTANTS['qA'] + Xb * CONSTANTS['qB'])
    tetaB = 1 - tetaA

    # Calcul des termes theta
    tetaAA = tetaA / (tetaA + tetaB * tauxBA)
    tetaBB = tetaB / (tetaB + tetaA * tauxAB)
    tetaAB = (tetaA * tauxAB) / (tetaA * tauxAB + tetaB)
    tetaBA = (tetaB * tauxBA) / (tetaB * tauxBA + tetaA)

    # Calcul final
    termes = (
            Xb * Ln(CONSTANTS['D_AB']) +
            Xa * Ln(CONSTANTS['D_BA']) +
            2 * (Xa * Ln(Xa / phiA) + Xb * Ln(Xb / phiB)) +
            2 * Xb * Xa * (
                    (phiA / Xa) * (1 - CONSTANTS['lambda_A'] / CONSTANTS['lambda_B']) +
                    (phiB / Xb) * (1 - CONSTANTS['lambda_B'] / CONSTANTS['lambda_A'])
            ) +
            Xb * CONSTANTS['qA'] * (
                    (1 - tetaBA ** 2) * Ln(tauxBA) +
                    (1 - tetaBB ** 2) * tauxAB * Ln(tauxAB)
            ) +
            Xa * CONSTANTS['qB'] * (
                    (1 - tetaAB ** 2) * Ln(tauxAB) +
                    (1 - tetaAA ** 2) * tauxBA * Ln(tauxBA)
            )
    )

    solution = e(termes)
    erreur = (abs(solution - CONSTANTS['V_exp']) / CONSTANTS['V_exp']) * 100

    return {
        'lnDab': termes,
        'Dab': solution,
        'erreur': erreur,
        'Xa': Xa,
        'T': T  # Ajout de la température dans le retour
    }

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        try:
            Xa = float(request.form["Xa"])
            T = float(request.form["T"])

            data = calcul_diffusion(Xa, T)
            result = f"""
                <div class="result-box">
                    <h3>Résultats pour Xa={data['Xa']:.3f} et T={data['T']:.2f} K</h3>
                    <p>ln(Dab): <span class="value">{data['lnDab']:.5f}</span></p>
                    <p>Dab: <span class="value">{data['Dab']:.5e} cm²/s</span></p>
                    <p>Erreur relative: <span class="value"{'error' if data['erreur'] > 5 else ''}">{data['erreur']:.2f}%</span></p>
                </div>
            """

        except ValueError as ve:
            result = f"<div class='error'>{str(ve)}</div>"
        except Exception as e:
            result = f"<div class='error'>Erreur de calcul: {str(e)}</div>"

    return render_template_string("""
        <html>
        <head>
            <title>Calculateur de Diffusion</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 20px auto;
                    padding: 20px;
                }
                .form-group {
                    margin-bottom: 15px;
                }
                label {
                    display: inline-block;
                    width: 150px;
                }
                input[type="text"] {
                    width: 200px;
                    padding: 5px;
                }
                button {
                    padding: 8px 20px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                .result-box {
                    margin-top: 20px;
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background-color: #f9f9f9;
                }
                .value {
                    color: #2c3e50;
                    font-weight: bold;
                }
                .error {
                    color: #e74c3c;
                    margin-top: 15px;
                    padding: 10px;
                    border: 1px solid #e74c3c;
                    border-radius: 4px;
                }
                .error .value {
                    color: #e74c3c;
                }
                h3 {
                    color: #34495e;
                    margin-top: 0;
                }
            </style>
        </head>
        <body>
            <h2>Calculateur de Diffusion</h2>
            <form method="POST">
                <div class="form-group">
                    <label for="Xa">Fraction Xa (0-1):</label>
                    <input type="number" name="Xa" step="0.01" min="0" max="1" required>
                </div>
                <div class="form-group">
                    <label for="T">Température (K):</label>
                    <input type="number" name="T" step="0.01" min="0.01" required>
                </div>
                <button type="submit">Calculer</button>
            </form>
            {% if result %}
                {{ result|safe }}
            {% endif %}
        </body>
        </html>
    """, result=result)


if __name__ == "__main__":
    app.run(debug=True)