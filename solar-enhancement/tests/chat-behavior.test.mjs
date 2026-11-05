import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { runInNewContext } from 'node:vm'
import { test } from 'node:test'

test('chat requires a key and recovers after an aborted request', async () => {
  const html = await readFile(new URL('../public/index.html', import.meta.url), 'utf8')
  const match = html.match(/(async function ask\(text\) \{[\s\S]*?\n\})\s*\$\("composer"\)/)
  assert.ok(match, 'actual chat function is present')
  let calls = 0, abortTimer
  const messages = []
  const context = {
    KEY: null,
    q: { value: 'initial' },
    AbortController,
    add: (cls, text) => { const msg = { className: cls, textContent: text }; messages.push(msg); return msg },
    say() {}, refresh() {},
    setTimeout: (callback) => { abortTimer = callback; return 1 },
    clearTimeout() {},
    fetch: async (_url, options) => {
      calls++
      if (calls === 1) return await new Promise((_resolve, reject) => options.signal.addEventListener('abort', () => reject(new Error('private upstream detail'))))
      if (calls === 2) return { ok: true, json: async () => ({ reply: 'Ready.', tools: {} }) }
      if (calls === 3) return { ok: true, json: async () => ({ reply: null }) }
      if (calls === 4) return { ok: true, json: async () => ({ reply: 'Another.', tools: {} }) }
      return { ok: false, status: 401, json: async () => { throw new Error('must not parse') } }
    },
  }
  runInNewContext(`let busy = 0; const hist = []; ${match[1]}; globalThis.invoke = ask; globalThis.isBusy = () => busy; globalThis.historySize = () => hist.length;`, context)
  await context.invoke('Hello')
  assert.equal(calls, 0)
  assert.match(messages.at(-1).textContent, /access link/)
  context.KEY = 'example'
  const pending = context.invoke('Hello')
  assert.equal(context.isBusy(), 1)
  abortTimer()
  await pending
  assert.equal(context.isBusy(), 0)
  assert.equal(context.historySize(), 0)
  assert.equal(context.q.value, 'Hello')
  assert.match(messages.at(-1).textContent, /Couldn.t answer/)
  assert.doesNotMatch(messages.at(-1).textContent, /private upstream detail/)
  await context.invoke('Try again')
  assert.equal(calls, 2)
  assert.equal(context.isBusy(), 0)
  assert.equal(messages.at(-1).textContent, 'Ready.')
  assert.equal(context.historySize(), 2)
  await context.invoke('Malformed')
  assert.equal(context.historySize(), 2)
  assert.equal(context.q.value, 'Malformed')
  context.say = () => { throw new Error('speech unavailable') }
  await context.invoke('Another')
  assert.equal(messages.at(-1).textContent, 'Another.')
  assert.equal(context.historySize(), 4)
  await context.invoke('Key rejected')
  assert.match(messages.at(-1).textContent, /access key wasn't accepted/)
  assert.equal(context.historySize(), 4)
})
