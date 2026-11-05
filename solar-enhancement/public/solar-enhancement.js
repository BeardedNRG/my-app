import { adviceFor, energyCost, kwhText, parseRate } from './solar-math.js'
import { disposeModel, restrictModelUrl } from './solar-model-utils.js'

const el = (id) => document.getElementById(id)
let snapshot = window.solarSnapshot ?? null
let rateStore = { import: '', export: '' }
try {
  const saved = JSON.parse(localStorage.getItem('solar-rates-v1') || '{}')
  if (typeof saved.import === 'string') rateStore.import = saved.import
  if (typeof saved.export === 'string') rateStore.export = saved.export
} catch { /* local storage is optional */ }
el('importRate').value = rateStore.import
el('exportRate').value = rateStore.export

const money = (value) => value === null ? '--' : new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(value)
function renderInsights() {
  const fresh = snapshot && Date.now() - snapshot.receivedAt <= 120000 && snapshot.receivedAt <= Date.now() + 5000
  const today = fresh ? snapshot.today : null
  const reportedPv = today?.solar_made_kwh == null && today?.alphaess_reported_pv_kwh != null
  el('dailyGeneratedLabel').textContent = reportedPv ? 'ALPHAESS PV' : 'GENERATED'
  el('dailyGenerated').textContent = kwhText(reportedPv ? today.alphaess_reported_pv_kwh : today?.solar_made_kwh)
  el('dailyImported').textContent = kwhText(today?.bought_from_grid_kwh)
  el('dailyExported').textContent = kwhText(today?.sold_to_grid_kwh)
  el('importCost').textContent = money(energyCost(today?.bought_from_grid_kwh, parseRate(el('importRate').value)))
  el('exportCredit').textContent = money(energyCost(today?.sold_to_grid_kwh, parseRate(el('exportRate').value)))
  el('solarAdvice').textContent = adviceFor(snapshot)
}
for (const [id, key] of [['importRate', 'import'], ['exportRate', 'export']]) {
  el(id).addEventListener('input', () => {
    rateStore[key] = el(id).value
    try { localStorage.setItem('solar-rates-v1', JSON.stringify(rateStore)) } catch { /* keep current tab usable */ }
    renderInsights()
  })
}
window.addEventListener('solar:live', (event) => { snapshot = event.detail; renderInsights() })
window.addEventListener('solar:offline', () => { snapshot = null; renderInsights() })
setInterval(renderInsights, 10000)
renderInsights()

const stage = el('houseStage')
let photoUrl
let photoSequence = 0
el('housePhotoFile').addEventListener('change', (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  const sequence = ++photoSequence
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 10 * 1024 * 1024) {
    el('houseStatus').textContent = 'Choose a JPG, PNG or WebP reference photo under 10 MB.'
    event.target.value = ''
    return
  }
  const candidateUrl = URL.createObjectURL(file)
  const preview = new Image()
  preview.onload = () => {
    if (sequence !== photoSequence) { URL.revokeObjectURL(candidateUrl); return }
    if (photoUrl) URL.revokeObjectURL(photoUrl)
    photoUrl = candidateUrl
    el('housePhoto').src = photoUrl
    el('houseReference').hidden = false
    el('houseStatus').textContent = 'Reference photo loaded locally. A separate 3D model is still needed.'
  }
  preview.onerror = () => {
    URL.revokeObjectURL(candidateUrl)
    if (sequence === photoSequence) el('houseStatus').textContent = 'Could not open that reference photo.'
  }
  preview.src = candidateUrl
  event.target.value = ''
})
let scene, camera, renderer, controls, model, objectUrl, resetCamera, loadSequence = 0
async function prepareViewer() {
  const [THREE, { OrbitControls }, { GLTFLoader }] = await Promise.all([
    import('three'), import('three/addons/controls/OrbitControls.js'), import('three/addons/loaders/GLTFLoader.js'),
  ])
  const nextRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  nextRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  nextRenderer.outputColorSpace = THREE.SRGBColorSpace
  nextRenderer.toneMapping = THREE.ACESFilmicToneMapping
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(35, 1, 0.01, 10000)
  camera.position.set(4, 3, 5)
  renderer = nextRenderer
  stage.appendChild(renderer.domElement)
  scene.add(new THREE.HemisphereLight(0xddeeff, 0x41444a, 2.5))
  const sun = new THREE.DirectionalLight(0xffe6c2, 3)
  sun.position.set(4, 8, 6)
  scene.add(sun)
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.enablePan = false
  controls.minPolarAngle = 0.05
  controls.maxPolarAngle = Math.PI * .48
  const manager = new THREE.LoadingManager()
  manager.setURLModifier(restrictModelUrl)
  const loader = new GLTFLoader(manager)
  const resize = () => {
    const width = Math.max(1, stage.clientWidth), height = Math.max(1, stage.clientHeight)
    renderer.setSize(width, height, false)
    camera.aspect = width / height
    camera.updateProjectionMatrix()
  }
  new ResizeObserver(resize).observe(stage)
  resize()
  renderer.setAnimationLoop(() => {
    if (!el('houseDetails').open || document.hidden) return
    controls.update()
    renderer.render(scene, camera)
  })
  resetCamera = (object) => {
    const box = new THREE.Box3().setFromObject(object)
    const center = box.getCenter(new THREE.Vector3())
    const size = box.getSize(new THREE.Vector3())
    const extent = Math.max(size.x, size.y, size.z, 1)
    controls.target.copy(center)
    controls.minDistance = extent * .5
    controls.maxDistance = extent * 10
    camera.position.copy(center).add(new THREE.Vector3(extent * 1.5, extent, extent * 1.5))
    camera.near = Math.max(extent / 1000, .001)
    camera.far = extent * 100
    camera.updateProjectionMatrix()
    controls.update()
  }
  return loader
}
let viewerLoaderPromise
el('houseFile').addEventListener('change', async (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  const sequence = ++loadSequence
  if (!/\.glb$/i.test(file.name) || file.size > 50 * 1024 * 1024) {
    el('houseStatus').textContent = 'Choose a self-contained GLB file smaller than 50 MB.'
    event.target.value = ''
    return
  }
  el('houseStatus').textContent = 'Opening the model locally…'
  let nextUrl
  try {
    viewerLoaderPromise ||= prepareViewer().catch((error) => {
      controls?.dispose()
      renderer?.dispose()
      renderer?.domElement.remove()
      renderer = controls = scene = camera = null
      viewerLoaderPromise = null
      throw error
    })
    const viewerLoader = await viewerLoaderPromise
    nextUrl = URL.createObjectURL(file)
    const loaded = await viewerLoader.loadAsync(nextUrl)
    if (sequence !== loadSequence) { disposeModel(loaded.scene); URL.revokeObjectURL(nextUrl); return }
    if (model) {
      scene.remove(model)
      disposeModel(model)
    }
    if (objectUrl) URL.revokeObjectURL(objectUrl)
    model = loaded.scene
    objectUrl = nextUrl
    scene.add(model)
    resetCamera(model)
    el('houseEmpty').hidden = true
    el('houseReset').hidden = false
    el('houseStatus').textContent = 'Model loaded in this tab. Drag to orbit; pinch or scroll to zoom.'
  } catch {
    if (nextUrl) URL.revokeObjectURL(nextUrl)
    if (sequence === loadSequence) el('houseStatus').textContent = 'Could not open this model. Use a self-contained GLB without external files; check that 3D graphics are available.'
  }
  event.target.value = ''
})
el('houseReset').addEventListener('click', () => { if (model && resetCamera) resetCamera(model) })
