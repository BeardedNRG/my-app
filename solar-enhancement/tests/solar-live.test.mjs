import assert from 'node:assert/strict'
import { test } from 'node:test'
import { formatDaily, formatPower, gridDirection, normalizeLiveResponse } from '../public/solar-live.js'

test('normalization keeps absent and impossible readings unavailable', () => {
  assert.throws(() => normalizeLiveResponse({}), /Invalid live response/)
  assert.throws(() => normalizeLiveResponse({ live: [] }), /Invalid live response/)
  const snapshot = normalizeLiveResponse({ live: { battery_percent: null, battery_meaning: null, solar_total_w: -2, house_load_w: NaN, grid_w: -1540 }, today: { solar_made_kwh: 0, sold_to_grid_kwh: -1 } }, 42)
  assert.equal(snapshot.receivedAt, 42)
  assert.equal(snapshot.live.battery_percent, null)
  assert.equal(snapshot.live.battery_meaning, '')
  assert.equal(snapshot.live.solar_total_w, null)
  assert.equal(snapshot.live.house_load_w, null)
  assert.equal(snapshot.live.grid_w, -1540)
  assert.equal(snapshot.today.solar_made_kwh, 0)
  assert.equal(snapshot.today.sold_to_grid_kwh, null)
  assert.equal(normalizeLiveResponse({ live: { battery_percent: 101 } }).live.battery_percent, null)
})

test('energy labels never infer a direction from signed watts', () => {
  assert.equal(formatPower(null), '--')
  assert.equal(formatPower(-1540), '1.54 kW')
  assert.equal(formatPower(0), '0 W')
  assert.equal(formatDaily(null), '--')
  assert.equal(formatDaily(0), '0.00 kWh')
  assert.equal(formatDaily(21.990000000000002), '21.99 kWh')
  assert.equal(gridDirection('exporting'), 'exporting')
  assert.equal(gridDirection('importing'), 'importing')
  assert.equal(gridDirection('not exporting'), null)
  assert.equal(gridDirection('importing and exporting'), null)
  assert.equal(gridDirection('unknown'), null)
})
