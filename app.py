import sqlite3
from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "your_secret_key"

# פונקציה שמתחברת למסד הנתונים
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# פונקציה ליצירת טבלאות אם הן לא קיימות
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # יצירת טבלת משתמשים
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    ''')

    # יצירת טבלת טרנזקציות
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')

    conn.commit()
    conn.close()

# פונקציה להוספת נתוני דוגמה
def insert_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # הכנסת נתוני דוגמה
    cursor.execute("DELETE FROM transactions;")
    cursor.execute("DELETE FROM users;")

    cursor.execute('''
        INSERT INTO users (name, email, password) VALUES
        ('John Doe', 'john@example.com', '1234'),
        ('Jane Smith', 'jane@example.com', '5678');
    ''')

    cursor.execute("SELECT id FROM users WHERE email = ?", ("john@example.com",))
    john_id = cursor.fetchone()[0]

    cursor.executemany('''
        INSERT INTO transactions (type, category, amount, user_id) VALUES
        (?, ?, ?, ?)
    ''', [
        ("income", "Scholarship", 1500, john_id),
        ("expense", "Rent", 800, john_id),
        ("income", "Part-time Job", 1200, john_id),
        ("expense", "Groceries", 300, john_id),
        ("expense", "Transportation", 100, john_id)
    ])

    conn.commit()
    conn.close()

# ניווט מותאם לפי משתמש
@app.context_processor
def inject_navigation():
    if "user_id" in session:
        nav_links = [
            {"url": "/", "label": "Home"},
            {"url": "/summary", "label": "Monthly Summary"},
            {"url": "/add_transaction", "label": "Add Transaction"},
            {"url": "/logout", "label": "Logout"}
        ]
    else:
        nav_links = [
            {"url": "/", "label": "Home"},
            {"url": "/login", "label": "Login"},
            {"url": "/signup", "label": "Sign Up"},
            {"url": "/contact", "label": "Contact Us"}
        ]
    return {"nav_links": nav_links}

# דף הבית
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

# דף Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))
        else:
            return "Invalid email or password. Please try again."

    return render_template("login.html")

# דף Dashboard עם 5 טרנזקציות אחרונות
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_name = session.get("user_name", "User")
    user_id = session.get("user_id")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, type, category, amount, date FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 5", (user_id,))
    transactions = cursor.fetchall()
    conn.close()

    return render_template("dashboard.html", user_name=user_name, transactions=transactions)

# דף הצגת כל הטרנזקציות
@app.route("/all_transactions")
def all_transactions():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, type, category, amount, date FROM transactions WHERE user_id = ? ORDER BY date DESC", (user_id,))
    all_transactions = cursor.fetchall()
    conn.close()

    return render_template("all_transactions.html", transactions=all_transactions)

# מחיקת טרנזקציה
@app.route("/delete_transaction/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, session["user_id"]))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))

# עריכת טרנזקציה
@app.route("/edit_transaction/<int:transaction_id>", methods=["GET", "POST"])
def edit_transaction(transaction_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, session["user_id"]))
    transaction = cursor.fetchone()

    if not transaction:
        conn.close()
        return "Transaction not found", 404

    if request.method == "POST":
        transaction_type = request.form["type"]
        category = request.form["category"]
        amount = request.form["amount"]

        cursor.execute("UPDATE transactions SET type = ?, category = ?, amount = ? WHERE id = ?",
                       (transaction_type, category, amount, transaction_id))
        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("edit_transaction.html", transaction=transaction)



# דף סיכום חודשי
@app.route("/summary")
def summary():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'income'", (user_id,))
    total_income = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'expense'", (user_id,))
    total_expenses = cursor.fetchone()[0] or 0

    balance = total_income - total_expenses

    conn.close()

    return render_template("summary.html", total_income=total_income, total_expenses=total_expenses, balance=balance)

# דף Contact Us
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]
        print(f"Message from {name} ({email}): {message}")
        return "Thank you for your message!"
    return render_template("contact.html")

# דף Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# דף Signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Email already exists. Please use a different email."
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")

# דף Add Transaction
@app.route("/add_transaction", methods=["GET", "POST"])
def add_transaction():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        transaction_type = request.form["type"]
        category = request.form["category"]
        amount = request.form["amount"]
        user_id = session["user_id"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO transactions (type, category, amount, user_id) VALUES (?, ?, ?, ?)",
                       (transaction_type, category, amount, user_id))
        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("add_transaction.html")

@app.route('/thank_you', methods=['POST'])
def thank_you():
    return render_template('thank_you.html')

# CSS ו-JS
@app.route('/MyCss/<path:filename>')
def serve_css(filename):
    return send_from_directory('MyCss', filename)





@app.route('/MYJS/<path:filename>')
def serve_js(filename):
    return send_from_directory('MYJS', filename)



if __name__ == "__main__":
    create_tables()
    insert_sample_data()
    app.run(debug=True)


    @app.route('/thank_you', methods=['POST'])
    def thank_you():
        return render_template('thank_you.html')
