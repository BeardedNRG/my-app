import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createAlphaEssClient } from './alphaess-client.mjs'

const supportedFields = ['soc', 'ppv', 'pload', 'pgrid', 'pbat']

// This is a structured result, never a log of vendor data. Dependencies are
// injectable so tests do not need live credentials or access to AlphaESS.
export async function probeAccount(credentials, makeClient = createAlphaEssClient) {
  try {
    if (!credentials || typeof credentials !== 'object' || Array.isArray(credentials)) return { status: 'invalid_input' }
    const client = makeClient({ appId: credentials.appId, appSecret: credentials.appSecret })
    const systems = await client.getEssList()
    if (!Array.isArray(systems)) return { status: 'connection_failed' }
    const boundSystemCount = systems.length
    if (boundSystemCount === 0) return { status: 'no_systems', boundSystemCount }
    // Never guess which device belongs to the intended site.
    if (boundSystemCount !== 1) return { status: 'multiple_systems', boundSystemCount }
    if (!systems[0] || typeof systems[0].sysSn !== 'string') return { status: 'system_identifier_unavailable', boundSystemCount }
    let data
    try {
      data = await client.getLastPowerData(systems[0].sysSn)
    } catch {
      return { status: 'power_unavailable', boundSystemCount }
    }
    if (!data || typeof data !== 'object' || Array.isArray(data)) return { status: 'power_unavailable', boundSystemCount }
    const available = Object.fromEntries(supportedFields.map((field) => [field, typeof data[field] === 'number' && Number.isFinite(data[field])]))
    const status = Object.values(available).some(Boolean) ? 'ok' : 'no_power_fields'
    return { status, boundSystemCount, availablePowerFields: available, measurementTimeVerified: false }
  } catch {
    return { status: 'connection_failed' }
  }
}

async function readCredentials(input) {
  // No terminal echo: callers must supply a private pipe, not type into stdin.
  if (input.isTTY) throw new Error('Private input is required')
  const chunks = []
  let total = 0
  let combined
  try {
    for await (const chunk of input) {
      const bytes = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)
      chunks.push(bytes)
      total += bytes.length
      if (total > 4096) throw new Error('Input is too large')
    }
    combined = Buffer.concat(chunks)
    return JSON.parse(combined.toString('utf8'))
  } finally {
    combined?.fill(0)
    chunks.forEach((chunk) => chunk.fill(0))
  }
}

async function main() {
  let result
  try {
    if (process.argv.length !== 2) throw new Error('Arguments are not accepted')
    const credentials = await readCredentials(process.stdin)
    result = await probeAccount(credentials)
  } catch {
    result = { status: 'invalid_input' }
  }
  process.stdout.write(`${JSON.stringify(result)}\n`)
  if (!['ok', 'no_systems', 'multiple_systems'].includes(result.status)) process.exitCode = 1
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main()
