// Translate the vendor's read-only responses to the existing app's contract.
// Fields and sign conventions must still be checked on the real installation.
const finite = (value) => typeof value === 'number' && Number.isFinite(value) ? value : null
const nonnegative = (value) => {
  const number = finite(value)
  return number !== null && number >= 0 ? number : null
}

export function mapAlphaEssSnapshot(power, energy, { todayDate, powerCoverageVerified = false, energyCoverageVerified = false } = {}) {
  const p = power && typeof power === 'object' && !Array.isArray(power) ? power : {}
  const e = energy && typeof energy === 'object' && !Array.isArray(energy) && typeof todayDate === 'string' && energy.theDate === todayDate ? energy : {}
  const strings = p.ppvDetail && typeof p.ppvDetail === 'object' && !Array.isArray(p.ppvDetail) ? p.ppvDetail : {}
  const soc = nonnegative(p.soc)
  return {
    live: {
      battery_percent: soc !== null && soc <= 100 ? soc : null,
      battery_meaning: '',
      solar_total_w: powerCoverageVerified === true ? nonnegative(p.ppv) : null,
      alphaess_reported_pv_w: nonnegative(p.ppv),
      house_load_w: nonnegative(p.pload),
      grid_w: finite(p.pgrid),
      grid_meaning: '',
      battery_w: finite(p.pbat),
      alphaess_string1_w: nonnegative(strings.ppv1),
      alphaess_string2_w: nonnegative(strings.ppv2),
      sunny_boy_w: null,
    },
    today: {
      solar_made_kwh: energyCoverageVerified === true ? nonnegative(e.epv) : null,
      alphaess_reported_pv_kwh: nonnegative(e.epv),
      bought_from_grid_kwh: nonnegative(e.eInput),
      sold_to_grid_kwh: nonnegative(e.eOutput),
      charged_kwh: nonnegative(e.eCharge),
      discharged_kwh: nonnegative(e.eDischarge),
    },
    measurement_time: null,
  }
}

export async function readAlphaEssDashboard(client, systemId, { timeZone, clock = () => new Date(), powerCoverageVerified = false, energyCoverageVerified = false } = {}) {
  const power = await client.getLastPowerData(systemId)
  let energy = null
  let todayDate
  if (typeof timeZone === 'string' && timeZone) {
    try {
      const dateAtSite = () => {
        const parts = new Intl.DateTimeFormat('en-CA', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(clock())
        const fields = Object.fromEntries(parts.map((part) => [part.type, part.value]))
        return `${fields.year}-${fields.month}-${fields.day}`
      }
      todayDate = dateAtSite()
      const candidate = await client.getOneDateEnergyBySn(systemId, todayDate)
      if (dateAtSite() === todayDate) energy = candidate
    } catch {
      // Power can still be shown if the site's time zone or daily data is unavailable.
    }
  }
  return mapAlphaEssSnapshot(power, energy, { todayDate, powerCoverageVerified, energyCoverageVerified })
}
