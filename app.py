from flask import Flask, render_template, request, redirect, session
import os
import sqlite3
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = "superpassword123"


# ---------------------------------------------------------
# CONNESSIONE DATABASE
# ---------------------------------------------------------
def get_conn():
    if os.getenv("RENDER") is None:
        # Locale → SQLite
        conn = sqlite3.connect("pasta.db")
        conn.row_factory = sqlite3.Row
        return conn
    else:
        # Render → PostgreSQL
        url = urlparse(os.getenv("DATABASE_URL"))
        return psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )


# ---------------------------------------------------------
# CREAZIONE TABELLE (POSTGRESQL)
# ---------------------------------------------------------
def init_db():
    if os.getenv("RENDER") is None:
        return  # In locale NON tocco SQLite, le tabelle già esistono

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS clienti (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            telefono TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS prodotti (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            prezzo REAL NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS prenotazioni (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER NOT NULL REFERENCES clienti(id),
            data_ritiro TEXT NOT NULL,
            fascia TEXT,
            note TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS dettagli (
            id SERIAL PRIMARY KEY,
            prenotazione_id INTEGER NOT NULL REFERENCES prenotazioni(id),
            prodotto_id INTEGER NOT NULL REFERENCES prodotti(id),
            quantità REAL NOT NULL
        );
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# PLACEHOLDER AUTOMATICO
# ---------------------------------------------------------
def ph():
    return "?" if os.getenv("RENDER") is None else "%s"


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]

        if user == "Lupastaro1" and pwd == "Lupastaro1":
            session["logged"] = True
            return redirect("/")
        else:
            return render_template("login.html", errore=True)

    return render_template("login.html")


# ---------------------------------------------------------
# CERCA PER DATA
# ---------------------------------------------------------
@app.route("/cerca")
def cerca():
    data = request.args.get("data")
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT 
            p.id, c.nome, p.data_ritiro, p.fascia, p.note,
            COALESCE((
                SELECT SUM(d.quantità * pr.prezzo)
                FROM dettagli d
                JOIN prodotti pr ON pr.id = d.prodotto_id
                WHERE d.prenotazione_id = p.id
            ), 0)
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        WHERE p.data_ritiro = {ph()}
        ORDER BY c.nome
    """, (data,))
    prenotazioni = cur.fetchall()

    lista = []
    for p in prenotazioni:
        cur.execute(f"""
            SELECT pr.nome, d.quantità
            FROM dettagli d
            JOIN prodotti pr ON pr.id = d.prodotto_id
            WHERE d.prenotazione_id = {ph()}
        """, (p[0],))
        prodotti = cur.fetchall()

        lista.append({
            "id": p[0],
            "nome": p[1],
            "data": p[2],
            "fascia": p[3],
            "note": p[4],
            "totale": p[5],
            "prodotti": prodotti
        })

    conn.close()
    return render_template("index.html", prenotazioni=lista, ricerca=True)


# ---------------------------------------------------------
# CERCA PER NOME
# ---------------------------------------------------------
@app.route("/cerca_nome")
def cerca_nome():
    nome = request.args.get("nome")
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT 
            p.id, c.nome, p.data_ritiro, p.fascia, p.note,
            COALESCE((
                SELECT SUM(d.quantità * pr.prezzo)
                FROM dettagli d
                JOIN prodotti pr ON pr.id = d.prodotto_id
                WHERE d.prenotazione_id = p.id
            ), 0)
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        WHERE c.nome ILIKE {ph()}
        ORDER BY p.data_ritiro DESC
    """, (nome + "%",))
    prenotazioni = cur.fetchall()

    lista = []
    for p in prenotazioni:
        cur.execute(f"""
            SELECT pr.nome, d.quantità
            FROM dettagli d
            JOIN prodotti pr ON pr.id = d.prodotto_id
            WHERE d.prenotazione_id = {ph()}
        """, (p[0],))
        prodotti = cur.fetchall()

        lista.append({
            "id": p[0],
            "nome": p[1],
            "data": p[2],
            "fascia": p[3],
            "note": p[4],
            "totale": p[5],
            "prodotti": prodotti
        })

    conn.close()
    return render_template("index.html", prenotazioni=lista, ricerca=True)


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------
@app.route("/")
def index():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            p.id, c.nome, p.data_ritiro, p.fascia, p.note,
            COALESCE((
                SELECT SUM(d.quantità * pr.prezzo)
                FROM dettagli d
                JOIN prodotti pr ON pr.id = d.prodotto_id
                WHERE d.prenotazione_id = p.id
            ), 0)
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        ORDER BY p.data_ritiro DESC
    """)
    prenotazioni = cur.fetchall()

    lista = []
    for p in prenotazioni:
        cur.execute(f"""
            SELECT pr.nome, d.quantità
            FROM dettagli d
            JOIN prodotti pr ON pr.id = d.prodotto_id
            WHERE d.prenotazione_id = {ph()}
        """, (p[0],))
        prodotti = cur.fetchall()

        lista.append({
            "id": p[0],
            "nome": p[1],
            "data": p[2],
            "fascia": p[3],
            "note": p[4],
            "totale": p[5],
            "prodotti": prodotti
        })

    conn.close()
    return render_template("index.html", prenotazioni=lista, ricerca=False)


# ---------------------------------------------------------
# AUTOCOMPLETE
# ---------------------------------------------------------
@app.route("/autocomplete")
def autocomplete():
    term = request.args.get("term")
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(f"SELECT nome FROM clienti WHERE nome ILIKE {ph()} LIMIT 10", (term + "%",))
    risultati = [r[0] for r in cur.fetchall()]

    conn.close()
    return risultati


# ---------------------------------------------------------
# STAMPA GIORNO
# ---------------------------------------------------------
@app.route("/stampa_giorno/<data>")
def stampa_giorno(data):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT p.id, c.nome, p.fascia, p.note
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        WHERE p.data_ritiro = {ph()}
        ORDER BY p.fascia, c.nome
    """, (data,))
    prenotazioni = cur.fetchall()

    lista = []
    for p in prenotazioni:
        cur.execute(f"""
            SELECT pr.nome, d.quantità
            FROM dettagli d
            JOIN prodotti pr ON pr.id = d.prodotto_id
            WHERE d.prenotazione_id = {ph()}
        """, (p[0],))
        prodotti = cur.fetchall()

        lista.append({
            "nome": p[1],
            "fascia": p[2],
            "note": p[3],
            "prodotti": prodotti
        })

    conn.close()
    return render_template("stampa_giorno.html", lista=lista, data=data)


# ---------------------------------------------------------
# NUOVA PRENOTAZIONE
# ---------------------------------------------------------
@app.route("/nuova", methods=["GET", "POST"])
def nuova():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, nome, prezzo FROM prodotti")
    prodotti = cur.fetchall()

    if request.method == "POST":
        nome = request.form["nome"]
        telefono = request.form["telefono"]
        data = request.form["data"]
        note = request.form["note"]
        fascia = request.form["fascia"]

        prodotti_ids = request.form.getlist("prodotto")
        quantita_list = request.form.getlist("quantità")

        cur.execute(f"SELECT id FROM clienti WHERE nome = {ph()}", (nome,))
        cliente = cur.fetchone()

        if cliente:
            cliente_id = cliente[0]
        else:
            cur.execute(f"INSERT INTO clienti (nome, telefono) VALUES ({ph()}, {ph()})", (nome, telefono))
            conn.commit()
            cur.execute(f"SELECT id FROM clienti WHERE nome = {ph()}", (nome,))
            cliente_id = cur.fetchone()[0]

        cur.execute(f"""
            INSERT INTO prenotazioni (cliente_id, data_ritiro, fascia, note)
            VALUES ({ph()}, {ph()}, {ph()}, {ph()})
            RETURNING id
        """, (cliente_id, data, fascia, note))
        prenotazione_id = cur.fetchone()[0]

        for prodotto_id, quantità in zip(prodotti_ids, quantita_list):
            if quantità.strip() != "":
                cur.execute(f"""
                    INSERT INTO dettagli (prenotazione_id, prodotto_id, quantità)
                    VALUES ({ph()}, {ph()}, {ph()})
                """, (prenotazione_id, prodotto_id, quantità))

        conn.commit()
        conn.close()
        return redirect("/")

    conn.close()
    return render_template("nuova.html", prodotti=prodotti)


# ---------------------------------------------------------
# CANCELLA
# ---------------------------------------------------------
@app.route("/cancella/<int:id>")
def cancella(id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(f"DELETE FROM dettagli WHERE prenotazione_id = {ph()}", (id,))
    cur.execute(f"DELETE FROM prenotazioni WHERE id = {ph()}", (id,))

    conn.commit()
    conn.close()
    return redirect("/")


# ---------------------------------------------------------
# MODIFICA
# ---------------------------------------------------------
@app.route("/modifica/<int:id>", methods=["GET", "POST"])
def modifica(id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, nome, prezzo FROM prodotti")
    prodotti = cur.fetchall()

    cur.execute(f"""
        SELECT p.id, c.nome, c.telefono, p.data_ritiro, p.fascia, p.note
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        WHERE p.id = {ph()}
    """, (id,))
    prenotazione = cur.fetchone()

    cur.execute(f"""
        SELECT d.prodotto_id, d.quantità
        FROM dettagli d
        WHERE d.prenotazione_id = {ph()}
    """, (id,))
    dettagli = cur.fetchall()

    if request.method == "POST":
        nome = request.form["nome"]
        telefono = request.form["telefono"]
        data = request.form["data"]
        fascia = request.form["fascia"]
        note = request.form["note"]

        cur.execute(f"""
            UPDATE clienti 
            SET nome={ph()}, telefono={ph()} 
            WHERE id=(SELECT cliente_id FROM prenotazioni WHERE id={ph()})
        """, (nome, telefono, id))

        cur.execute(f"""
            UPDATE prenotazioni 
            SET data_ritiro={ph()}, fascia={ph()}, note={ph()} 
            WHERE id={ph()}
        """, (data, fascia, note, id))

        cur.execute(f"DELETE FROM dettagli WHERE prenotazione_id={ph()}", (id,))

        prodotti_ids = request.form.getlist("prodotto")
        quantita_list = request.form.getlist("quantità")

        for prodotto_id, quantità in zip(prodotti_ids, quantita_list):
            if quantità.strip() != "":
                cur.execute(f"""
                    INSERT INTO dettagli (prenotazione_id, prodotto_id, quantità)
                    VALUES ({ph()}, {ph()}, {ph()})
                """, (id, prodotto_id, quantità))

        conn.commit()
        conn.close()
        return redirect("/")

    conn.close()
    return render_template(
        "modifica.html",
        prenotazione=prenotazione,
        prodotti=prodotti,
        dettagli=dettagli
    )


# ---------------------------------------------------------
# AVVIO LOCALE
# ---------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
