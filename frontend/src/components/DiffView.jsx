import { useMemo } from 'react'
import { computeWordDiff } from '../utils/jsonDiff.js'
import { parseXmlPoints } from '../utils/xmlCompare.js'

/**
 * Render word-diff segments as React elements with highlights.
 */
function renderSegments(segments) {
  return segments.map((seg, i) =>
    seg.diff
      ? <mark key={i} className="diff-highlight">{seg.text}</mark>
      : <span key={i}>{seg.text}</span>
  )
}

/**
 * Render a cell value with word-level highlighting against the other side.
 */
function DiffCell({ value, masterValue, status }) {
  if (!value) return <span className="diff-empty">--</span>

  if (status === 'wrong' && masterValue) {
    const segments = computeWordDiff(value, masterValue)
    return <span>{renderSegments(segments)}</span>
  }

  if (status === 'missing') {
    return <mark className="diff-highlight">{value}</mark>
  }

  return <span>{value}</span>
}

export default function DiffView({ masterXml, vlmXml, ocrXml }) {
  const { rows, stats } = useMemo(() => {
    const master = parseXmlPoints(masterXml || '')
    const vlm = parseXmlPoints(vlmXml || '')
    const ocr = parseXmlPoints(ocrXml || '')

    const masterKeys = Object.keys(master).sort()

    let vlmCorrect = 0
    let vlmWrong = 0
    let ocrCorrect = 0
    let ocrWrong = 0

    const rows = masterKeys.map((key) => {
      const mVal = master[key] ?? ''
      const vVal = vlm[key] ?? ''
      const oVal = ocr[key] ?? ''

      const vlmStatus = vVal === mVal ? 'match' : (vVal ? 'wrong' : 'missing')
      const ocrStatus = oVal === mVal ? 'match' : (oVal ? 'wrong' : 'missing')

      if (vlmStatus === 'match') vlmCorrect++
      else vlmWrong++

      if (ocrStatus === 'match') ocrCorrect++
      else ocrWrong++

      return { key, mVal, vVal, oVal, vlmStatus, ocrStatus }
    })

    const vlmExtra = Object.keys(vlm).filter((k) => !(k in master)).length
    const ocrExtra = Object.keys(ocr).filter((k) => !(k in master)).length

    return {
      rows,
      stats: {
        total: masterKeys.length,
        vlmCorrect,
        vlmWrong,
        ocrCorrect,
        ocrWrong,
        vlmExtra,
        ocrExtra,
      },
    }
  }, [masterXml, vlmXml, ocrXml])

  if (!masterXml) {
    return <div className="diff-view"><p style={{ padding: 24, color: 'var(--text-muted)' }}>No results to compare.</p></div>
  }

  const vlmPct = stats.total > 0
    ? ((stats.vlmCorrect / stats.total) * 100).toFixed(1)
    : '0.0'
  const ocrPct = stats.total > 0
    ? ((stats.ocrCorrect / stats.total) * 100).toFixed(1)
    : '0.0'

  return (
    <div className="diff-view">
      <div className="diff-toolbar">
        <div className="diff-stats">
          <span className="diff-stat">
            <span className="diff-stat-dot match" />
            VLM: {stats.vlmCorrect} correct / {stats.vlmWrong} wrong ({vlmPct}%)
          </span>
          <span className="diff-stat">
            <span className="diff-stat-dot match" />
            OCR: {stats.ocrCorrect} correct / {stats.ocrWrong} wrong ({ocrPct}%)
          </span>
          <span className="diff-stat">
            <span className="diff-stat-dot changed" />
            VLM extra: {stats.vlmExtra}
          </span>
          <span className="diff-stat">
            <span className="diff-stat-dot changed" />
            OCR extra: {stats.ocrExtra}
          </span>
        </div>
        <div className="diff-legend">
          {stats.total} master XML datapoints
        </div>
      </div>

      <div className="diff-table-wrapper">
        <table className="diff-table">
          <thead>
            <tr>
              <th style={{ width: '30%' }}>Field Path</th>
              <th style={{ width: '23%' }}>Master XML</th>
              <th style={{ width: '23%' }}>VLM (Vision)</th>
              <th style={{ width: '24%' }}>OCR + LLM</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ key, mVal, vVal, oVal, vlmStatus, ocrStatus }) => (
              <tr key={key} className={`diff-row ${vlmStatus !== 'match' || ocrStatus !== 'match' ? 'changed' : 'match'}`}>
                <td>{key}</td>
                <td>{mVal || <span className="diff-empty">--</span>}</td>
                <td>
                  <DiffCell value={vVal} masterValue={mVal} status={vlmStatus} />
                </td>
                <td>
                  <DiffCell value={oVal} masterValue={mVal} status={ocrStatus} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
