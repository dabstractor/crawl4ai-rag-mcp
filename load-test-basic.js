import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 10 },   // Stay at 10 users for 1 minute  
    { duration: '30s', target: 25 },  // Ramp up to 25 users
    { duration: '1m', target: 25 },   // Stay at 25 users for 1 minute
    { duration: '30s', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],  // 95% of requests should be below 2000ms
    http_req_failed: ['rate<0.1'],      // Less than 10% of requests should fail
  },
};

const BASE_URL = 'http://localhost:8051/api';

export default function () {
  // Test health endpoint
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
    'health response has success field': (r) => {
      try {
        const json = r.json();
        return json.hasOwnProperty('success');
      } catch (e) {
        return false;
      }
    },
  });

  sleep(1);

  // Test sources endpoint
  const sourcesRes = http.get(`${BASE_URL}/sources`);
  check(sourcesRes, {
    'sources status is 200': (r) => r.status === 200,
    'sources response has sources array': (r) => {
      try {
        const json = r.json();
        return Array.isArray(json.sources);
      } catch (e) {
        return false;
      }
    },
  });

  sleep(1);

  // Test status endpoint
  const statusRes = http.get(`${BASE_URL}/status`);
  check(statusRes, {
    'status endpoint is 200': (r) => r.status === 200,
    'status response has api_version': (r) => {
      try {
        const json = r.json();
        return json.hasOwnProperty('api_version');
      } catch (e) {
        return false;
      }
    },
  });

  sleep(2);
}