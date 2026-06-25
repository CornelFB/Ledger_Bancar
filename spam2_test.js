import http from 'k6/http';
import { check } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

export const options = {
  vus: 100,         
  iterations: 5000, 
};

// Lista cu toți clienții băncii
const accounts = [
  '11111111-1111-1111-1111-111111111111', // Domnu Mamuleanu
  '22222222-2222-2222-2222-222222222222', // Doamna Popescu
  '33333333-3333-3333-3333-333333333333', // Florin
  '44444444-4444-4444-4444-444444444444', // Badea Cornel
  '55555555-5555-5555-5555-555555555555'  // Domnu Popescu
];

function getRandomAccount() {
  return accounts[Math.floor(Math.random() * accounts.length)];
}

export default function () {
  const url = 'http://127.0.0.1:8000/transfer';
  
  let from_account = getRandomAccount();
  let to_account = getRandomAccount();

  // Prevenim să își trimită bani lor înșiși
  while (from_account === to_account) {
    to_account = getRandomAccount();
  }

  // Se trimite o sumă la întâmplare, între 1 și 50 de cenți
  const payload = JSON.stringify({
    from_account: from_account,
    to_account: to_account,
    amount: Math.floor(Math.random() * 50) + 1 
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      // Generăm o tranzacție NOUĂ la fiecare iterație
      'Idempotency-Key': uuidv4(), 
    },
  };

  const res = http.post(url, payload, params);
  
  check(res, {
    'statusul este 200': (r) => r.status === 200,
  });
}