from datetime import date, timedelta
import os
import random
import sqlite3
from pathlib import Path

from faker import Faker

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
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL,
                city TEXT NOT NULL, country TEXT NOT NULL, account_number TEXT NOT NULL,
                balance REAL NOT NULL, status TEXT NOT NULL, joined_at TEXT NOT NULL
            );
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL, amount REAL NOT NULL, merchant TEXT NOT NULL,
                city TEXT NOT NULL, transaction_date TEXT NOT NULL,
                suspicious INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(customer_id) REFERENCES customers(id)
            );
            CREATE INDEX idx_transactions_customer ON transactions(customer_id);
            CREATE INDEX idx_transactions_date ON transactions(transaction_date);
            CREATE INDEX idx_transactions_suspicious ON transactions(suspicious);
            """
        )
        customers = [
            (
                customer_id, fake.name(), fake.email(), fake.city(), "Polska",
                f"PL{random.randint(10, 99)} {random.randint(1000, 9999)} "
                f"{random.randint(1000, 9999)} {random.randint(1000, 9999)}",
                round(random.uniform(120, 185_000), 2),
                "Zablokowane" if random.random() < 0.055 else "Aktywne",
                (today - timedelta(days=random.randint(20, 2500))).isoformat(),
            )
            for customer_id in range(1, CUSTOMER_COUNT + 1)
        ]
        connection.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", customers)

        merchants = ["PayPoint", "Market24", "TravelHub", "TechWorld", "Kawiarnia", "Przelew własny"]
        transactions = [
            (
                transaction_id, random.randint(1, CUSTOMER_COUNT),
                "Wpływ" if random.random() < 0.43 else "Wydatek",
                (amount := round(random.uniform(8, 4500), 2)), random.choice(merchants),
                fake.city(), (today - timedelta(days=random.randint(0, 364))).isoformat(),
                int(amount > 3500 or random.random() < 0.018),
            )
            for transaction_id in range(1, TRANSACTION_COUNT + 1)
        ]
        connection.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)", transactions)
        connection.commit()
