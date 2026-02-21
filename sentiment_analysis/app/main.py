import os
from flask import Flask, request, render_template, session, redirect
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import base64
from io import BytesIO

from google.oauth2 import id_token
from google.auth.transport import requests as grequests

from sentiment import analizar_sentimiento
from text_utils import (
    normalizar_texto,
    es_solo_simbolos,
    es_texto_basura,
    tiene_palabras_validas,
    PALABRAS_GENERICAS
)

# ==============================
# CONFIGURACIÓN APP
# ==============================

app = Flask(__name__)
# Es vital que esta clave sea secreta y persistente en Cloud Run
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "una-clave-muy-secreta-123")

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")

# ==============================
# VALIDAR TOKEN GOOGLE
# ==============================

def verify_google_token(token):
    try:
        # Verificamos el token directamente con Google
        idinfo = id_token.verify_oauth2_token(
            token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )

        # Eliminamos la validación de dominio corporativo (hd) 
        # para que cualquier cuenta autorizada en la consola pueda entrar.
        return idinfo

    except Exception as e:
        print(f"Error validando token: {e}")
        return None


# ==============================
# LOGIN
# ==============================

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    token = data.get("credential")

    user_info = verify_google_token(token)

    if user_info:
        # Guardamos la sesión del usuario
        session["user"] = {
            "name": user_info.get("name"),
            "email": user_info.get("email"),
            "picture": user_info.get("picture")
        }
        return {"status": "success"}
    else:
        return {"status": "unauthorized"}, 401


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ==============================
# RUTA PRINCIPAL
# ==============================

@app.route("/", methods=["GET", "POST"])
def analizar_estados():

    # GET → Mostrar login o formulario
