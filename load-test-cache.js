import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '2m', target: 10 },   // Stay at 10 users for 2 minutes
    { duration: '30s', target: 20 },  // Ramp up to 20 users
    { duration: '2m', target: 20 },   // Stay at 20 users for 2 minutes
    { duration: '30s', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'],   // 95% of requests should be below 5000ms
    http_req_failed: ['rate<0.1'],       // Less than 10% of requests should fail
  },
};

const BASE_URL = 'http://localhost:8051/api';

// Fixed queries to test cache effectiveness
const cachedQueries = [
  'python tutorial',
  'javascript guide', 
  'api documentation',
  'web development',
  'database management'
];

export default function () {
  // Use the same queries repeatedly to test cache effectiveness
  const query = cachedQueries[Math.floor(Math.random() * cachedQueries.length)];
  
  // First, get cache stats
  const cacheStatsRes = http.get(`${BASE_URL}/cache-stats`);
  check(cacheStatsRes, {
    'cache-stats status is 200': (r) => r.status === 200,
    'cache-stats has sources cache': (r) => {
      try {
        const json = r.json();
        return json.hasOwnProperty('sources_cache');
      } catch (e) {
        return false;
      }
    },
  });

  sleep(0.5);

  // Test health endpoint (should be cached after first call)
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
  });

  sleep(0.5);

  // Test sources endpoint (should be cached)
  const sourcesRes = http.get(`${BASE_URL}/sources`);
  check(sourcesRes, {
    'sources status is 200': (r) => r.status === 200,
  });

  sleep(1);

  // Test search with same queries (should benefit from caching)
  const searchRes = http.get(`${BASE_URL}/search?query=${encodeURIComponent(query)}&match_count=5`);
  check(searchRes, {
    'search status is 200': (r) => r.status === 200,
    'search has data': (r) => {
      try {
        const json = r.json();
        return json.hasOwnProperty('data');
      } catch (e) {
        return false;
      }
    },
  });

  sleep(1);

  // Test code examples with same patterns
  const codeQuery = ['python', 'javascript', 'api'][Math.floor(Math.random() * 3)];
  const codeRes = http.get(`${BASE_URL}/code-examples?query=${encodeURIComponent(codeQuery)}&match_count=3`);
  check(codeRes, {
    'code examples status is 200': (r) => r.status === 200,
  });

  sleep(2);

  // Occasionally clear cache to test performance difference
  if (Math.random() < 0.05) { // 5% chance
    const clearRes = http.post(`${BASE_URL}/cache-clear`);
    check(clearRes, {
      'cache clear status is 200': (r) => r.status === 200,
      'cache cleared successfully': (r) => {
        try {
          const json = r.json();
          return json.success === true;
        } catch (e) {
          return false;
        }
      },
    });
    sleep(1);
  }
}