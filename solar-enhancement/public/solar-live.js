const finite = (value) => typeof value === 'number' && Number.isFinite(value)
const nonnegative = (value) => finite(value) && value >= 0 ? value : null
const signed = (value) => finite(value) ? value : null
const label = (value) => typeof value === 'string' ? value.trim().slice(0, 80) : ''

// Do not infer direction from a sign until the actual backend convention is verified.
export function gridDirection(meaning) {
  const text = label(meaning).toLowerCase()
  const exporting = /\b(export|exporting|feed-in|feeding|selling)\b/.test(text)
  const importing = /\b(import|importing|buying|purchasing)\b/.test(text)
  if (/\b(not|no|zero|unknown|neither)\b/.test(text) || exporting === importing) return null
  return exporting ? 'exporting' : 'importing'
}

export function normalizeLiveResponse(data, receivedAt = Date.now()) {
  if (!data || typeof data !== 'object' || Array.isArray(data) || !data.live || typeof data.live !== 'object' || Array.isArray(data.live)) {
    throw new TypeError('Invalid live response')
  }
  const raw = data.live
  const percent = nonnegative(raw.battery_percent)
  const live = {
    battery_percent: percent !== null && percent <= 100 ? percent : null,
    battery_meaning: label(raw.battery_meaning),
    solar_total_w: nonnegative(raw.solar_total_w),
    alphaess_reported_pv_w: nonnegative(raw.alphaess_reported_pv_w),
    house_load_w: nonnegative(raw.house_load_w),
    grid_w: signed(raw.grid_w),
    grid_meaning: label(raw.grid_meaning),
    battery_w: signed(raw.battery_w),
    alphaess_string1_w: nonnegative(raw.alphaess_string1_w),
    alphaess_string2_w: nonnegative(raw.alphaess_string2_w),
    sunny_boy_w: nonnegative(raw.sunny_boy_w),
  }
  const daily = data.today && typeof data.today === 'object' && !Array.isArray(data.today) ? data.today : {}
  const today = {
    solar_made_kwh: nonnegative(daily.solar_made_kwh),
    alphaess_reported_pv_kwh: nonnegative(daily.alphaess_reported_pv_kwh),
    bought_from_grid_kwh: nonnegative(daily.bought_from_grid_kwh),
    sold_to_grid_kwh: nonnegative(daily.sold_to_grid_kwh),
  }
  return { live, today, receivedAt }
}

export function formatPower(value) {
  if (!finite(value)) return '--'
  const magnitude = Math.abs(value)
  return magnitude >= 1000 ? `${(magnitude / 1000).toFixed(2)} kW` : `${Math.round(magnitude)} W`
}

export function formatDaily(value) {
  return nonnegative(value) === null ? '--' : `${value.toFixed(2)} kWh`
}
