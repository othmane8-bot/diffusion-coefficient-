from flask import Flask, request, render_template_string, redirect, url_for
from numpy import log as Ln, exp as e

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
    if not (0 <= Xa <= 1):
        raise ValueError("La fraction Xa doit être entre 0 et 1")
    if T <= 0:
        raise ValueError("La température doit être positive")
    Xb = 1 - Xa
    phiA = (Xa * CONSTANTS['lambda_A']) / (Xa * CONSTANTS['lambda_A'] + Xb * CONSTANTS['lambda_B'])
    phiB = 1 - phiA
    tauxAB = e(-CONSTANTS['aAB'] / T)
    tauxBA = e(-CONSTANTS['aBA'] / T)
    tetaA = (Xa * CONSTANTS['qA']) / (Xa * CONSTANTS['qA'] + Xb * CONSTANTS['qB'])
    tetaB = 1 - tetaA
    tetaAA = tetaA / (tetaA + tetaB * tauxBA)
    tetaBB = tetaB / (tetaB + tetaA * tauxAB)
    tetaAB = (tetaA * tauxAB) / (tetaA * tauxAB + tetaB)
    tetaBA = (tetaB * tauxBA) / (tetaB * tauxBA + tetaA)
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
        'T': T
    }

@app.route("/")
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Accueil - Calculateur de Diffusion</title>
    </head>
    <body>
        <h1>Bienvenue sur le Calculateur de Diffusion</h1>
        <p>Cliquez sur le lien ci-dessous pour accéder aux calculs.</p>
        <p><a href="{{ url_for('calcul') }}">Accéder aux Calculs</a></p>
    </body>
    </html>
    """)

@app.route("/calcul", methods=["GET", "POST"])
def calcul():
    result = ""
    if request.method == "POST":
        try:
            Xa = float(request.form["Xa"])
            T = float(request.form["T"])
            data = calcul_diffusion(Xa, T)
            result = f"""
                <h3>Résultats pour Xa = {data['Xa']:.3f} et T = {data['T']:.2f} K</h3>
                <p>ln(Dab) : {data['lnDab']:.5f}</p>
                <p>Dab : {data['Dab']:.5e} cm²/s</p>
                <p>Erreur relative : {data['erreur']:.2f}%</p>
            """
        except ValueError as ve:
            result = f"<p>Erreur : {str(ve)}</p>"
        except Exception as e:
            result = f"<p>Erreur de calcul : {str(e)}</p>"
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Calculateur de Diffusion</title>
    </head>
    <body>
        <h2>Calculateur de Diffusion</h2>
        <form method="POST">
            <label for="Xa">Fraction Xa (0-1) :</label>
            <input type="number" id="Xa" name="Xa" step="0.01" min="0" max="1" required>
            <br>
            <label for="T">Température (K) :</label>
            <input type="number" id="T" name="T" step="0.01" min="0.01" required>
            <br>
            <button type="submit">Calculer</button>
        </form>
        {% if result %}
            {{ result|safe }}
        {% endif %}
        <p><a href="{{ url_for('home') }}">Retour à l'accueil</a></p>
    </body>
    </html>
    """, result=result)

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
