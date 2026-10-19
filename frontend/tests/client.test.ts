import test from 'node:test';
import assert from 'node:assert/strict';
import { DEFAULT_TIMEOUT_MS, ApiError, shouldFetchLive, apiClient } from '../src/api/client.ts';

test('DEFAULT_TIMEOUT_MS is 35,000 ms to accommodate upstream provider latencies', () => {
  assert.equal(DEFAULT_TIMEOUT_MS, 35000);
});

test('shouldFetchLive prevents redundant fetches on errors or active loading', () => {
  // Scenario 1: Fresh state (no data, no error, not loading) -> should fetch
  assert.equal(shouldFetchLive({ data: null, error: null, loading: false }), true);
  assert.equal(shouldFetchLive(null), true);
  assert.equal(shouldFetchLive(undefined), true);

  // Scenario 2: Data already present -> do not fetch live
  assert.equal(shouldFetchLive({ data: { temp: 25 }, error: null, loading: false }), false);

  // Scenario 3: Context already recorded an error (e.g. SoilGrids 504 timeout or EE 503) -> do not fetch live
  assert.equal(
    shouldFetchLive({ data: null, error: 'SoilGrids request timed out after 15.0s', loading: false }),
    false,
    'Must not trigger live fetch when context already recorded error'
  );

  // Scenario 4: Context is actively loading -> do not trigger duplicate fetch
  assert.equal(
    shouldFetchLive({ data: null, error: null, loading: true }),
    false,
    'Must not trigger live fetch when context is already loading'
  );

  // Scenario 5: User explicitly forces refresh (force=true) -> should fetch even if error was present
  assert.equal(
    shouldFetchLive({ data: null, error: 'Previous failure', loading: false }, true),
    true,
    'Must allow explicit user forced refresh'
  );
});

test('ApiError formats status and detail correctly', () => {
  const err = new ApiError('Custom error message', 503, { code: 'UNAVAILABLE' });
  assert.equal(err.name, 'ApiError');
  assert.equal(err.message, 'Custom error message');
  assert.equal(err.status, 503);
  assert.deepEqual(err.data, { code: 'UNAVAILABLE' });
});

test('apiClient aborts with HTTP 408 on timeout', async () => {
  // Use a mock/unroutable address with a short 50ms timeout to verify abort behavior
  const startTime = Date.now();
  await assert.rejects(
    async () => {
      await apiClient('/test-timeout', { method: 'GET' }, 50);
    },
    (err: unknown) => {
      assert.ok(err instanceof ApiError);
      const apiErr = err as ApiError;
      assert.equal(apiErr.status, 408);
      assert.ok(
        apiErr.message.includes('timed out after 0.05s'),
        `Expected timeout message, got: ${apiErr.message}`
      );
      return true;
    }
  );
  const elapsed = Date.now() - startTime;
  // Should abort quickly near 50ms, well below normal request times
  assert.ok(elapsed < 2000, `Expected abort near 50ms, took ${elapsed}ms`);
});
