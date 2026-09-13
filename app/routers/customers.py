from fastapi import APIRouter, HTTPException, Query

from ..database import connect

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("")
def customers(search: str = "", status: str = "", limit: int = Query(8, le=50)):
    pattern = f"%{search}%"
    with connect() as connection:
        rows = connection.execute(
            """SELECT id, name, email, city, balance, status FROM customers
               WHERE (name LIKE ? OR email LIKE ? OR account_number LIKE ?)
                 AND (? = '' OR status = ?) ORDER BY balance DESC LIMIT ?""",
            (pattern, pattern, pattern, status, status, limit),
        ).fetchall()
    return [dict(row) for row in rows]


@router.get("/{customer_id}")
def customer_details(customer_id: int):
    with connect() as connection:
        customer = connection.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        transactions = connection.execute(
            """SELECT id, transaction_type, amount, merchant, city, transaction_date date, suspicious
               FROM transactions WHERE customer_id = ? ORDER BY transaction_date DESC, id DESC LIMIT 20""",
            (customer_id,),
        ).fetchall()
    if customer is None:
        raise HTTPException(status_code=404, detail="Nie znaleziono klienta")
    return {"customer": dict(customer), "transactions": [dict(row) for row in transactions]}
