import { useState } from 'react'
import axios from 'axios'
import './App.css'

const API_BASE = 'http://localhost:8000/api'

function App() {
  const [folderPath, setFolderPath] = useState('C:\\\\')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSort = async (dryRun = true) => {
    setLoading(true)
    try {
      const res = await axios.post(`${API_BASE}/sort`, {
        folder_path: folderPath,
        dry_run: dryRun
      })
      setResults(res.data)
    } catch (err) {
      console.error(err)
      alert('Error connecting to backend')
    }
    setLoading(false)
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>SmartSort</h1>
        <p>Organize your files intelligently.</p>
      </header>

      <main className="glass-panel main-panel">
        <div className="input-group">
          <label>Target Directory</label>
          <input 
            type="text" 
            className="input-field" 
            value={folderPath} 
            onChange={(e) => setFolderPath(e.target.value)} 
          />
        </div>

        <div className="action-buttons">
          <button className="btn" onClick={() => handleSort(true)} disabled={loading}>
            {loading ? 'Simulating...' : 'Dry Run (Simulate)'}
          </button>
          <button className="btn btn-danger" onClick={() => handleSort(false)} disabled={loading}>
            {loading ? 'Sorting...' : 'Organize Files'}
          </button>
        </div>

        {results && (
          <div className="results-panel">
            <h2>Sort Summary</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <h3>{results.summary.moved}</h3>
                <p>Moved</p>
              </div>
              <div className="stat-card">
                <h3>{results.summary.duplicate}</h3>
                <p>Duplicates</p>
              </div>
              <div className="stat-card">
                <h3>{results.summary.error}</h3>
                <p>Errors</p>
              </div>
              <div className="stat-card">
                <h3>{results.summary.total}</h3>
                <p>Total</p>
              </div>
            </div>

            <div className="file-list glass-panel">
              <h3>File Details</h3>
              <ul>
                {results.results.map((file, i) => (
                  <li key={i}>
                    <strong>{file.filename}</strong>: {file.status} 
                    {file.destination ? ` -> ${file.destination}` : ''}
                    {file.reason ? ` (${file.reason})` : ''}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
