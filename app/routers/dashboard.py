from fastapi import APIRouter

from ..database import connect

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary():
    with connect() as connection:
        totals = connection.execute(
            """
            SELECT (SELECT COUNT(*) FROM customers) customers,
                   (SELECT COUNT(*) FROM transactions WHERE transaction_date >= date('now', '-29 days')) transactions,
                   (SELECT COALESCE(SUM(balance), 0) FROM customers) balance,
                   (SELECT COUNT(*) FROM transactions WHERE suspicious = 1) suspicious
            """
        ).fetchone()
        daily = connection.execute(
            """SELECT transaction_date date, ROUND(SUM(amount), 2) amount
               FROM transactions WHERE transaction_date >= date('now', '-29 days')
               GROUP BY transaction_date ORDER BY transaction_date"""
        ).fetchall()
        suspicious = connection.execute(
            """SELECT t.id, c.name, t.amount, t.merchant, t.transaction_date date
               FROM transactions t JOIN customers c ON c.id = t.customer_id
               WHERE t.suspicious = 1 ORDER BY t.transaction_date DESC, t.amount DESC LIMIT 6"""
        ).fetchall()
    return {**dict(totals), "daily": [dict(row) for row in daily], "suspicious_list": [dict(row) for row in suspicious]}
