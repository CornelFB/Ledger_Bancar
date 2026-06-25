import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 200,          
  iterations: 1000,   
};

export default function () {
  const url = 'http://127.0.0.1:8000/transfer';
  
  // Domnu Mamuleanu îi trimite lui Badea Cornel 10 cenți
  const payload = JSON.stringify({
    from_account: '11111111-1111-1111-1111-111111111111', // Domnu Mamuleanu
    to_account: '44444444-4444-4444-4444-444444444444',   // Badea Cornel
    amount: 10
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      // Aceeași cheie pentru toate request-urile ca să testăm idempotența!
      'Idempotency-Key': 'spam-mamuleanu-badea', 
    },
  };
  
  const res = http.post(url, payload, params);
  
  check(res, {
    'statusul este 200': (r) => r.status === 200,
  });
}