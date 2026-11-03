from flask import Flask, render_template, request, redirect
import psycopg2
from urllib.parse import urlparse
import os

app = Flask(__name__)

# ---------------------------------------------------------
# CONNESSIONE AL DATABASE (PostgreSQL su Render)
# ---------------------------------------------------------
def get_conn():
    if "RENDER" in os.environ:
        url = urlparse(os.environ["DATABASE_URL"])
        return psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
    else:
        # SQLite locale (solo per sviluppo)
        import sqlite3
        return sqlite3.connect("pasta.db")


# ---------------------------------------------------------
# CREAZIONE TABELLE (COMPATIBILE CON POSTGRESQL)
# ---------------------------------------------------------
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # CLIENTI
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clienti (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL
        );
    """)

    # PRODOTTI
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prodotti (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            prezzo REAL NOT NULL
        );
    """)

    # PRENOTAZIONI
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prenotazioni (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER REFERENCES clienti(id),
            data_ritiro DATE NOT NULL,
            fascia TEXT NOT NULL,
            note TEXT
        );
    """)

    # DETTAGLI
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dettagli (
            id SERIAL PRIMARY KEY,
            prenotazione_id INTEGER REFERENCES prenotazioni(id),
            prodotto_id INTEGER REFERENCES prodotti(id),
            quantità INTEGER NOT NULL
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


# ---------------------------------------------------------
# INIZIALIZZA IL DATABASE SU RENDER
# ---------------------------------------------------------
init_db()


# ---------------------------------------------------------
# ROTTA HOME
# ---------------------------------------------------------
@app.route("/")
def index():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM prenotazioni ORDER BY id DESC;")
    prenotazioni = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", prenotazioni=prenotazioni)


# ---------------------------------------------------------
# AGGIUNGI CLIENTE
# ---------------------------------------------------------
@app.route("/add_cliente", methods=["POST"])
def add_cliente():
    nome = request.form["nome"]
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO clienti (nome) VALUES (%s);", (nome,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")


# ---------------------------------------------------------
# AGGIUNGI PRODOTTO
# ---------------------------------------------------------
@app.route("/add_prodotto", methods=["POST"])
def add_prodotto():
    nome = request.form["nome"]
    prezzo = request.form["prezzo"]
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO prodotti (nome, prezzo) VALUES (%s, %s);", (nome, prezzo))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")


# ---------------------------------------------------------
# AGGIUNGI PRENOTAZIONE
# ---------------------------------------------------------
@app.route("/add_prenotazione", methods=["POST"])
def add_prenotazione():
    cliente_id = request.form["cliente_id"]
    data_ritiro = request.form["data_ritiro"]
    fascia = request.form["fascia"]
    note = request.form["note"]

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO prenotazioni (cliente_id, data_ritiro, fascia, note)
        VALUES (%s, %s, %s, %s);
    """, (cliente_id, data_ritiro, fascia, note))

    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")


# ---------------------------------------------------------
# AVVIO LOCALE
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
