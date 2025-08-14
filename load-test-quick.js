import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  stages: [
    { duration: '15s', target: 5 },   // Ramp up to 5 users
    { duration: '30s', target: 5 },   // Stay at 5 users for 30 seconds
    { duration: '15s', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'],   // 95% of requests should be below 5000ms
    http_req_failed: ['rate<0.1'],       // Less than 10% of requests should fail
  },
};

const BASE_URL = 'http://localhost:8051/api';

export default function () {
  // Test health endpoint
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
  });

  sleep(1);

  // Test status endpoint  
  const statusRes = http.get(`${BASE_URL}/status`);
  check(statusRes, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(1);

  // Test sources endpoint
  const sourcesRes = http.get(`${BASE_URL}/sources`);
  check(sourcesRes, {
    'sources status is 200': (r) => r.status === 200,
  });

  sleep(2);
}