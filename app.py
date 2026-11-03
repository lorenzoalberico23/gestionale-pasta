from flask import Flask, render_template, request, redirect, session
import os
import sqlite3
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)
init_db()
app.secret_key = "superpassword123"


def get_conn():
    # Locale → SQLite
    if os.getenv("RENDER") is None:
        return sqlite3.connect("pasta.db")

    # Render → PostgreSQL
    url = urlparse(os.getenv("DATABASE_URL"))
    return psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Prodotti
    cur.execute("""
    CREATE TABLE IF NOT EXISTS prodotti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        prezzo REAL NOT NULL
    );
    """)

    # Clienti
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clienti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefono TEXT
    );
    """)

    # Prenotazioni
    cur.execute("""
    CREATE TABLE IF NOT EXISTS prenotazioni (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        data_ritiro TEXT NOT NULL,
        fascia TEXT,
        note TEXT,
        FOREIGN KEY(cliente_id) REFERENCES clienti(id)
    );
    """)

    # Dettagli prenotazioni
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dettagli (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prenotazione_id INTEGER NOT NULL,
        prodotto_id INTEGER NOT NULL,
        quantità REAL NOT NULL,
        FOREIGN KEY(prenotazione_id) REFERENCES prenotazioni(id),
        FOREIGN KEY(prodotto_id) REFERENCES prodotti(id)
    );
    """)

    conn.commit()
    conn.close()


# LOGIN
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


# CERCA PER DATA
@app.route("/cerca")
def cerca():
    data = request.args.get("data")
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
        WHERE p.data_ritiro = ?
        ORDER BY c.nome
    """, (data,))
    prenotazioni = cur.fetchall()

    lista = []
    for p in prenotazioni:
        cur.execute("""
            SELECT pr.nome, d.quantità
            FROM dettagli d
            JOIN prodotti pr ON pr.id = d.prodotto_id
            WHERE d.prenotazione_id = ?
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


# CERCA PER NOME
@app.route("/cerca_nome")
def cerca_nome():
    nome = request.args.get("nome")
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
        WHERE c.nome ILIKE ?
        ORDER BY p.data_ritiro DESC
    """, (nome + "%",))
    prenotazioni = cur.fetchall()

    lista = []
    for p in prenotazioni:
        cur.execute("""
            SELECT pr.nome, d.quantità
            FROM dettagli d
            JOIN prodotti pr ON pr.id = d.prodotto_id
            WHERE d.prenotazione_id = ?
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


# HOME
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
        cur.execute("""
            SELECT pr.nome, d.quantità
            FROM dettagli d
            JOIN prodotti pr ON pr.id = d.prodotto_id
            WHERE d.prenotazione_id = ?
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


# AUTOCOMPLETE
@app.route("/autocomplete")
def autocomplete():
    term = request.args.get("term")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT nome FROM clienti WHERE nome ILIKE ? LIMIT 10", (term + "%",))
    risultati = [r[0] for r in cur.fetchall()]
    conn.close()
    return risultati


# STAMPA GIORNO
@app.route("/stampa_giorno/<data>")
def stampa_giorno(data):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id, c.nome, p.fascia, p.note
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        WHERE p.data_ritiro = ?
        ORDER BY p.fascia, c.nome
    """, (data,))
    prenotazioni = cur.fetchall()

    lista = []
    for p in prenotazioni:
        cur.execute("""
            SELECT pr.nome, d.quantità
            FROM dettagli d
            JOIN prodotti pr ON pr.id = d.prodotto_id
            WHERE d.prenotazione_id = ?
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


# NUOVA PRENOTAZIONE
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

        cur.execute("SELECT id FROM clienti WHERE nome = ?", (nome,))
        cliente = cur.fetchone()

        if cliente:
            cliente_id = cliente[0]
        else:
            cur.execute("INSERT INTO clienti (nome, telefono) VALUES (?, ?)", (nome, telefono))
            conn.commit()
            cur.execute("SELECT id FROM clienti WHERE nome = ?", (nome,))
            cliente_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO prenotazioni (cliente_id, data_ritiro, fascia, note)
            VALUES (?, ?, ?, ?)
            RETURNING id
        """, (cliente_id, data, fascia, note))
        prenotazione_id = cur.fetchone()[0]

        for prodotto_id, quantità in zip(prodotti_ids, quantita_list):
            if quantità.strip() != "":
                cur.execute("""
                    INSERT INTO dettagli (prenotazione_id, prodotto_id, quantità)
                    VALUES (?, ?, ?)
                """, (prenotazione_id, prodotto_id, quantità))

        conn.commit()
        conn.close()
        return redirect("/")

    conn.close()
    return render_template("nuova.html", prodotti=prodotti)


# CANCELLA
@app.route("/cancella/<int:id>")
def cancella(id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM dettagli WHERE prenotazione_id = ?", (id,))
    cur.execute("DELETE FROM prenotazioni WHERE id = ?", (id,))

    conn.commit()
    conn.close()
    return redirect("/")


# MODIFICA
@app.route("/modifica/<int:id>", methods=["GET", "POST"])
def modifica(id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, nome, prezzo FROM prodotti")
    prodotti = cur.fetchall()

    cur.execute("""
        SELECT p.id, c.nome, c.telefono, p.data_ritiro, p.fascia, p.note
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        WHERE p.id = ?
    """, (id,))
    prenotazione = cur.fetchone()

    cur.execute("""
        SELECT d.prodotto_id, d.quantità
        FROM dettagli d
        WHERE d.prenotazione_id = ?
    """, (id,))
    dettagli = cur.fetchall()

    if request.method == "POST":
        nome = request.form["nome"]
        telefono = request.form["telefono"]
        data = request.form["data"]
        fascia = request.form["fascia"]
        note = request.form["note"]

        cur.execute("""
            UPDATE clienti 
            SET nome=?, telefono=? 
            WHERE id=(SELECT cliente_id FROM prenotazioni WHERE id=?)
        """, (nome, telefono, id))

        cur.execute("""
            UPDATE prenotazioni 
            SET data_ritiro=?, fascia=?, note=? 
            WHERE id=?
        """, (data, fascia, note, id))

        cur.execute("DELETE FROM dettagli WHERE prenotazione_id=?", (id,))

        prodotti_ids = request.form.getlist("prodotto")
        quantita_list = request.form.getlist("quantità")

        for prodotto_id, quantità in zip(prodotti_ids, quantita_list):
            if quantità.strip() != "":
                cur.execute("""
                    INSERT INTO dettagli (prenotazione_id, prodotto_id, quantità)
                    VALUES (?, ?, ?)
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


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
