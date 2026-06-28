# Ledger_Bancar
🏦 Ledger Bancar Idempotent - Core Banking System
Proiectul reprezintă backend-ul unui sistem bancar care gestionează corect tranzacțiile financiare sub trafic ridicat. Aplicația asigură că datele rămân corecte chiar și când mii de utilizatori fac transferuri în același timp.
✨ Caracteristici Tehnice Principale

🔒 Tranzacții ACID & Pessimistic Locking – Previne race condition-urile prin blocarea rândurilor din baza de date la nivel de tranzacție (SELECT ... FOR UPDATE). Dacă 100 de cereri încearcă să modifice același cont simultan, ele sunt procesate pe rând, fără să corupă soldul.
🛡️ Idempotență via Redis – Protecție împotriva cererilor duplicate (ex: utilizatorul apasă de două ori butonul de plată). Fiecare tranzacție folosește un Idempotency-Key stocat în cache (Redis), prevenind dubla taxare.
🚀 Arhitectură Decuplată – Backend asincron (FastAPI) separat de interfața grafică (HTML/JS). Comunicarea se face prin REST API, cu permisiunile gestionate prin middleware CORS.
📊 Testat cu K6 – Sistemul a fost supus unor teste de încărcare cu Grafana K6, procesând mii de iterații concurente fără să corupă datele.

🛠️ Tehnologii

Backend: Python 3, FastAPI, Uvicorn
Bază de date: PostgreSQL (driver asincron asyncpg)
Cache: Redis
Frontend: HTML5, Vanilla JavaScript, Bootstrap 5
Load Testing: Grafana K6

🚀 Cum rulezi proiectul
1. Pornirea serverului
-source venv/Scripts/activate
-uvicorn main:app --reload
Serverul pornește pe http://127.0.0.1:8000. La start, tabelele se creează automat și se populează cu date de test.
2. Interfața grafică
Deschide index.html  în orice browser. Datele se actualizează automat din server.
3. Teste de stres
-k6 run spam_test.js
-k6 run spam2_test.js