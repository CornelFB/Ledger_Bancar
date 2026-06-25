import http from 'k6/http';
import { check } from 'k6';


export const options = {
  vus: 200,          
  iterations: 100000,   
};

export default function () {
  const url = 'http://127.0.0.1:8000/transfer';
  
  // Datele transferului (mutăm 10 cenți)
  const payload = JSON.stringify({
    from_account: '11111111-1111-1111-1111-111111111111',
    to_account: '22222222-2222-2222-2222-222222222222',
    amount: 10
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      // ATENȚIE: Toți cei 50 de utilizatori trimit EXACT aceeași cheie!
      'Idempotency-Key': 'simulare1', 
    },
  };

  
  const res = http.post(url, payload, params);
  
  // vedem daca totul este ok
  
  check(res, {
    'statusul este 200': (r) => r.status === 200,
  });
}