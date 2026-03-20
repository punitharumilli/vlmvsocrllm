export function parseXmlPoints(xmlText) {
  const points = {}
  if (!xmlText || !xmlText.trim()) return points

  const parser = new DOMParser()
  const doc = parser.parseFromString(xmlText, 'application/xml')
  const parseErr = doc.querySelector('parsererror')
  if (parseErr) {
    throw new Error('Invalid XML document')
  }

  function localTagName(tagName) {
    if (!tagName) return ''
    const idx = tagName.indexOf(':')
    return idx >= 0 ? tagName.slice(idx + 1) : tagName
  }

  function walk(elem, path) {
    const tag = localTagName(elem.tagName)
    const currentPath = path ? `${path}/${tag}` : tag

    for (const attr of Array.from(elem.attributes || [])) {
      const attrName = localTagName(attr.name)
      points[`${currentPath}@${attrName}`] = String(attr.value).trim().replace(/\s+/g, ' ')
    }

    // Leaf text only when there are no element children.
    const childElements = Array.from(elem.children || [])
    const text = (elem.textContent || '').trim().replace(/\s+/g, ' ')
    if (text && childElements.length === 0) {
      points[currentPath] = text
    }

    const counts = {}
    childElements.forEach((child) => {
      const childTag = localTagName(child.tagName)
      const idx = counts[childTag] || 0
      counts[childTag] = idx + 1
      walk(child, `${currentPath}[${idx}]`)
    })
  }

  if (doc.documentElement) {
    walk(doc.documentElement, '')
  }

  return normalizePoints(points)
}

const UNIT_MAP = {
  '%': { dsiUnit: '\\percent', factor: 1 },
  percent: { dsiUnit: '\\percent', factor: 1 },
  ppm: { dsiUnit: '\\one', factor: 1e-6 },
  ppb: { dsiUnit: '\\one', factor: 1e-9 },
  one: { dsiUnit: '\\one', factor: 1 },
  'mg/kg': { dsiUnit: '\\milli\\gram\\kilogram\\tothe{-1}', factor: 1 },
  'mgkg-1': { dsiUnit: '\\milli\\gram\\kilogram\\tothe{-1}', factor: 1 },
  'ug/kg': { dsiUnit: '\\micro\\gram\\kilogram\\tothe{-1}', factor: 1 },
  'µg/kg': { dsiUnit: '\\micro\\gram\\kilogram\\tothe{-1}', factor: 1 },
  'μg/kg': { dsiUnit: '\\micro\\gram\\kilogram\\tothe{-1}', factor: 1 },
  'g/kg': { dsiUnit: '\\gram\\kilogram\\tothe{-1}', factor: 1 },
  mg: { dsiUnit: '\\milli\\gram', factor: 1 },
  g: { dsiUnit: '\\gram', factor: 1 },
  kg: { dsiUnit: '\\kilogram', factor: 1 },
  ug: { dsiUnit: '\\micro\\gram', factor: 1 },
  'µg': { dsiUnit: '\\micro\\gram', factor: 1 },
  'μg': { dsiUnit: '\\micro\\gram', factor: 1 },
  l: { dsiUnit: '\\litre', factor: 1 },
  ml: { dsiUnit: '\\milli\\litre', factor: 1 },
  pa: { dsiUnit: '\\pascal', factor: 1 },
  bar: { dsiUnit: '\\pascal', factor: 100000 },
  mbar: { dsiUnit: '\\pascal', factor: 100 },
  hpa: { dsiUnit: '\\pascal', factor: 100 },
}

function numStr(s) {
  return String(s).replace(/[^0-9.eE+-]/g, '')
}

function normalizeUnitKey(unit) {
  return String(unit || '')
    .replace(/^\s*in\s+/i, '')
    .replace(/\s+/g, '')
    .replace(/⁻/g, '-')
    .replace(/¹/g, '1')
    .replace(/²/g, '2')
    .replace(/³/g, '3')
    .toLowerCase()
}

function convertToDsi(value, unit) {
  const val = value == null ? '' : String(value).trim()
  const rawUnit = unit == null ? '' : String(unit).trim()
  if (!rawUnit) return { dsiValue: val, dsiUnit: '' }
  if (rawUnit.startsWith('\\')) return { dsiValue: val, dsiUnit: rawUnit }

  const rule = UNIT_MAP[normalizeUnitKey(rawUnit)]
  if (!rule) return { dsiValue: val, dsiUnit: rawUnit }

  const n = Number.parseFloat(numStr(val))
  if (Number.isNaN(n)) {
    return { dsiValue: val, dsiUnit: rule.dsiUnit }
  }

  const dsiValue = rule.factor === 1 ? val : Number((n * rule.factor).toPrecision(10)).toString()
  return { dsiValue, dsiUnit: rule.dsiUnit }
}

function normalizePoints(points) {
  const out = {}

  for (const [k, v] of Object.entries(points)) {
    if (k.includes('/uniqueIdentifier')) continue
    if (k.includes('/document')) continue
    if (k.includes('/validity') && k.includes('/dispatchDate')) continue
    if (k.includes('/mainSigner')) continue
    out[k] = v
  }

  for (const [k, unitValue] of Object.entries(out)) {
    if (!k.endsWith('/unit')) continue
    const valueKey = `${k.slice(0, -5)}/value`
    if (!(valueKey in out)) continue
    const { dsiValue, dsiUnit } = convertToDsi(out[valueKey], unitValue)
    out[valueKey] = dsiValue
    out[k] = dsiUnit
  }

  return out
}
