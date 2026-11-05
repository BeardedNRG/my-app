export function restrictModelUrl(url) {
  if (url.startsWith('blob:') || url.startsWith('data:')) return url
  throw new Error('The model references external files; use a self-contained GLB.')
}

export function disposeModel(root) {
  const geometries = new Set(), materials = new Set(), textures = new Set()
  const collectTexture = (value) => {
    if (value?.isTexture) textures.add(value)
    else if (Array.isArray(value)) value.forEach(collectTexture)
  }
  root.traverse((node) => {
    if (node.geometry) geometries.add(node.geometry)
    for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
      if (!material) continue
      materials.add(material)
      Object.values(material).forEach(collectTexture)
      for (const uniform of Object.values(material.uniforms || {})) collectTexture(uniform?.value)
    }
  })
  const bitmaps = new Set()
  for (const texture of textures) {
    const image = texture.source?.data
    if (typeof ImageBitmap !== 'undefined' && image instanceof ImageBitmap) bitmaps.add(image)
    texture.dispose()
  }
  bitmaps.forEach((bitmap) => bitmap.close())
  materials.forEach((material) => material.dispose())
  geometries.forEach((geometry) => geometry.dispose())
}
