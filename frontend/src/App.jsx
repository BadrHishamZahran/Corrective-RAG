import { useState } from 'react'
const API = 'http://127.0.0.1:8000'
export default function App() {
  const [file, setFile] = useState(null), [question, setQuestion] = useState(''), [messages, setMessages] = useState([]), [busy, setBusy] = useState(false), [notice, setNotice] = useState('')
  async function upload() {
    if (!file) return
    setBusy(true); setNotice('Uploading and indexing document...')
    try { const data = new FormData(); data.append('file', file); const res = await fetch(`${API}/upload`, { method: 'POST', body: data }); const json = await res.json(); if (!res.ok) throw new Error(json.detail || 'Upload failed'); setNotice(`${json.filename}: ${json.chunks_added} chunks indexed successfully.`); setFile(null) }
    catch (e) { setNotice(e.message) } finally { setBusy(false) }
  }
  async function ask(e) {
    e.preventDefault(); if (!question.trim()) return
    const q = question.trim(); setQuestion(''); setMessages(m => [...m, { role: 'user', text: q }]); setBusy(true)
    try { const res = await fetch(`${API}/ask`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q }) }); const json = await res.json(); if (!res.ok) throw new Error(json.detail || 'Request failed'); setMessages(m => [...m, { role: 'assistant', ...json }]) }
    catch (e) { setMessages(m => [...m, { role: 'assistant', answer: e.message, sources: [] }]) } finally { setBusy(false) }
  }
  return <main className="shell">
    <header><h1>Corrective RAG</h1><p className="subtitle">Ask questions about your course documents. Retrieval is evaluated and corrected when needed.</p></header>
    <section className="panel upload"><div><h2>Knowledge base</h2><p>Upload PDF, DOCX, or TXT documents.</p></div><div className="upload-controls"><input type="file" accept=".pdf,.docx,.txt" onChange={e => setFile(e.target.files?.[0] || null)} /><button onClick={upload} disabled={!file || busy}>Upload document</button></div>{notice && <p className="notice">{notice}</p>}</section>
    <section className="panel chat"><h2>Ask your course assistant</h2><div className="conversation">{messages.length === 0 && <div className="empty">Your questions and answers will appear here.</div>}{messages.map((m, i) => <article className={`message ${m.role}`} key={i}><div className="role">{m.role === 'user' ? 'YOU' : 'ASSISTANT'}</div><p>{m.role === 'user' ? m.text : m.answer}</p>{m.role === 'assistant' && m.retrieval_status && <div className="meta">Retrieval: {m.retrieval_status} · Score: {m.retrieval_score}{m.corrected_query && <span> · Corrected query: {m.corrected_query}</span>}</div>}{m.role === 'assistant' && m.sources?.length > 0 && <div className="sources"><strong>Sources</strong>{m.sources.map((s, j) => <div key={j}>{s.filename}{s.page ? ` · Page ${s.page}` : ''}</div>)}</div>}</article>)}</div><form onSubmit={ask}><input value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ask a question about your documents..." /><button disabled={busy || !question.trim()}>Send</button></form>{busy && <p className="working">Processing locally. This may take a little time.</p>}</section>
    <footer>Runs locally with Ollama · Qwen2.5 3B · ChromaDB</footer>
  </main>
}
