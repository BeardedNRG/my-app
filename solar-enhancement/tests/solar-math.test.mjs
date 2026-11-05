import assert from 'node:assert/strict'
import { test } from 'node:test'
import { energyCost, parseRate, adviceFor, kwhText } from '../public/solar-math.js'

test('tariff estimates use kWh and cents per kWh', () => {
  assert.equal(energyCost(3.73, 30), 1.119)
  assert.ok(Math.abs(energyCost(3.83, 5) - 0.1915) < 1e-10)
  assert.equal(energyCost(null, 10), null)
  assert.equal(energyCost(3, null), null)
  assert.equal(energyCost(-1, 10), null)
})
test('missing, invalid, and negative rates are not zero rates', () => {
  assert.equal(parseRate(''), null)
  assert.equal(parseRate('  '), null)
  assert.equal(parseRate('-5'), null)
  assert.equal(parseRate('NaN'), null)
  assert.equal(parseRate('0'), 0)
  assert.equal(parseRate('31.5'), 31.5)
})
test('advice requires fresh unambiguous direction, never watt-sign guesses', () => {
  const now = 1000000
  assert.match(adviceFor(null, now), /Waiting/)
  assert.match(adviceFor({ receivedAt: now - 121000, live: { grid_meaning: 'exporting' } }, now), /Waiting/)
  assert.match(adviceFor({ receivedAt: now, live: { grid_w: -1200 } }, now), /not clear/)
  assert.match(adviceFor({ receivedAt: now, live: { grid_w: 400, grid_meaning: 'not exporting' } }, now), /not clear/)
  assert.match(adviceFor({ receivedAt: now, live: { grid_w: 400, grid_meaning: 'importing and exporting' } }, now), /not clear/)
  assert.match(adviceFor({ receivedAt: now, live: { grid_meaning: 'exporting' } }, now), /unavailable/)
  assert.match(adviceFor({ receivedAt: now, live: { grid_meaning: 'exporting', grid_w: 0 } }, now), /zero/)
  assert.match(adviceFor({ receivedAt: now, live: { grid_meaning: 'exporting', grid_w: -1200 } }, now), /reports export.*time is not confirmed/)
  assert.match(adviceFor({ receivedAt: now, live: { grid_meaning: 'importing', grid_w: 1200 } }, now), /reports import.*time is not confirmed/)
})
test('missing energy is shown as unavailable', () => {
  assert.equal(kwhText(null), '--')
  assert.equal(kwhText(0), '0.00 kWh')
  assert.equal(kwhText(21.99), '21.99 kWh')
})
