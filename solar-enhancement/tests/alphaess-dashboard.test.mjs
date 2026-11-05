import assert from 'node:assert/strict'
import { test } from 'node:test'
import { mapAlphaEssSnapshot, readAlphaEssDashboard } from '../server/alphaess-dashboard.mjs'

test('maps documented AlphaESS readings without claiming unverified directions or second-inverter output', () => {
  const result = mapAlphaEssSnapshot({ soc: 82.4, ppv: 3540, pload: 1430, pgrid: -800, pbat: 2110, ppvDetail: { ppv1: 1900, ppv2: 1640 }, sysSn: 'private' }, { theDate: '2026-11-04', epv: 21.99, eInput: 3.73, eOutput: 3.83, eCharge: 12.2, eDischarge: 3 }, { todayDate: '2026-11-04' })
  assert.equal(result.live.battery_percent, 82.4)
  assert.equal(result.live.solar_total_w, null)
  assert.equal(result.live.alphaess_reported_pv_w, 3540)
  assert.equal(result.live.alphaess_string1_w, 1900)
  assert.equal(result.live.grid_w, -800)
  assert.equal(result.live.grid_meaning, '')
  assert.equal(result.live.battery_meaning, '')
  assert.equal(result.live.sunny_boy_w, null)
  assert.equal(result.today.solar_made_kwh, null)
  assert.equal(result.today.alphaess_reported_pv_kwh, 21.99)
  assert.equal(result.today.bought_from_grid_kwh, 3.73)
  assert.equal(result.today.sold_to_grid_kwh, 3.83)
  assert.equal(result.measurement_time, null)
  assert.equal(JSON.stringify(result).includes('private'), false)
})

test('missing and invalid input stays unavailable, never zero or fabricated', () => {
  const result = mapAlphaEssSnapshot({ soc: 101, ppv: -2, pload: null, pgrid: NaN, ppvDetail: null }, null)
  assert.equal(result.live.battery_percent, null)
  assert.equal(result.live.solar_total_w, null)
  assert.equal(result.live.grid_w, null)
  assert.equal(result.live.alphaess_string1_w, null)
  assert.equal(result.today.solar_made_kwh, null)
  assert.equal(mapAlphaEssSnapshot({ soc: 0, ppv: 0 }, { theDate: '2026-11-04', epv: 0 }, { todayDate: '2026-11-04', energyCoverageVerified: true }).today.solar_made_kwh, 0)
  const independent = mapAlphaEssSnapshot({ ppv: 100 }, { theDate: '2026-11-04', epv: 4 }, { todayDate: '2026-11-04', powerCoverageVerified: true })
  assert.equal(independent.live.solar_total_w, 100)
  assert.equal(independent.today.solar_made_kwh, null)
})

test('a daily-data failure does not suppress a valid power response', async () => {
  const fake = { getLastPowerData: async () => ({ soc: 50 }), getOneDateEnergyBySn: async () => { throw new Error('private upstream detail') } }
  const result = await readAlphaEssDashboard(fake, 'test-system', { timeZone: 'Australia/Brisbane' })
  assert.equal(result.live.battery_percent, 50)
  assert.equal(result.today.solar_made_kwh, null)
  assert.equal(JSON.stringify(result).includes('private upstream detail'), false)
})

test('today is derived from the site timezone and mismatched vendor dates are withheld', async () => {
  const dates = []
  const fake = { getLastPowerData: async () => ({ ppv: 10 }), getOneDateEnergyBySn: async (_id, date) => { dates.push(date); return { theDate: '2026-11-03', eInput: 17, epv: 20 } } }
  const result = await readAlphaEssDashboard(fake, 'test-system', { timeZone: 'Australia/Brisbane', clock: () => new Date('2026-11-03T16:00:00Z'), powerCoverageVerified: true, energyCoverageVerified: true })
  assert.deepEqual(dates, ['2026-11-04'])
  assert.equal(result.today.bought_from_grid_kwh, null)
  assert.equal(result.today.solar_made_kwh, null)
  assert.equal(result.live.solar_total_w, 10)
})

test('a daily request crossing the site midnight cannot report yesterday as today', async () => {
  const times = [new Date('2026-11-03T13:59:59Z'), new Date('2026-11-03T14:00:01Z')]
  const fake = { getLastPowerData: async () => ({ soc: 50 }), getOneDateEnergyBySn: async (_id, date) => ({ theDate: date, eInput: 12 }) }
  const result = await readAlphaEssDashboard(fake, 'test-system', { timeZone: 'Australia/Brisbane', clock: () => times.shift() })
  assert.equal(result.today.bought_from_grid_kwh, null)
})

test('a failed second clock check cannot expose unverified daily data', async () => {
  let calls = 0
  const fake = { getLastPowerData: async () => ({ soc: 50 }), getOneDateEnergyBySn: async (_id, date) => ({ theDate: date, eInput: 12 }) }
  const result = await readAlphaEssDashboard(fake, 'test-system', { timeZone: 'Australia/Brisbane', clock: () => { if (++calls > 1) throw new Error('clock failed'); return new Date('2026-11-03T13:59:59Z') } })
  assert.equal(result.today.bought_from_grid_kwh, null)
})
