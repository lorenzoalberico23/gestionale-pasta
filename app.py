from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "superpassword123"

DB_NAME = "pasta.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Creazione tabella prodotti
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prodotti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            prezzo REAL
        )
    """)

    # Inserimento prodotti base
    cur.execute("SELECT COUNT(*) FROM prodotti")
    if cur.fetchone()[0] == 0:
        prodotti_base = [
            ("Raffiche", 8.40),
            ("Ravioli Ricotta e Spinaci", 15.00),
            ("Ravioli Carne", 15.00),
            ("Tortellini Grandi", 15.00),
            ("Chitarra", 8.00),
            ("Chitarrina", 8.00),
            ("Mezza Chitarra", 8.00),
            ("Tagliatelle", 8.00),
            ("Pappardelle", 8.00),
            ("Fettuccine", 8.00),
            ("Tacconcini all'Uovo", 8.00),
            ("Tortellini Piccoli", 16.60),
            ("Chitarra senz'Uovo", 7.00),
            ("Chitarrina senz'Uovo", 7.00),
            ("Mezza Chitarra senz'Uovo", 7.00),
            ("Tagliatelle senz'Uovo", 7.00),
            ("Pappardelle senz'Uovo", 7.00),
            ("Fettuccine senz'Uovo", 7.00),
            ("Tacconcini", 7.00),
            ("Sagnette", 7.00),
            ("Maltagliati", 7.00),
            ("Rentrocilo", 7.00),
            ("Gnocchi", 8.00),
            ("Raviolini", 16.00),
            ("Pallottine", 28.00),
            ("Sfoglia lessa", 12.00),
            ("Cannelloni Ricotta e Spinaci", 14.50),
            ("Cannelloni Carne", 14.50),
            ("Rollè", 14.50),
            ("Crepes", 14.50),
            ("Pizza Rustica", 20.00),
            ("Grocchetti", 8.40),
            ("Chitarra Verde", 8.40),
            ("Chitarrina Verde", 8.40),
            ("Mezza Chitarra Verde", 8.40),
            ("Tagliatelle Verdi", 8.40),
            ("Pappardelle Verdi", 8.40),
            ("Fettuccine Verdi", 8.40),
            ("Sfoglia Cruda", 8.50),
            ("Quadrucci per Brodo", 8.50),
            ("Lasagne Pronte", 14.50)
        ]
        cur.executemany("INSERT INTO prodotti (nome, prezzo) VALUES (?, ?)", prodotti_base)

    # Tabella clienti
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clienti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefono TEXT
        )
    """)

    # Tabella prenotazioni
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prenotazioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            data_ritiro TEXT NOT NULL,
            fascia TEXT,
            note TEXT,
            FOREIGN KEY(cliente_id) REFERENCES clienti(id)
        )
    """)

    # Tabella dettagli
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dettagli (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prenotazione_id INTEGER NOT NULL,
            prodotto_id INTEGER NOT NULL,
            quantità REAL NOT NULL,
            FOREIGN KEY(prenotazione_id) REFERENCES prenotazioni(id),
            FOREIGN KEY(prodotto_id) REFERENCES prodotti(id)
        )
    """)

    conn.commit()
    conn.close()

def db():
    return sqlite3.connect(DB_NAME)

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

@app.route("/cerca")
def cerca():
    data = request.args.get("data")
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            p.id,
            c.nome,
            p.data_ritiro,
            p.fascia,
            p.note,
            IFNULL((
                SELECT SUM(d.quantità * pr.prezzo)
                FROM dettagli d
                JOIN prodotti pr ON pr.id = d.prodotto_id
                WHERE d.prenotazione_id = p.id
            ), 0) AS totale
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        WHERE p.data_ritiro = ?
        ORDER BY c.nome
    """, (data,))
    prenotazioni = cur.fetchall()

    lista_completa = []

    for p in prenotazioni:
        cur.execute("""
            SELECT pr.nome, d.quantità
            FROM dettagli d
            JOIN prodotti pr ON pr.id = d.prodotto_id
            WHERE d.prenotazione_id = ?
        """, (p[0],))
        prodotti = cur.fetchall()

        lista_completa.append({
            "id": p[0],
            "nome": p[1],
            "data": p[2],
            "fascia": p[3],
            "note": p[4],
            "totale": p[5],     # ⭐ AGGIUNTO
            "prodotti": prodotti
        })

    conn.close()
    return render_template("index.html", prenotazioni=lista_completa, ricerca=True)

@app.route("/cerca_nome")
def cerca_nome():
    nome = request.args.get("nome")
    conn = db()
    cur = conn.cursor()

    # Cerca prenotazioni per nome cliente
    cur.execute("""
        SELECT 
            p.id,
            c.nome,
            p.data_ritiro,
            p.fascia,
            p.note,
            IFNULL((
                SELECT SUM(d.quantità * pr.prezzo)
                FROM dettagli d
                JOIN prodotti pr ON pr.id = d.prodotto_id
                WHERE d.prenotazione_id = p.id
            ), 0) AS totale
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        WHERE c.nome LIKE ?
        ORDER BY p.data_ritiro DESC
    """, (nome + "%",))
    prenotazioni = cur.fetchall()

    lista_finale = []

    for p in prenotazioni:
        cur.execute("""
            SELECT pr.nome, d.quantità
            FROM dettagli d
            JOIN prodotti pr ON pr.id = d.prodotto_id
            WHERE d.prenotazione_id = ?
        """, (p[0],))
        prodotti = cur.fetchall()

        lista_finale.append({
            "id": p[0],
            "nome": p[1],
            "data": p[2],
            "fascia": p[3],
            "note": p[4],
            "totale": p[5],
            "prodotti": prodotti
        })

    conn.close()
    return render_template("index.html", prenotazioni=lista_finale, ricerca=True)

@app.route("/")
def index():
    conn = db()
    cur = conn.cursor()

    # Prenotazioni + totale
    cur.execute("""
        SELECT 
            p.id,
            c.nome,
            p.data_ritiro,
            p.fascia,
            p.note,
            IFNULL((
                SELECT SUM(d.quantità * pr.prezzo)
                FROM dettagli d
                JOIN prodotti pr ON pr.id = d.prodotto_id
                WHERE d.prenotazione_id = p.id
            ), 0) AS totale
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        ORDER BY p.data_ritiro DESC
    """)
    prenotazioni = cur.fetchall()

    # Aggiungo i prodotti a ogni prenotazione
    lista_finale = []
    for p in prenotazioni:
        cur.execute("""
            SELECT pr.nome, d.quantità
            FROM dettagli d
            JOIN prodotti pr ON pr.id = d.prodotto_id
            WHERE d.prenotazione_id = ?
        """, (p[0],))
        prodotti = cur.fetchall()

        lista_finale.append({
            "id": p[0],
            "nome": p[1],
            "data": p[2],
            "fascia": p[3],
            "note": p[4],
            "totale": p[5],
            "prodotti": prodotti
        })

    conn.close()
    return render_template("index.html", prenotazioni=lista_finale, ricerca=False)

@app.route("/autocomplete")
def autocomplete():
    term = request.args.get("term")
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT nome FROM clienti WHERE nome LIKE ? LIMIT 10", (term + "%",))
    risultati = [r[0] for r in cur.fetchall()]
    conn.close()
    return risultati

@app.route("/stampa_giorno/<data>")
def stampa_giorno(data):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id, c.nome, p.fascia, p.note
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        WHERE p.data_ritiro = ?
        ORDER BY p.fascia, c.nome COLLATE NOCASE
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

@app.route("/nuova", methods=["GET", "POST"])
def nuova():
    conn = db()
    cur = conn.cursor()

    # Recupera anche il prezzo
    cur.execute("SELECT id, nome, prezzo FROM prodotti")
    prodotti = cur.fetchall()

    if request.method == "POST":
        nome = request.form["nome"]
        telefono = request.form["telefono"]
        data = request.form["data"]
        note = request.form["note"]
        fascia = request.form["fascia"]

        # LISTE DI PRODOTTI E QUANTITÀ
        prodotti_ids = request.form.getlist("prodotto")
        quantita_list = request.form.getlist("quantità")

        # Cerca cliente esistente
        cur.execute("SELECT id FROM clienti WHERE nome = ?", (nome,))
        cliente = cur.fetchone()

        if cliente:
            cliente_id = cliente[0]
        else:
            cur.execute("INSERT INTO clienti (nome, telefono) VALUES (?, ?)", (nome, telefono))
            cliente_id = cur.lastrowid

        # Inserisci prenotazione
        cur.execute("""
            INSERT INTO prenotazioni (cliente_id, data_ritiro, fascia, note)
            VALUES (?,?,?,?)
        """, (cliente_id, data, fascia, note))
        prenotazione_id = cur.lastrowid

        # Inserisci TUTTI i prodotti
        for prodotto_id, quantità in zip(prodotti_ids, quantita_list):
            if quantità.strip() != "":
                cur.execute("""
                    INSERT INTO dettagli (prenotazione_id, prodotto_id, quantità)
                    VALUES (?,?,?)
                """, (prenotazione_id, prodotto_id, quantità))

        conn.commit()
        conn.close()
        return redirect("/")

    conn.close()
    return render_template("nuova.html", prodotti=prodotti)

@app.route("/cancella/<int:id>")
def cancella(id):
    conn = db()
    cur = conn.cursor()

    # Cancella dettagli
    cur.execute("DELETE FROM dettagli WHERE prenotazione_id = ?", (id,))

    # Cancella prenotazione
    cur.execute("DELETE FROM prenotazioni WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/stampa_mattina/<data>")
def stampa_mattina(data):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id, c.nome, p.note, p.fascia
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        WHERE p.data_ritiro = ? AND p.fascia = 'Mattina'
        ORDER BY c.nome COLLATE NOCASE
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
            "note": p[2],      # ⭐ ORA LE NOTE CI SONO
            "fascia": p[3],
            "prodotti": prodotti
        })

    conn.close()
    return render_template("stampa_fascia.html", lista=lista, data=data, titolo="Mattina")

@app.route("/stampa_pomeriggio/<data>")
def stampa_pomeriggio(data):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id, c.nome, p.note, p.fascia
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        WHERE p.data_ritiro = ? AND p.fascia = 'Pomeriggio'
        ORDER BY c.nome COLLATE NOCASE
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
            "note": p[2],      # ⭐ ORA LE NOTE CI SONO
            "fascia": p[3],
            "prodotti": prodotti
        })

    conn.close()
    return render_template("stampa_fascia.html", lista=lista, data=data, titolo="Pomeriggio")

@app.route("/stampa_totale/<data>")
def stampa_totale(data):
    conn = db()
    cur = conn.cursor()

    # Controllo se esistono fasce
    cur.execute("""
        SELECT COUNT(*)
        FROM prenotazioni
        WHERE data_ritiro = ?
        AND (fascia = 'Mattina' OR fascia = 'Pomeriggio')
    """, (data,))
    fasce_presenti = cur.fetchone()[0] > 0

    # Totali Mattina + prenotazioni senza fascia
    cur.execute("""
        SELECT pr.nome, SUM(d.quantità)
        FROM dettagli d
        JOIN prenotazioni p ON p.id = d.prenotazione_id
        JOIN prodotti pr ON pr.id = d.prodotto_id
        WHERE p.data_ritiro = ?
        AND (p.fascia = 'Mattina' OR p.fascia IS NULL OR p.fascia = '' OR p.fascia = ' ')
        GROUP BY pr.nome
        ORDER BY pr.nome
    """, (data,))
    totali_mattina = cur.fetchall()

    # Totali Pomeriggio
    cur.execute("""
        SELECT pr.nome, SUM(d.quantità)
        FROM dettagli d
        JOIN prenotazioni p ON p.id = d.prenotazione_id
        JOIN prodotti pr ON pr.id = d.prodotto_id
        WHERE p.data_ritiro = ?
        AND p.fascia = 'Pomeriggio'
        GROUP BY pr.nome
        ORDER BY pr.nome
    """, (data,))
    totali_pomeriggio = cur.fetchall()

    # Se NON ci sono fasce → totale unico
    totali_unici = None
    if not fasce_presenti:
        cur.execute("""
            SELECT pr.nome, SUM(d.quantità)
            FROM dettagli d
            JOIN prenotazioni p ON p.id = d.prenotazione_id
            JOIN prodotti pr ON pr.id = d.prodotto_id
            WHERE p.data_ritiro = ?
            GROUP BY pr.nome
            ORDER BY pr.nome
        """, (data,))
        totali_unici = cur.fetchall()

    conn.close()

    return render_template(
        "stampa_totale.html",
        totali_mattina=totali_mattina,
        totali_pomeriggio=totali_pomeriggio,
        totali_unici=totali_unici,
        fasce_presenti=fasce_presenti,
        data=data
    )


@app.route("/modifica/<int:id>", methods=["GET", "POST"])
def modifica(id):
    conn = db()
    cur = conn.cursor()

    # Lista prodotti (con prezzo!)
    cur.execute("SELECT id, nome, prezzo FROM prodotti")
    prodotti = cur.fetchall()

    # Dati prenotazione + cliente + fascia
    cur.execute("""
        SELECT p.id, c.nome, c.telefono, p.data_ritiro, p.fascia, p.note
        FROM prenotazioni p
        JOIN clienti c ON p.cliente_id = c.id
        WHERE p.id = ?
    """, (id,))
    prenotazione = cur.fetchone()

    # Prodotti già inseriti (prodotto_id + quantità)
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

        # Aggiorna cliente
        cur.execute("""
            UPDATE clienti 
            SET nome=?, telefono=? 
            WHERE id=(SELECT cliente_id FROM prenotazioni WHERE id=?)
        """, (nome, telefono, id))

        # Aggiorna prenotazione
        cur.execute("""
            UPDATE prenotazioni 
            SET data_ritiro=?, fascia=?, note=? 
            WHERE id=?
        """, (data, fascia, note, id))

        # Cancella vecchi prodotti
        cur.execute("DELETE FROM dettagli WHERE prenotazione_id=?", (id,))

        # Inserisci nuovi prodotti
        prodotti_ids = request.form.getlist("prodotto")
        quantita_list = request.form.getlist("quantità")

        for prodotto_id, quantità in zip(prodotti_ids, quantita_list):
            if quantità.strip() != "":
                cur.execute("""
                    INSERT INTO dettagli (prenotazione_id, prodotto_id, quantità)
                    VALUES (?,?,?)
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


# Avvio DB all'avvio del server
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)