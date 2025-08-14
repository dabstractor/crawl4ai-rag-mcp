import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 5 },   // Ramp up to 5 users
    { duration: '2m', target: 5 },    // Stay at 5 users for 2 minutes
    { duration: '30s', target: 15 },  // Ramp up to 15 users
    { duration: '2m', target: 15 },   // Stay at 15 users for 2 minutes
    { duration: '30s', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<10000'],  // 95% of requests should be below 10000ms (search can be slow)
    http_req_failed: ['rate<0.2'],       // Less than 20% of requests should fail
  },
};

const BASE_URL = 'http://localhost:8051/api';

// Test queries for different scenarios
const testQueries = [
  'python',
  'javascript', 
  'api documentation',
  'web scraping',
  'machine learning',
  'database query',
  'authentication',
  'error handling',
  'performance optimization',
  'data visualization'
];

export default function () {
  // Pick a random query
  const randomQuery = testQueries[Math.floor(Math.random() * testQueries.length)];
  
  // Test GET search endpoint
  const searchParams = new URLSearchParams({
    query: randomQuery,
    match_count: '5'
  });
  
  const searchRes = http.get(`${BASE_URL}/search?${searchParams.toString()}`);
  check(searchRes, {
    'search status is 200': (r) => r.status === 200,
    'search response has success field': (r) => {
      try {
        const json = r.json();
        return json.hasOwnProperty('success');
      } catch (e) {
        return false;
      }
    },
    'search response has data array': (r) => {
      try {
        const json = r.json();
        return Array.isArray(json.data);
      } catch (e) {
        return false;
      }
    },
  });

  sleep(2);

  // Test POST search endpoint
  const postSearchPayload = {
    query: randomQuery,
    match_count: 3
  };

  const postSearchRes = http.post(`${BASE_URL}/search`, JSON.stringify(postSearchPayload), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(postSearchRes, {
    'POST search status is 200': (r) => r.status === 200,
    'POST search response has success field': (r) => {
      try {
        const json = r.json();
        return json.hasOwnProperty('success');
      } catch (e) {
        return false;
      }
    },
  });

  sleep(3);

  // Test code examples endpoint
  const codeQuery = ['python example', 'javascript function', 'api usage', 'data processing'][Math.floor(Math.random() * 4)];
  const codeParams = new URLSearchParams({
    query: codeQuery,
    match_count: '3'
  });
  
  const codeRes = http.get(`${BASE_URL}/code-examples?${codeParams.toString()}`);
  check(codeRes, {
    'code examples status is 200': (r) => r.status === 200,
    'code examples response has success field': (r) => {
      try {
        const json = r.json();
        return json.hasOwnProperty('success');
      } catch (e) {
        return false;
      }
    },
  });

  sleep(4);
}