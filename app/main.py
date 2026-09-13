from contextlib import asynccontextmanager
from datetime import date, timedelta
import os
import random
import sqlite3
from pathlib import Path

from faker import Faker
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("FAKEBANK_DB_PATH", BASE_DIR / "fakebank.db"))
CUSTOMER_COUNT = 10_000
TRANSACTION_COUNT = 100_000


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def seed_database() -> None:
    if DB_PATH.exists():
        with connect() as connection:
            if connection.execute("SELECT 1 FROM customers LIMIT 1").fetchone():
                return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    fake = Faker("pl_PL")
    random.seed(20260913)
    today = date.today()

    with connect() as connection:
        connection.executescript(
            """
            DROP TABLE IF EXISTS transactions;
            DROP TABLE IF EXISTS customers;
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                city TEXT NOT NULL,
                country TEXT NOT NULL,
                account_number TEXT NOT NULL,
                balance REAL NOT NULL,
                status TEXT NOT NULL,
                joined_at TEXT NOT NULL
            );
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                merchant TEXT NOT NULL,
                city TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                suspicious INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            );
            CREATE INDEX idx_transactions_customer ON transactions(customer_id);
            CREATE INDEX idx_transactions_date ON transactions(transaction_date);
            CREATE INDEX idx_transactions_suspicious ON transactions(suspicious);
            """
        )
        customers = []
        for customer_id in range(1, CUSTOMER_COUNT + 1):
            customers.append(
                (
                    customer_id,
                    fake.name(),
                    fake.email(),
                    fake.city(),
                    "Polska",
                    f"PL{random.randint(10, 99)} {random.randint(1000, 9999)} "
                    f"{random.randint(1000, 9999)} {random.randint(1000, 9999)}",
                    round(random.uniform(120, 185_000), 2),
                    "Zablokowane" if random.random() < 0.055 else "Aktywne",
                    (today - timedelta(days=random.randint(20, 2500))).isoformat(),
                )
            )
        connection.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", customers
        )

        transactions = []
        merchants = ["PayPoint", "Market24", "TravelHub", "TechWorld", "Kawiarnia", "Przelew własny"]
        for transaction_id in range(1, TRANSACTION_COUNT + 1):
            amount = round(random.uniform(8, 4500), 2)
            suspicious = int(amount > 3500 or random.random() < 0.018)
            transactions.append(
                (
                    transaction_id,
                    random.randint(1, CUSTOMER_COUNT),
                    "Wpływ" if random.random() < 0.43 else "Wydatek",
                    amount,
                    random.choice(merchants),
                    fake.city(),
                    (today - timedelta(days=random.randint(0, 364))).isoformat(),
                    suspicious,
                )
            )
        connection.executemany(
            "INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)", transactions
        )
        connection.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_database()
    yield


app = FastAPI(title="FakeBank", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")


@app.get("/api/summary")
def summary():
    with connect() as connection:
        totals = connection.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM customers) customers,
              (SELECT COUNT(*) FROM transactions
               WHERE transaction_date >= date('now', '-29 days')) transactions,
              (SELECT COALESCE(SUM(balance), 0) FROM customers) balance,
              (SELECT COUNT(*) FROM transactions WHERE suspicious = 1) suspicious
            """
        ).fetchone()
        daily = connection.execute(
            """
            SELECT transaction_date date, ROUND(SUM(amount), 2) amount
            FROM transactions
            WHERE transaction_date >= date('now', '-29 days')
            GROUP BY transaction_date ORDER BY transaction_date
            """
        ).fetchall()
        countries = connection.execute(
            "SELECT country, COUNT(*) count FROM customers GROUP BY country ORDER BY count DESC"
        ).fetchall()
        suspicious = connection.execute(
            """
            SELECT t.id, c.name, t.amount, t.merchant, t.transaction_date date
            FROM transactions t JOIN customers c ON c.id = t.customer_id
            WHERE t.suspicious = 1 ORDER BY t.transaction_date DESC, t.amount DESC LIMIT 6
            """
        ).fetchall()
    return {
        **dict(totals),
        "daily": [dict(row) for row in daily],
        "countries": [dict(row) for row in countries],
        "suspicious_list": [dict(row) for row in suspicious],
    }


@app.get("/api/customers")
def customers(search: str = "", status: str = "", limit: int = Query(8, le=50)):
    pattern = f"%{search}%"
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id, name, email, city, balance, status
            FROM customers
            WHERE (name LIKE ? OR email LIKE ? OR account_number LIKE ?)
              AND (? = '' OR status = ?)
            ORDER BY balance DESC LIMIT ?
            """,
            (pattern, pattern, pattern, status, status, limit),
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/customers/{customer_id}")
def customer_details(customer_id: int):
    with connect() as connection:
        customer = connection.execute(
            "SELECT * FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
        transactions = connection.execute(
            """
            SELECT id, transaction_type, amount, merchant, city, transaction_date date, suspicious
            FROM transactions WHERE customer_id = ?
            ORDER BY transaction_date DESC, id DESC LIMIT 20
            """,
            (customer_id,),
        ).fetchall()
    if customer is None:
        raise HTTPException(status_code=404, detail="Nie znaleziono klienta")
    return {"customer": dict(customer), "transactions": [dict(row) for row in transactions]}


@app.get("/api/transactions")
def transactions(
    suspicious: bool = False,
    start: str = "",
    end: str = "",
    limit: int = Query(12, le=50),
):
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT t.id, c.name, t.transaction_type, t.amount, t.merchant,
                   t.transaction_date date, t.suspicious
            FROM transactions t JOIN customers c ON c.id = t.customer_id
            WHERE (? = 0 OR t.suspicious = 1)
              AND (? = '' OR t.transaction_date >= ?)
              AND (? = '' OR t.transaction_date <= ?)
            ORDER BY t.transaction_date DESC, t.id DESC LIMIT ?
            """,
            (int(suspicious), start, start, end, end, limit),
        ).fetchall()
    return [dict(row) for row in rows]
