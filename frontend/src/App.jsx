import { useRef, useState } from 'react'
import './App.css'
import UploadZone from './components/UploadZone.jsx'
import ResultPanel from './components/ResultPanel.jsx'
import DiffView from './components/DiffView.jsx'
import { generateHtmlReport, generateMarkdownReport } from './utils/reportExport.js'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

function App() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState('')
  const [vlmResult, setVlmResult] = useState(null)
  const [ocrLlmResult, setOcrLlmResult] = useState(null)
  const [vlmTimeMs, setVlmTimeMs] = useState(0)
  const [ocrLlmTimeMs, setOcrLlmTimeMs] = useState(0)
  const [ocrRawText, setOcrRawText] = useState('')
  const [vlmError, setVlmError] = useState('')
  const [ocrError, setOcrError] = useState('')
  const [activeView, setActiveView] = useState('side-by-side')
  const [fileName, setFileName] = useState('')
  const [vlmInputTokens, setVlmInputTokens] = useState(0)
  const [vlmOutputTokens, setVlmOutputTokens] = useState(0)
  const [ocrInputTokens, setOcrInputTokens] = useState(0)
  const [ocrOutputTokens, setOcrOutputTokens] = useState(0)
  const [vlmXml, setVlmXml] = useState('')
  const [ocrXml, setOcrXml] = useState('')
  const [masterScore, setMasterScore] = useState(null)
  const [masterXmlName, setMasterXmlName] = useState('')
  const [masterXmlContent, setMasterXmlContent] = useState('')
  const masterXmlInputRef = useRef(null)

  async function handleUpload(file) {
    setIsProcessing(true)
    setError('')
    setVlmError('')
    setOcrError('')
    setVlmResult(null)
    setOcrLlmResult(null)
    setVlmTimeMs(0)
    setOcrLlmTimeMs(0)
    setOcrRawText('')
    setFileName(file.name)
    setVlmInputTokens(0)
    setVlmOutputTokens(0)
    setOcrInputTokens(0)
    setOcrOutputTokens(0)
    setVlmXml('')
    setOcrXml('')
    setMasterScore(null)
    setMasterXmlName('')
    setMasterXmlContent('')

    const form = new FormData()
    form.append('file', file)

    try {
      const resp = await fetch(`${API_BASE}/api/benchmark`, {
        method: 'POST',
        body: form,
      })

      if (!resp.ok) {
        const detail = await resp.json().catch(() => ({}))
        throw new Error(detail?.detail || `Request failed with status ${resp.status}`)
      }

      const data = await resp.json()

      setVlmResult(data.vlm_result)
      setOcrLlmResult(data.ocr_llm_result)
      setVlmTimeMs(data.vlm_time_ms || 0)
      setOcrLlmTimeMs(data.ocr_llm_time_ms || 0)
      setOcrRawText(data.ocr_raw_text || '')
      setVlmInputTokens(data.vlm_input_tokens || 0)
      setVlmOutputTokens(data.vlm_output_tokens || 0)
      setOcrInputTokens(data.ocr_input_tokens || 0)
      setOcrOutputTokens(data.ocr_output_tokens || 0)
      setVlmXml(data.vlm_xml || '')
      setOcrXml(data.ocr_llm_xml || '')
      setMasterScore(null)

      if (data.vlm_error) setVlmError(data.vlm_error)
      if (data.ocr_llm_error) setOcrError(data.ocr_llm_error)
    } catch (err) {
      setError(err?.message || 'Benchmark failed')
    } finally {
      setIsProcessing(false)
    }
  }

  function handleReset() {
    setIsProcessing(false)
    setError('')
    setVlmError('')
    setOcrError('')
    setVlmResult(null)
    setOcrLlmResult(null)
    setVlmTimeMs(0)
    setOcrLlmTimeMs(0)
    setOcrRawText('')
    setFileName('')
    setActiveView('side-by-side')
    setVlmInputTokens(0)
    setVlmOutputTokens(0)
    setOcrInputTokens(0)
    setOcrOutputTokens(0)
    setVlmXml('')
    setOcrXml('')
    setMasterScore(null)
    setMasterXmlName('')
    setMasterXmlContent('')
  }

  async function handleMasterXmlPicked(e) {
    const file = e.target.files?.[0]
    if (!file) return

    if (!vlmXml && !ocrXml) {
      setError('Run extraction first before comparing with master XML.')
      return
    }

    const xmlText = await file.text()
    setMasterXmlName(file.name)
    setMasterXmlContent(xmlText)
    setError('')

    const form = new FormData()
    form.append('master_xml', file)
    form.append('vlm_xml', vlmXml || '')
    form.append('ocr_llm_xml', ocrXml || '')

    try {
      const resp = await fetch(`${API_BASE}/api/compare-master`, {
        method: 'POST',
        body: form,
      })

      if (!resp.ok) {
        const detail = await resp.json().catch(() => ({}))
        throw new Error(detail?.detail || `Compare failed with status ${resp.status}`)
      }

      const data = await resp.json()
      setMasterScore(data.master_xml_score || null)
    } catch (err) {
      setError(err?.message || 'Master XML comparison failed')
    } finally {
      // Let users re-upload the same file if needed.
      e.target.value = ''
    }
  }

  function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  function handleDownloadHtml() {
    const baseName = fileName.replace(/\.[^.]+$/, '') || 'benchmark'
    const html = generateHtmlReport({
      fileName, vlmResult, ocrLlmResult, vlmTimeMs, ocrLlmTimeMs,
      vlmInputTokens, vlmOutputTokens, ocrInputTokens, ocrOutputTokens,
      masterXml: masterXmlContent,
      vlmXml,
      ocrXml,
      masterScore,
    })
    downloadFile(html, `${baseName}_benchmark.html`, 'text/html')
  }

  function handleDownloadMarkdown() {
    const baseName = fileName.replace(/\.[^.]+$/, '') || 'benchmark'
    const md = generateMarkdownReport({
      fileName, vlmResult, ocrLlmResult, vlmTimeMs, ocrLlmTimeMs,
      vlmInputTokens, vlmOutputTokens, ocrInputTokens, ocrOutputTokens,
      masterXml: masterXmlContent,
      vlmXml,
      ocrXml,
      masterScore,
    })
    downloadFile(md, `${baseName}_benchmark.md`, 'text/markdown')
  }

  const hasResults = vlmResult || ocrLlmResult

  const speedRatio =
    vlmTimeMs > 0 && ocrLlmTimeMs > 0
      ? (ocrLlmTimeMs / vlmTimeMs).toFixed(1)
      : null

  const vlmTotalTokens = vlmInputTokens + vlmOutputTokens
  const ocrTotalTokens = ocrInputTokens + ocrOutputTokens

  const speedWinner = (() => {
    if (!(vlmTimeMs > 0 && ocrLlmTimeMs > 0)) return '--'
    if (vlmTimeMs === ocrLlmTimeMs) return 'Tie'
    if (vlmTimeMs < ocrLlmTimeMs) {
      return `VLM ${(ocrLlmTimeMs / vlmTimeMs).toFixed(1)}x faster`
    }
    return `OCR ${(vlmTimeMs / ocrLlmTimeMs).toFixed(1)}x faster`
  })()

  const tokenWinner = (() => {
    if (!(vlmTotalTokens > 0 && ocrTotalTokens > 0)) return '--'
    if (vlmTotalTokens === ocrTotalTokens) return 'Tie'
    if (vlmTotalTokens < ocrTotalTokens) {
      return `VLM ${(ocrTotalTokens / vlmTotalTokens).toFixed(1)}x fewer tokens`
    }
    return `OCR ${(vlmTotalTokens / ocrTotalTokens).toFixed(1)}x fewer tokens`
  })()

  const qualityWinner = (() => {
    const v = masterScore?.vlm
    const o = masterScore?.ocr_llm
    if (!v || !o) return 'Upload Master XML to score quality'
    if (v.accuracy_pct === o.accuracy_pct) return `Tie at ${v.accuracy_pct}%`
    if (v.accuracy_pct > o.accuracy_pct) {
      return `VLM best (${v.accuracy_pct}% vs ${o.accuracy_pct}%)`
    }
    return `OCR best (${o.accuracy_pct}% vs ${v.accuracy_pct}%)`
  })()

  return (
    <div className="app-root">
      {/* Header */}
      <header className="app-header">
        <div className="brand">
          <div className="brand-mark">VLM vs OCR+LLM</div>
          <div className="brand-sub">Structured Data Extraction Benchmark</div>
        </div>
        {hasResults && (
          <div className="header-actions">
            <nav className="view-toggle">
              <button
                className={activeView === 'side-by-side' ? 'active' : ''}
                onClick={() => setActiveView('side-by-side')}
              >
                Side by Side
              </button>
              <button
                className={activeView === 'diff' ? 'active' : ''}
                onClick={() => setActiveView('diff')}
              >
                Diff View
              </button>
            </nav>
            <div className="download-btns">
              <input
                ref={masterXmlInputRef}
                type="file"
                accept="application/xml,text/xml,.xml"
                onChange={handleMasterXmlPicked}
                hidden
              />
              <button
                className="btn-download"
                onClick={() => masterXmlInputRef.current?.click()}
                title="Upload master XML and compare with extracted XML outputs"
              >
                Master XML Compare
              </button>
              <button className="btn-download" onClick={handleDownloadHtml} title="Download as HTML report">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                HTML
              </button>
              <button className="btn-download" onClick={handleDownloadMarkdown} title="Download as Markdown for GitHub">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                MD
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Summary bar */}
      {hasResults && (
        <div className="summary-bar">
          <div className="summary-card">
            <span className="summary-label">Best Extraction Quality</span>
            <span className="summary-value faster">{qualityWinner}</span>
          </div>
          <div className="summary-card">
            <span className="summary-label">Speed Winner</span>
            <span className="summary-value faster">{speedWinner}</span>
          </div>
          <div className="summary-card">
            <span className="summary-label">Token Efficiency</span>
            <span className="summary-value faster">{tokenWinner}</span>
          </div>
          <div className="summary-card">
            <div className="summary-left">
              <span className="summary-label">VLM (Vision)</span>
              <span className="token-info">In: {vlmInputTokens.toLocaleString()} | Out: {vlmOutputTokens.toLocaleString()}</span>
            </div>
            <span className="summary-value vlm">
              {(vlmTimeMs / 1000).toFixed(1)}
              <span className="summary-unit">s</span>
            </span>
          </div>
          <div className="summary-card">
            <div className="summary-left">
              <span className="summary-label">OCR + LLM</span>
              <span className="token-info">In: {ocrInputTokens.toLocaleString()} | Out: {ocrOutputTokens.toLocaleString()}</span>
            </div>
            <span className="summary-value ocr">
              {(ocrLlmTimeMs / 1000).toFixed(1)}
              <span className="summary-unit">s</span>
            </span>
          </div>
          <div className="summary-card">
            <span className="summary-label">Speed Comparison</span>
            <span className="summary-value faster">
              {speedWinner}
            </span>
          </div>
          {masterScore?.vlm && (
            <div className="summary-card">
              <span className="summary-label">VLM vs Master XML</span>
              <span className="summary-value vlm">
                {masterScore.vlm.correct} correct / {masterScore.vlm.wrong} wrong
              </span>
              <span className="token-info">Accuracy: {masterScore.vlm.accuracy_pct}%</span>
            </div>
          )}
          {masterScore?.ocr_llm && (
            <div className="summary-card">
              <span className="summary-label">OCR+LLM vs Master XML</span>
              <span className="summary-value ocr">
                {masterScore.ocr_llm.correct} correct / {masterScore.ocr_llm.wrong} wrong
              </span>
              <span className="token-info">Accuracy: {masterScore.ocr_llm.accuracy_pct}%</span>
            </div>
          )}
        </div>
      )}

      {/* Main content area */}
      <main className="main-content">
        {!hasResults && !isProcessing && !error && (
          <UploadZone onUpload={handleUpload} />
        )}

        {!hasResults && !isProcessing && error && (
          <div className="loading-overlay">
            <div className="error-card">
              <div className="error-icon">!</div>
              <p className="error-title">Benchmark Failed</p>
              <p className="error-detail">{error}</p>
              <button className="btn-retry" onClick={handleReset}>
                Try Again
              </button>
            </div>
          </div>
        )}

        {isProcessing && (
          <div className="loading-overlay">
            <div className="spinner" />
            <p className="loading-text">Running benchmark...</p>
            <p className="loading-sub">
              Extracting with VLM and OCR+LLM concurrently
            </p>
          </div>
        )}

        {hasResults && activeView === 'side-by-side' && (
          <div className={`split ${masterXmlContent ? 'split-three' : ''}`}>
            {masterXmlContent && (
              <ResultPanel
                title="Master XML"
                xmlOutput={masterXmlContent}
                variant="master"
                showMetrics={false}
              />
            )}
            <ResultPanel
              title="VLM (Vision)"
              result={vlmResult}
              xmlOutput={vlmXml}
              timeMs={vlmTimeMs}
              error={vlmError}
              variant="vlm"
              compareWith={null}
              inputTokens={vlmInputTokens}
              outputTokens={vlmOutputTokens}
            />
            <ResultPanel
              title="OCR + LLM"
              result={ocrLlmResult}
              xmlOutput={ocrXml}
              timeMs={ocrLlmTimeMs}
              error={ocrError}
              ocrText={ocrRawText}
              variant="ocr"
              compareWith={null}
              inputTokens={ocrInputTokens}
              outputTokens={ocrOutputTokens}
            />
          </div>
        )}

        {hasResults && activeView === 'diff' && (
          <DiffView masterXml={masterXmlContent} vlmXml={vlmXml} ocrXml={ocrXml} />
        )}
      </main>

      {error && <div className="error-bar">{error}</div>}

      <footer className="app-footer">
        <span className="muted">
          {fileName
            ? `File: ${fileName}${masterXmlName ? ` | Master XML: ${masterXmlName}` : ''}`
            : 'gemini-2.5-flash | Both paths use identical schema & prompts'}
        </span>
        {hasResults && (
          <button className="btn-reset" onClick={handleReset}>
            New Benchmark
          </button>
        )}
      </footer>
    </div>
  )
}

export default App
