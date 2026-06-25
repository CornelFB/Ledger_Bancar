from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
import asyncpg
import redis.asyncio as redis
#Aplicatia FastAPI care va rula serverul
app = FastAPI(title="Ledger Bancar Idempotent")


db_pool = None
redis_client = None


class TransactionRequest(BaseModel):
    from_account: str = Field(..., description="ID-ul contului din care pleacă banii")
    to_account: str = Field(..., description="ID-ul contului în care ajung banii")
    amount: int = Field(..., gt=0, description="Suma în cenți/bani (trebuie să fie strict pozitivă)")

#Pornim sistemul și creăm tabelele în baza de date, plus conturile de test
#Acest eveniment se va declansa automat la ponrirea aplicatiei
@app.on_event("startup")
async def startup_event():
    global db_pool, redis_client
    
   #Conectarea la baza de date PostgreSQL
    db_pool = await asyncpg.create_pool(
        user="ledger_user",
        password="secretpassword",
        database="ledger_db",
        host="127.0.0.1",
        port=5432
    )
    
   #Crearea tabelelor si crearea conturilor de test
    async with db_pool.acquire() as connection:
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id UUID PRIMARY KEY,
                balance BIGINT NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id UUID PRIMARY KEY,
                from_account UUID REFERENCES accounts(id),
                to_account UUID REFERENCES accounts(id),
                amount BIGINT NOT NULL,
                idempotency_key VARCHAR(255) UNIQUE NOT NULL,
                status VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Inserăm 1000 RON în contul 1 și 500 RON în contul 2 (valori în cenți)
            INSERT INTO accounts (id, balance) 
            VALUES 
                ('11111111-1111-1111-1111-111111111111', 100000),
                ('22222222-2222-2222-2222-222222222222', 50000)
            ON CONFLICT (id) DO NOTHING;
        """)

    #Conctarea la Redis pentru gestionarea cheilor de idempotenta
    redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)
    print(" Sistemul a pornit: tabelele au fost create și conexiunile sunt active!")

@app.on_event("shutdown")
async def shutdown_event():
    await db_pool.close()
    await redis_client.close()

#final api(se efectueaza transfere)
@app.post("/transfer")
async def transfer_money(
    request: TransactionRequest, 
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    #Verificarea existentei cheii de idempotenta in Redis
    return {"status": "ok", "mesaj": "Am primit datele!", "cheie_idempotenta": idempotency_key}