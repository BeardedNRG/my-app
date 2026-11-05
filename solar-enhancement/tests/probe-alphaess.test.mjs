import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { probeAccount } from '../server/probe-alphaess.mjs'

const credentials = { appId: 'example-id', appSecret: 'example-secret' }
const probePath = fileURLToPath(new URL('../server/probe-alphaess.mjs', import.meta.url))

test('one bound system produces only a sanitized field-presence summary', async () => {
  const calls = []
  const result = await probeAccount(credentials, (options) => {
    assert.deepEqual(options, credentials)
    return {
      getEssList: async () => { calls.push('list'); return [{ sysSn: 'private-serial' }] },
      getLastPowerData: async (serial) => {
        assert.equal(serial, 'private-serial')
        calls.push('power')
        return { soc: 82.3, ppv: 0, pload: null, pgrid: NaN, pbat: -240, extra: 'private-value' }
      },
    }
  })
  assert.deepEqual(calls, ['list', 'power'])
  assert.deepEqual(result, { status: 'ok', boundSystemCount: 1, availablePowerFields: { soc: true, ppv: true, pload: false, pgrid: false, pbat: true }, measurementTimeVerified: false })
  const output = JSON.stringify(result)
  for (const privateValue of ['example-id', 'example-secret', 'private-serial', 'private-value', '82.3', '-240']) assert.equal(output.includes(privateValue), false)
})

test('zero or multiple systems never select a device or request power', async () => {
  for (const count of [0, 2]) {
    let powerCalls = 0
    const result = await probeAccount(credentials, () => ({
      getEssList: async () => Array.from({ length: count }, () => ({ sysSn: 'private-serial' })),
      getLastPowerData: async () => { powerCalls++; return {} },
    }))
    assert.deepEqual(result, { status: count === 0 ? 'no_systems' : 'multiple_systems', boundSystemCount: count })
    assert.equal(powerCalls, 0)
  }
})

test('missing fields and failures stay generic and do not disclose upstream details', async () => {
  const empty = await probeAccount(credentials, () => ({ getEssList: async () => [{ sysSn: 'private-serial' }], getLastPowerData: async () => ({}) }))
  assert.equal(empty.status, 'no_power_fields')
  assert.deepEqual(Object.values(empty.availablePowerFields), [false, false, false, false, false])
  const noIdentifier = await probeAccount(credentials, () => ({ getEssList: async () => [{}] }))
  assert.deepEqual(noIdentifier, { status: 'system_identifier_unavailable', boundSystemCount: 1 })
  const powerFailed = await probeAccount(credentials, () => ({ getEssList: async () => [{ sysSn: 'private-serial' }], getLastPowerData: async () => { throw new Error('private-upstream-error') } }))
  assert.deepEqual(powerFailed, { status: 'power_unavailable', boundSystemCount: 1 })
  const listFailed = await probeAccount(credentials, () => ({ getEssList: async () => { throw new Error('private-upstream-error') } }))
  assert.deepEqual(listFailed, { status: 'connection_failed' })
})

test('CLI rejects arguments, malformed and excessive input without echoing it', () => {
  for (const scenario of [
    { args: ['secret-in-argument'], input: '' },
    { args: [], input: 'secret-in-malformed-json' },
    { args: [], input: 'secret-too-large'.repeat(400) },
  ]) {
    const result = spawnSync(process.execPath, [probePath, ...scenario.args], { input: scenario.input, encoding: 'utf8', timeout: 5000 })
    assert.equal(result.status, 1)
    assert.equal(result.stdout, '{"status":"invalid_input"}\n')
    assert.equal(result.stderr, '')
  }
})
