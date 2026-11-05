import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { runInNewContext } from 'node:vm'
import { test } from 'node:test'
import { normalizeLiveResponse, formatPower, formatDaily, gridDirection } from '../public/solar-live.js'

test('the actual live panel clears old readings when a refresh fails', async () => {
  const html = await readFile(new URL('../public/index.html', import.meta.url), 'utf8')
  const match = html.match(/<script type="module">([\s\S]*?)<\/script>/)
  assert.ok(match, 'live panel module is present')
  const source = match[1].replace(/^\s*import\s+\{[^}]+\}\s+from\s+['"]\.\/solar-live\.js['"];?/, '')
  const elements = new Map(), intervals = []
  const element = (id) => {
    if (!elements.has(id)) elements.set(id, {
      textContent: '', value: '', style: {}, classList: { toggle() {}, add() {}, remove() {}, contains() { return false } },
      appendChild() {}, addEventListener() {},
      getContext() { return { clearRect() {}, fillRect() {}, beginPath() {}, arc() {}, fill() {}, createRadialGradient() { return { addColorStop() {} } } } },
    })
    return elements.get(id)
  }
  let calls = 0, resolveSlow
  const events = []
  const context = {
    normalizeLiveResponse, formatPower, formatDaily, gridDirection, URLSearchParams, AbortController,
    location: { search: '?key=example' }, localStorage: { setItem() {}, getItem() { return null } },
    document: { getElementById: element, createElement: () => element('created') },
    fetch: async () => {
      calls++
      if (calls === 1) return { ok: true, json: async () => ({ live: { battery_percent: 82, battery_meaning: 'Charging', solar_total_w: 3540, house_load_w: 1430, grid_w: 0, grid_meaning: 'Idle' }, today: { solar_made_kwh: 21.99 } }) }
      if (calls === 2) return { ok: false, json: async () => ({ error: 'private upstream detail' }) }
      if (calls === 4) return await new Promise((resolve) => { resolveSlow = resolve })
      if (calls === 5) return { ok: true, json: async () => ({ live: { battery_percent: 60 } }) }
      if (calls === 6) return { ok: true, json: async () => ({ live: { alphaess_reported_pv_w: 1200 }, today: { alphaess_reported_pv_kwh: 4.5 } }) }
      if (calls === 7) return { ok: true, json: async () => ({ live: { grid_w: 500, battery_w: -700 } }) }
      if (calls === 8) return { ok: true, json: async () => ({ live: { grid_w: 0, battery_w: 0, grid_meaning: 'Exporting', battery_meaning: 'Charging' } }) }
      if (calls === 9) return { ok: true, json: async () => ({ live: { grid_meaning: 'Exporting', battery_meaning: 'Charging' } }) }
      return { ok: true, json: async () => ({ live: {} }) }
    },
    Event: class { constructor(type) { this.type = type } },
    CustomEvent: class { constructor(type, init) { this.type = type; this.detail = init.detail } },
    setTimeout, clearTimeout, setInterval: (callback, delay) => { intervals.push({ callback, delay }) },
    requestAnimationFrame() {}, addEventListener() {}, innerWidth: 800, innerHeight: 600, devicePixelRatio: 1,
  }
  context.window = context
  context.dispatchEvent = (event) => events.push(event)
  runInNewContext(source, context)
  await new Promise((resolve) => setImmediate(resolve))
  assert.equal(element('soc').textContent, '82%')
  assert.equal(element('solar').textContent, '3.54 kW')
  assert.equal(element('tMade').textContent, '21.99 kWh')
  assert.ok(events.some((event) => event.type === 'solar:live'))
  await intervals.find((interval) => interval.delay === 30000).callback()
  assert.equal(element('soc').textContent, '--')
  assert.equal(element('solar').textContent, '--')
  assert.equal(element('tMade').textContent, '--')
  assert.equal(element('age').textContent, 'Connection unavailable')
  assert.equal(context.solarSnapshot, null)
  assert.equal(events.at(-1).type, 'solar:offline')
  await intervals.find((interval) => interval.delay === 30000).callback()
  assert.equal(element('age').textContent, 'No system readings in response')
  assert.equal(element('soc').textContent, '--')
  const refresh = intervals.find((interval) => interval.delay === 30000).callback
  const older = refresh()
  await refresh()
  resolveSlow({ ok: true, json: async () => ({ live: { battery_percent: 10 } }) })
  await older
  assert.equal(element('soc').textContent, '60%', 'an older response cannot replace a newer reading')
  await refresh()
  assert.equal(element('solar').textContent, '1.20 kW')
  assert.equal(element('solarLabel').textContent, 'ALPHAESS PV')
  assert.equal(element('tMade').textContent, '4.50 kWh')
  assert.equal(element('tMadeLabel').textContent, 'AlphaESS PV today')
  await refresh()
  assert.equal(element('gridState').textContent, 'direction unconfirmed')
  assert.equal(element('batFlow').textContent, 'direction unconfirmed')
  await refresh()
  assert.equal(element('gridState').textContent, '')
  assert.equal(element('batFlow').textContent, '')
  await refresh()
  assert.equal(element('gridState').textContent, '')
  assert.equal(element('batFlow').textContent, '')
})
