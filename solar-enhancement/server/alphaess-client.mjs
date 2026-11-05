import { createHash } from 'node:crypto'

// Official example: https://github.com/alphaess-developer/alphacloud_open_api/blob/main/alpha_api_demo.py
// This module is server-only and deliberately exposes no settings-write operations.
const API_ORIGIN = 'https://openapi.alphaess.com'
const credentialPattern = /^[\x21-\x7e]{1,512}$/
const serialPattern = /^[A-Za-z0-9_-]{1,128}$/

function error(message) {
  // Do not expose vendor error bodies, headers, URLs, or credentials.
  return new Error(message)
}

export function createAlphaEssClient({ appId, appSecret, fetchImpl = globalThis.fetch, now = Date.now, timeoutMs = 15000 } = {}) {
  if (typeof appId !== 'string' || !credentialPattern.test(appId) || typeof appSecret !== 'string' || !credentialPattern.test(appSecret)) {
    throw error('AlphaESS credentials are not configured')
  }
  if (typeof fetchImpl !== 'function' || typeof now !== 'function' || !Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 120000) {
    throw error('AlphaESS client configuration is invalid')
  }

  async function request(path, sysSn, queryDate) {
    let timestamp
    try {
      const milliseconds = now()
      if (typeof milliseconds !== 'number' || !Number.isFinite(milliseconds) || milliseconds < 0 || milliseconds > Number.MAX_SAFE_INTEGER) throw error('Invalid clock')
      timestamp = String(Math.floor(milliseconds / 1000))
    } catch {
      throw error('AlphaESS request could not be prepared')
    }
    const sign = createHash('sha512').update(appId + appSecret + timestamp, 'ascii').digest('hex')
    const url = new URL(`/api/${path}`, API_ORIGIN)
    if (sysSn !== undefined) url.searchParams.set('sysSn', sysSn)
    if (queryDate !== undefined) url.searchParams.set('queryDate', queryDate)
    let response
    try {
      response = await fetchImpl(url, {
        method: 'GET',
        headers: { appId, timeStamp: timestamp, sign },
        redirect: 'error',
        signal: AbortSignal.timeout(timeoutMs),
      })
    } catch {
      throw error('AlphaESS request failed')
    }
    if (!response || response.ok !== true) throw error('AlphaESS request failed')
    let body
    try {
      body = await response.json()
    } catch {
      throw error('AlphaESS response was invalid')
    }
    if (!body || typeof body !== 'object' || Array.isArray(body) || body.code !== 200 || body.data === undefined || body.data === null) {
      throw error('AlphaESS response was invalid')
    }
    return body.data
  }

  return Object.freeze({
    async getEssList() {
      const data = await request('getEssList')
      if (Array.isArray(data)) return data
      if (typeof data === 'object' && typeof data.sysSn === 'string') return [data]
      throw error('AlphaESS response was invalid')
    },
    async getLastPowerData(sysSn) {
      if (typeof sysSn !== 'string' || !serialPattern.test(sysSn)) throw error('AlphaESS system identifier is invalid')
      const data = await request('getLastPowerData', sysSn)
      if (typeof data !== 'object' || Array.isArray(data)) throw error('AlphaESS response was invalid')
      return data
    },
    async getSumDataForCustomer(sysSn) {
      if (typeof sysSn !== 'string' || !serialPattern.test(sysSn)) throw error('AlphaESS system identifier is invalid')
      const data = await request('getSumDataForCustomer', sysSn)
      if (typeof data !== 'object' || Array.isArray(data)) throw error('AlphaESS response was invalid')
      return data
    },
    async getOneDateEnergyBySn(sysSn, queryDate) {
      if (typeof sysSn !== 'string' || !serialPattern.test(sysSn)) throw error('AlphaESS system identifier is invalid')
      if (typeof queryDate !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(queryDate)) throw error('AlphaESS date is invalid')
      const date = new Date(`${queryDate}T00:00:00.000Z`)
      if (Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== queryDate) throw error('AlphaESS date is invalid')
      const data = await request('getOneDateEnergyBySn', sysSn, queryDate)
      if (typeof data !== 'object' || Array.isArray(data)) throw error('AlphaESS response was invalid')
      return data
    },
  })
}
