import { gridDirection } from './solar-live.js'

const finiteNonnegative = (value) => typeof value === 'number' && Number.isFinite(value) && value >= 0
export function energyCost(energyKwh, centsPerKwh) {
  if (!finiteNonnegative(energyKwh) || !finiteNonnegative(centsPerKwh)) return null
  return (energyKwh * centsPerKwh) / 100
}
export function parseRate(value) {
  if (typeof value !== 'string' || value.trim() === '') return null
  const rate = Number(value)
  return finiteNonnegative(rate) && rate <= 1000 ? rate : null
}
export function adviceFor(snapshot, now = Date.now()) {
  if (!snapshot || !Number.isFinite(snapshot.receivedAt) || now - snapshot.receivedAt > 120000 || snapshot.receivedAt > now + 5000) return 'Waiting for a recent response before suggesting when to use power.'
  const direction = gridDirection(snapshot.live?.grid_meaning)
  const flow = snapshot.live?.grid_w
  if (flow === 0) return 'The latest response reports zero grid flow. Its measurement time is not confirmed; check again before shifting an appliance.'
  if (typeof flow !== 'number' || !Number.isFinite(flow)) return 'Grid flow is unavailable, so there is not enough information for a timing suggestion.'
  if (direction === 'exporting') return 'The latest response reports export. Its measurement time is not confirmed; check current flow before running a flexible appliance.'
  if (direction === 'importing') return 'The latest response reports import. Its measurement time is not confirmed; check current flow before shifting a flexible appliance.'
  return 'Check the solar, house and battery readings together before shifting an appliance. The grid direction is not clear enough for a specific suggestion.'
}
export function kwhText(value) {
  return finiteNonnegative(value) ? `${value.toFixed(2)} kWh` : '--'
}
