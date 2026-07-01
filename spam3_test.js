import http from 'k6/http';
import { check } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

export const options = {
  vus: 100,         
  iterations: 5000,  
};


const conturi = [
  '11111111-1111-1111-1111-111111111111', // Domnu Mamuleanu
  '22222222-2222-2222-2222-222222222222', // Doamna Popescu
  '33333333-3333-3333-3333-333333333333', // Florin
  '44444444-4444-4444-4444-444444444444', // Badea Cornel
  '55555555-5555-5555-5555-555555555555'  // Domnu Popescu
];

export default function () {
  const url = 'http://127.0.0.1:8000/transfer';
  
  // 50% din tranzactii vor folosi aceeasi cheie (SPAM), 50% vor fi tranzactii reale (UNICE)
  const esteSpam = Math.random() < 0.5; 
  const cheie = esteSpam ? 'CHEIE-SPAM-SUPREMA' : uuidv4();

  // Alegem un expeditor la intamplare
  const indexExpeditor = Math.floor(Math.random() * conturi.length);
  const fromAcc = conturi[indexExpeditor];
  
  // Alegem un destinatar la intamplare (ne asiguram ca nu e aceeasi persoana)
  let indexDestinatar;
  do {
    indexDestinatar = Math.floor(Math.random() * conturi.length);
  } while (indexDestinatar === indexExpeditor);
  const toAcc = conturi[indexDestinatar];

  
  const suma = Math.floor(Math.random() * 50) + 1;

  const payload = JSON.stringify({
    from_account: fromAcc, 
    to_account: toAcc,   
    amount: suma
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': cheie, 
    },
  };
  
  const res = http.post(url, payload, params);
  
  check(res, {
    'statusul este 200': (r) => r.status === 200,
  });
}