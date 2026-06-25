from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
import asyncpg
import redis.asyncio as redis
import uuid
import json

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
    
    # Conectarea la baza de date PostgreSQL
    db_pool = await asyncpg.create_pool(
        user="ledger_user",
        password="secretpassword",
        database="ledger_db",
        host="127.0.0.1",
        port=5432
    )
    
    # Crearea tabelelor si inserarea conturilor de test
    async with db_pool.acquire() as connection:
        await connection.execute("""
            -- Ștergem vechiturile
            DROP TABLE IF EXISTS transactions;
            DROP TABLE IF EXISTS accounts;

            -- Creăm noile tabele cu coloana owner_name
            CREATE TABLE accounts (
                id UUID PRIMARY KEY,
                owner_name VARCHAR(100) NOT NULL,
                balance BIGINT NOT NULL DEFAULT 0
            );

            CREATE TABLE transactions (
                id UUID PRIMARY KEY,
                from_account UUID REFERENCES accounts(id),
                to_account UUID REFERENCES accounts(id),
                amount BIGINT NOT NULL,
                idempotency_key VARCHAR(255) UNIQUE NOT NULL,
                status VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Inserăm 300.000 de cenți in total (3000 RON)
            INSERT INTO accounts (id, owner_name, balance) VALUES 
                ('11111111-1111-1111-1111-111111111111', 'Domnu Mamuleanu', 100000),
                ('22222222-2222-2222-2222-222222222222', 'Doamna Popescu', 50000),
                ('33333333-3333-3333-3333-333333333333', 'Florin', 50000),
                ('44444444-4444-4444-4444-444444444444', 'Badea Cornel', 50000),
                ('55555555-5555-5555-5555-555555555555', 'Domnu Popescu', 50000)
            ON CONFLICT (id) DO NOTHING;
        """)

    # Conctarea la Redis pentru gestionarea cheilor de idempotenta
    redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)
    print(" Sistemul a pornit: tabelele au fost create și conexiunile sunt active!")

@app.on_event("shutdown")
async def shutdown_event():
    await db_pool.close()
    await redis_client.close()

@app.post("/transfer")
async def transfer_money(
    request: TransactionRequest, 
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    global db_pool, redis_client
    
    # 1. VERIFICARE ANTI-SPAM (Redis)
    cached_response = await redis_client.get(idempotency_key)
    if cached_response:
        return json.loads(cached_response)
        
    if request.from_account == request.to_account:
        raise HTTPException(status_code=400, detail="Nu poti trimite bani catre acelasi cont!")

    async with db_pool.acquire() as conn:
        async with conn.transaction(): # Tranzacție sigură (ACID)
            
            # Ordonăm ID-urile pentru a preveni Deadlock-ul
            account_ids = sorted([request.from_account, request.to_account])
            
            # 2. PESSIMISTIC LOCKING: Blocăm rândurile
            accounts = await conn.fetch("""
                SELECT id, balance FROM accounts 
                WHERE id = ANY($1::uuid[]) 
                FOR UPDATE
            """, account_ids)
            
            if len(accounts) != 2:
                raise HTTPException(status_code=404, detail="Conturi invalide!")
                
            accounts_dict = {str(acc['id']): acc['balance'] for acc in accounts}
            sender_balance = accounts_dict[request.from_account]
            
            # 3. Verificăm fondurile expeditorului
            if sender_balance < request.amount:
                raise HTTPException(status_code=400, detail="Fonduri insuficiente!")
                
            # 4. Mutăm banii propriu-zis
            await conn.execute("UPDATE accounts SET balance = balance - $1 WHERE id = $2", request.amount, request.from_account)
            await conn.execute("UPDATE accounts SET balance = balance + $1 WHERE id = $2", request.amount, request.to_account)
            
            # 5. Notăm în jurnalul contabil
            tx_id = str(uuid.uuid4())
            try:
                await conn.execute("""
                    INSERT INTO transactions (id, from_account, to_account, amount, idempotency_key, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, tx_id, request.from_account, request.to_account, request.amount, idempotency_key, "SUCCESS")
            except asyncpg.exceptions.UniqueViolationError:
                raise HTTPException(status_code=409, detail="Tranzactie deja procesata.")
                
    # 6. Salvăm dovada succesului în memoria cache (Redis) timp de 24 ore
    response_data = {
        "status": "success", 
        "mesaj": "Transfer efectuat cu succes!",
        "transaction_id": tx_id
    }
    await redis_client.set(idempotency_key, json.dumps(response_data), ex=86400)
    
    return response_data

@app.get("/audit")
async def audit_balances():
    global db_pool
    async with db_pool.acquire() as conn:
        total_balance = await conn.fetchval("SELECT SUM(balance) FROM accounts")
        total_tx = await conn.fetchval("SELECT COUNT(*) FROM transactions")
        
        accounts_info = await conn.fetch("SELECT owner_name, balance FROM accounts ORDER BY owner_name")
        balances = {acc['owner_name']: acc['balance'] for acc in accounts_info}

        return {
            "total_bani_in_sistem": total_balance,
            "tranzactii_procesate": total_tx,
            "status": "Perfect echilibrat! Credit + Debit = 0" if total_balance == 300000 else "Aducem bani de acasa...",
            "solduri_persoane": balances
        }