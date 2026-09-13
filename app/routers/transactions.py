from fastapi import APIRouter, Query

from ..database import connect

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("")
def transactions(
    suspicious: bool = False,
    start: str = "",
    end: str = "",
    limit: int = Query(12, le=50),
):
    with connect() as connection:
        rows = connection.execute(
            """SELECT t.id, c.name, t.transaction_type, t.amount, t.merchant,
                      t.transaction_date date, t.suspicious
               FROM transactions t JOIN customers c ON c.id = t.customer_id
               WHERE (? = 0 OR t.suspicious = 1)
                 AND (? = '' OR t.transaction_date >= ?)
                 AND (? = '' OR t.transaction_date <= ?)
               ORDER BY t.transaction_date DESC, t.id DESC LIMIT ?""",
            (int(suspicious), start, start, end, end, limit),
        ).fetchall()
    return [dict(row) for row in rows]
