import assert from 'node:assert/strict'
import { test } from 'node:test'
import { GLTFLoader } from '../node_modules/three/examples/jsm/loaders/GLTFLoader.js'
import { LoadingManager } from '../node_modules/three/build/three.module.js'
import { disposeModel, restrictModelUrl } from '../public/solar-model-utils.js'

function fixtureGlb() {
  const vertices = Buffer.alloc(36)
  ;[0, 0, 0, 1, 0, 0, 0, 1, 0].forEach((value, index) => vertices.writeFloatLE(value, index * 4))
  const json = JSON.stringify({ asset: { version: '2.0' }, scene: 0, scenes: [{ nodes: [0] }], nodes: [{ mesh: 0 }], meshes: [{ primitives: [{ attributes: { POSITION: 0 } }] }], accessors: [{ bufferView: 0, componentType: 5126, count: 3, type: 'VEC3', min: [0, 0, 0], max: [1, 1, 0] }], bufferViews: [{ buffer: 0, byteOffset: 0, byteLength: 36 }], buffers: [{ byteLength: 36 }] })
  const jsonLength = Math.ceil(Buffer.byteLength(json) / 4) * 4
  const total = 12 + 8 + jsonLength + 8 + vertices.length
  const glb = Buffer.alloc(total, 0x20)
  glb.writeUInt32LE(0x46546c67, 0); glb.writeUInt32LE(2, 4); glb.writeUInt32LE(total, 8)
  glb.writeUInt32LE(jsonLength, 12); glb.writeUInt32LE(0x4e4f534a, 16); glb.write(json, 20)
  const binOffset = 20 + jsonLength
  glb.writeUInt32LE(vertices.length, binOffset); glb.writeUInt32LE(0x004e4942, binOffset + 4); vertices.copy(glb, binOffset + 8)
  return glb.buffer.slice(glb.byteOffset, glb.byteOffset + glb.byteLength)
}

test('three.js loads a real self-contained binary GLB in isolation', async () => {
  const parsed = await new Promise((resolve, reject) => new GLTFLoader().parse(fixtureGlb(), '', resolve, reject))
  assert.equal(parsed.scene.children.length, 1)
  assert.equal(parsed.scene.children[0].isMesh, true)
})
test('model loading policy can reject external asset requests', () => {
  const manager = new LoadingManager()
  manager.setURLModifier(restrictModelUrl)
  assert.throws(() => manager.resolveURL('https://example.com/texture.png'), /external files/)
  assert.equal(manager.resolveURL('data:image/png;base64,AA=='), 'data:image/png;base64,AA==')
})

test('replacing a model disposes shared GPU objects and bitmap data once', () => {
  const previousImageBitmap = globalThis.ImageBitmap
  const counts = { bitmap: 0, texture: 0, material: 0, geometry: 0 }
  globalThis.ImageBitmap = class { close() { counts.bitmap++ } }
  try {
    const image = new ImageBitmap()
    const texture = { isTexture: true, source: { data: image }, dispose() { counts.texture++ } }
    const material = { map: texture, uniforms: { map: { value: texture } }, dispose() { counts.material++ } }
    const geometry = { dispose() { counts.geometry++ } }
    disposeModel({ traverse(callback) { callback({ material, geometry }); callback({ material, geometry }) } })
    assert.deepEqual(counts, { bitmap: 1, texture: 1, material: 1, geometry: 1 })
  } finally {
    if (previousImageBitmap === undefined) delete globalThis.ImageBitmap
    else globalThis.ImageBitmap = previousImageBitmap
  }
})
