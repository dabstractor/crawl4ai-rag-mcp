import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 20 },   // Ramp up to 20 users
    { duration: '2m', target: 20 },   // Stay at 20 users for 2 minutes
    { duration: '1m', target: 50 },   // Ramp up to 50 users
    { duration: '2m', target: 50 },   // Stay at 50 users for 2 minutes
    { duration: '1m', target: 100 },  // Ramp up to 100 users (stress test)
    { duration: '2m', target: 100 },  // Stay at 100 users for 2 minutes
    { duration: '1m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<15000'],  // 95% of requests should be below 15000ms
    http_req_failed: ['rate<0.3'],       // Less than 30% of requests should fail
  },
};

const BASE_URL = 'http://localhost:8051/api';

const testScenarios = [
  // Health check scenario (lightweight)
  () => {
    const res = http.get(`${BASE_URL}/health`);
    check(res, { 'health status is 200': (r) => r.status === 200 });
    sleep(0.5);
  },
  
  // Status check scenario (lightweight)
  () => {
    const res = http.get(`${BASE_URL}/status`);
    check(res, { 'status is 200': (r) => r.status === 200 });
    sleep(0.5);
  },
  
  // Sources scenario (medium weight)
  () => {
    const res = http.get(`${BASE_URL}/sources`);
    check(res, { 'sources status is 200': (r) => r.status === 200 });
    sleep(1);
  },
  
  // Cache stats scenario (lightweight)
  () => {
    const res = http.get(`${BASE_URL}/cache-stats`);
    check(res, { 'cache-stats status is 200': (r) => r.status === 200 });
    sleep(0.5);
  },
  
  // Search scenario (heavy weight)
  () => {
    const queries = ['api', 'docs', 'code', 'example', 'tutorial'];
    const query = queries[Math.floor(Math.random() * queries.length)];
    const res = http.get(`${BASE_URL}/search?query=${query}&match_count=3`);
    check(res, { 'search status is 200': (r) => r.status === 200 });
    sleep(2);
  }
];

export default function () {
  // Randomly select a scenario with weighted probabilities
  const rand = Math.random();
  let scenario;
  
  if (rand < 0.3) {
    // 30% health checks (lightweight)
    scenario = testScenarios[0];
  } else if (rand < 0.5) {
    // 20% status checks (lightweight)
    scenario = testScenarios[1];
  } else if (rand < 0.7) {
    // 20% sources (medium)
    scenario = testScenarios[2];
  } else if (rand < 0.8) {
    // 10% cache stats (lightweight)
    scenario = testScenarios[3];
  } else {
    // 20% search (heavy)
    scenario = testScenarios[4];
  }
  
  scenario();
}