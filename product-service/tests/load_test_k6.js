/**
 * k6 load testing script for Product Service
 * 
 * Usage:
 *   k6 run tests/load_test_k6.js
 * 
 * Install k6:
 *   https://k6.io/docs/getting-started/installation/
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 users
    { duration: '1m', target: 10 },     // Stay at 10 users
    { duration: '30s', target: 20 },    // Ramp up to 20 users
    { duration: '1m', target: 20 },     // Stay at 20 users
    { duration: '30s', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],   // 95% of requests should be below 500ms
    http_req_failed: ['rate<0.01'],     // Error rate should be less than 1%
    errors: ['rate<0.01'],
  },
};

// Base URL - adjust for your environment
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8001';

// JWT Token - in real scenario, get this from User Service
// For testing, you might need to authenticate first
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';

export default function () {
  const headers = {
    'Content-Type': 'application/json',
  };

  // Add auth token if available
  if (AUTH_TOKEN) {
    headers['Authorization'] = `Bearer ${AUTH_TOKEN}`;
  }

  // Test 1: List products (public endpoint - search)
  const searchResponse = http.get(`${BASE_URL}/api/products/search/`, {
    headers: headers,
    params: { page: 1, page_size: 20 },
  });

  const searchSuccess = check(searchResponse, {
    'search status is 200': (r) => r.status === 200,
    'search response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!searchSuccess);
  sleep(1);

  // Test 2: Get product by ID (if we have product IDs from previous calls)
  // This would require getting a product ID first, so we'll skip for now
  // In a real scenario, you'd store product IDs from list/search calls

  // Test 3: Check stock (public endpoint)
  // This requires a valid product ID, so we'll use a mock ID
  // In real scenario, get actual product IDs
  const stockResponse = http.get(`${BASE_URL}/api/products/507f1f77bcf86cd799439011/stock/`, {
    headers: headers,
  });

  const stockSuccess = check(stockResponse, {
    'stock check status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'stock response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!stockSuccess);
  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'summary.json': JSON.stringify(data),
  };
}

function textSummary(data, options) {
  // Simple text summary
  return `
    Test Summary:
    - Total requests: ${data.metrics.http_reqs.values.count}
    - Failed requests: ${data.metrics.http_req_failed.values.rate * 100}%
    - Average response time: ${data.metrics.http_req_duration.values.avg}ms
    - 95th percentile: ${data.metrics.http_req_duration.values['p(95)']}ms
  `;
}
