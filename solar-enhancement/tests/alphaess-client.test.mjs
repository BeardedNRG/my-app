import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createAlphaEssClient } from '../server/alphaess-client.mjs'

const fakeId = 'example-app-id'
const fakeSecret = 'example-private-secret'
const fakeSerial = 'AL-EXAMPLE_1'
const fixedNow = 1700000000123
const goodResponse = (data) => ({ ok: true, json: async () => ({ code: 200, data }) })

test('read requests use vendor signing, fixed origin, encoding and no redirects', async () => {
  const requests = []
  const client = createAlphaEssClient({
    appId: fakeId, appSecret: fakeSecret, now: () => fixedNow,
    fetchImpl: async (url, options) => {
      requests.push({ url, options })
      return goodResponse(requests.length === 1 ? [{ sysSn: fakeSerial }] : { soc: 82, pgrid: -10 })
    },
  })
  assert.deepEqual(await client.getEssList(), [{ sysSn: fakeSerial }])
  assert.deepEqual(await client.getLastPowerData(fakeSerial), { soc: 82, pgrid: -10 })
  assert.equal(requests[0].url.href, 'https://openapi.alphaess.com/api/getEssList')
  assert.equal(requests[1].url.origin, 'https://openapi.alphaess.com')
  assert.equal(requests[1].url.pathname, '/api/getLastPowerData')
  assert.equal(requests[1].url.searchParams.get('sysSn'), fakeSerial)
  // SHA-512 reference vector produced independently with Python hashlib.
  const expected = '04d15fd3c4f8be3569854a68cb0867913738ab817b5d1940066d0a7889246fa9f29844ce1ba382e41520b53f37035455e99abc3c1762c6f5d883bc2d1a3b3694'
  for (const { url, options } of requests) {
    assert.equal(options.method, 'GET')
    assert.equal(options.redirect, 'error')
    assert.equal(options.headers.appId, fakeId)
    assert.equal(options.headers.timeStamp, '1700000000')
    assert.equal(options.headers.sign, expected)
    assert.ok(options.signal instanceof AbortSignal)
    assert.equal(url.href.includes(fakeSecret), false)
  }
  assert.deepEqual(Object.keys(client).sort(), ['getEssList', 'getLastPowerData', 'getOneDateEnergyBySn', 'getSumDataForCustomer'])
})

test('daily totals and summary use read-only endpoints and require a real date', async () => {
  const requests = []
  const client = createAlphaEssClient({ appId: fakeId, appSecret: fakeSecret, now: () => fixedNow, fetchImpl: async (url) => { requests.push(url); return goodResponse({ epv: 12.5 }) } })
  for (const value of ['', '2026-2-04', '2026-02-30', '2026-13-01', '../2026-01-01', null]) {
    await assert.rejects(client.getOneDateEnergyBySn(fakeSerial, value), /date is invalid/)
  }
  await assert.rejects(client.getOneDateEnergyBySn('../bad', '2026-02-03'), /system identifier is invalid/)
  assert.equal(requests.length, 0)
  assert.deepEqual(await client.getOneDateEnergyBySn(fakeSerial, '2024-02-29'), { epv: 12.5 })
  assert.deepEqual(await client.getSumDataForCustomer(fakeSerial), { epv: 12.5 })
  assert.equal(requests[0].pathname, '/api/getOneDateEnergyBySn')
  assert.equal(requests[0].searchParams.get('queryDate'), '2024-02-29')
  assert.equal(requests[0].searchParams.get('sysSn'), fakeSerial)
  assert.equal(requests[1].pathname, '/api/getSumDataForCustomer')
  assert.equal(requests[1].searchParams.get('sysSn'), fakeSerial)
})

test('rejects unsafe configuration and serial values before making a request', async () => {
  let calls = 0
  const fetchImpl = async () => { calls++; return goodResponse({}) }
  assert.throws(() => createAlphaEssClient({ appId: '', appSecret: fakeSecret }), /credentials/)
  assert.throws(() => createAlphaEssClient({ appId: fakeId, appSecret: 'nonasciié' }), /credentials/)
  assert.throws(() => createAlphaEssClient({ appId: fakeId, appSecret: fakeSecret, timeoutMs: 0 }), /configuration/)
  const client = createAlphaEssClient({ appId: fakeId, appSecret: fakeSecret, fetchImpl })
  for (const value of ['', '../host', 'abc?sign=x', 'space here', null, 1]) {
    await assert.rejects(client.getLastPowerData(value), /system identifier is invalid/)
  }
  assert.equal(calls, 0)
})

test('upstream, parsing and clock failures do not leak diagnostic or credential content', async () => {
  const sensitive = `${fakeId} ${fakeSecret}`
  const cases = [
    async () => { throw new Error(sensitive) },
    async () => ({ ok: false, status: 403, json: async () => ({ message: sensitive }) }),
    async () => ({ ok: true, json: async () => { throw new Error(sensitive) } }),
    async () => ({ ok: true, json: async () => ({ code: 400, msg: sensitive }) }),
    async () => goodResponse(null),
  ]
  for (const fetchImpl of cases) {
    const client = createAlphaEssClient({ appId: fakeId, appSecret: fakeSecret, fetchImpl, now: () => fixedNow })
    await assert.rejects(client.getEssList(), (err) => !err.message.includes(fakeId) && !err.message.includes(fakeSecret) && !err.cause)
  }
  const client = createAlphaEssClient({ appId: fakeId, appSecret: fakeSecret, now: () => { throw new Error(sensitive) } })
  await assert.rejects(client.getEssList(), (err) => err.message === 'AlphaESS request could not be prepared' && !err.cause)
})

test('rejects malformed data and accepts a single returned system object', async () => {
  const single = createAlphaEssClient({ appId: fakeId, appSecret: fakeSecret, fetchImpl: async () => goodResponse({ sysSn: fakeSerial }) })
  assert.deepEqual(await single.getEssList(), [{ sysSn: fakeSerial }])
  const invalid = createAlphaEssClient({ appId: fakeId, appSecret: fakeSecret, fetchImpl: async () => goodResponse('not an object') })
  await assert.rejects(invalid.getEssList(), /response was invalid/)
  await assert.rejects(invalid.getLastPowerData(fakeSerial), /response was invalid/)
  await assert.rejects(invalid.getSumDataForCustomer(fakeSerial), /response was invalid/)
  await assert.rejects(invalid.getOneDateEnergyBySn(fakeSerial, '2026-11-04'), /response was invalid/)
})
