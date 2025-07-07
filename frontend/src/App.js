import { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import NewsSection from "./NewsSection";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentTheme, setCurrentTheme] = useState('finance');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [activeFilter, setActiveFilter] = useState('all');

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const response = await axios.get(`${API}/history`);
      setHistory(response.data);
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  const handleThemeSwitch = (theme) => {
    setCurrentTheme(theme);
    setResults(null);
    setActiveFilter('all');
  };

  const handleSearch = async (type = 'combined') => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/${type}`, {
        query: query,
        type: type
      });
      setResults(response.data);
      await loadHistory();
    } catch (error) {
      console.error('Error processing query:', error);
      setResults({
        error: 'Failed to process query. Please try again.',
        query: query
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const getThemeData = () => {
    if (currentTheme === 'finance') {
      return {
        title: 'Finance',
        subtitle: 'AI-Powered Financial Research',
        heroImage: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwxfHxmaW5hbmNpYWwlMjBkYXNoYm9hcmR8ZW58MHx8fHwxNzUxODgwMTg4fDA&ixlib=rb-4.1.0&q=85',
        filters: ['News', 'Stocks', 'Wealth', 'Budgets'],
        sampleQueries: [
          'What is the current state of the stock market?',
          'Explain cryptocurrency trends in 2024',
          'How to build a diversified investment portfolio?'
        ]
      };
    } else {
      return {
        title: 'Space',
        subtitle: 'AI-Powered Space Research',
        heroImage: 'https://images.unsplash.com/photo-1484931575886-a5f4df44d5b7?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHwxfHxzcGFjZSUyMGFzdHJvbm9teXxlbnwwfHx8fDE3NTE4ODAxOTJ8MA&ixlib=rb-4.1.0&q=85',
        filters: ['Astronomy', 'Stars', 'Galaxies', 'Developments'],
        sampleQueries: [
          'What are the latest discoveries from James Webb telescope?',
          'Explain black holes and their formation',
          'Recent developments in Mars exploration'
        ]
      };
    }
  };

  const themeData = getThemeData();

  return (
    <div className={`app ${currentTheme}`}>
      {/* Header */}
      <header className="header">
        <div className="container">
          <div className="header-content">
            <div className="logo">
              <span 
                className={`logo-part ${currentTheme === 'finance' ? 'active' : ''}`}
                onClick={() => handleThemeSwitch('finance')}
              >
                Finance
              </span>
              <span 
                className={`logo-part ${currentTheme === 'space' ? 'active' : ''}`}
                onClick={() => handleThemeSwitch('space')}
              >
                Space
              </span>
            </div>
            <div className="search-container">
              <input
                type="text"
                placeholder={`Search ${themeData.title} topics...`}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="search-input"
              />
              <button 
                onClick={() => handleSearch('combined')}
                disabled={loading}
                className="search-button"
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero" style={{ backgroundImage: `url(${themeData.heroImage})` }}>
        <div className="hero-overlay">
          <div className="container">
            <div className="hero-content">
              <h1 className="hero-title">{themeData.title}Space</h1>
              <p className="hero-subtitle">{themeData.subtitle}</p>
              <div className="hero-actions">
                <button 
                  onClick={() => handleSearch('combined')}
                  disabled={loading || !query.trim()}
                  className="btn-primary"
                >
                  AI Research
                </button>
                <button 
                  onClick={() => handleSearch('search')}
                  disabled={loading || !query.trim()}
                  className="btn-secondary"
                >
                  Web Search
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Filters */}
      <section className="filters">
        <div className="container">
          <div className="filter-buttons">
            <button 
              className={`filter-btn ${activeFilter === 'all' ? 'active' : ''}`}
              onClick={() => setActiveFilter('all')}
            >
              All
            </button>
            {themeData.filters.map(filter => (
              <button 
                key={filter}
                className={`filter-btn ${activeFilter === filter ? 'active' : ''}`}
                onClick={() => setActiveFilter(filter)}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main className="main-content">
        <div className="container">
          <div className="content-grid">
            {/* Results Section */}
            <div className="results-section">
              {loading && (
                <div className="loading-card">
                  <div className="loading-spinner"></div>
                  <p>Processing your query...</p>
                </div>
              )}

              {results && !loading && (
                <div className="results-container">
                  {results.error ? (
                    <div className="error-card">
                      <h3>Error</h3>
                      <p>{results.error}</p>
                    </div>
                  ) : (
                    <>
                      {results.ai_summary && (
                        <div className="ai-summary-card">
                          <h3>AI Summary</h3>
                          <p>{results.ai_summary}</p>
                        </div>
                      )}
                      
                      {results.response && (
                        <div className="ai-response-card">
                          <h3>AI Response</h3>
                          <p>{results.response}</p>
                        </div>
                      )}

                      {results.search_results && results.search_results.length > 0 && (
                        <div className="search-results">
                          <h3>Related Information</h3>
                          <div className="search-grid">
                            {results.search_results.map((result, index) => (
                              <div key={index} className="search-result-card">
                                <h4>{result.title}</h4>
                                <p>{result.snippet}</p>
                                <a href={result.url} target="_blank" rel="noopener noreferrer">
                                  Read more →
                                </a>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {results.results && results.results.length > 0 && (
                        <div className="search-results">
                          <h3>Search Results</h3>
                          <div className="search-grid">
                            {results.results.map((result, index) => (
                              <div key={index} className="search-result-card">
                                <h4>{result.title}</h4>
                                <p>{result.snippet}</p>
                                <a href={result.url} target="_blank" rel="noopener noreferrer">
                                  Read more →
                                </a>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              {!results && !loading && (
                <div className="sample-queries">
                  <h3>Try these sample queries:</h3>
                  <div className="sample-grid">
                    {themeData.sampleQueries.map((sample, index) => (
                      <div 
                        key={index}
                        className="sample-card"
                        onClick={() => {
                          setQuery(sample);
                          handleSearch('combined');
                        }}
                      >
                        <p>{sample}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div className="sidebar">
              <div className="sidebar-section">
                <h3>Recent Queries</h3>
                <div className="history-list">
                  {history.slice(0, 5).map((item, index) => (
                    <div key={index} className="history-item">
                      <p className="history-query">{item.query}</p>
                      <span className="history-type">{item.type}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="sidebar-section">
                <h3>Quick Actions</h3>
                <div className="quick-actions">
                  <button 
                    onClick={() => handleSearch('query')}
                    disabled={loading || !query.trim()}
                    className="quick-btn"
                  >
                    AI Only
                  </button>
                  <button 
                    onClick={() => handleSearch('search')}
                    disabled={loading || !query.trim()}
                    className="quick-btn"
                  >
                    Search Only
                  </button>
                  <button 
                    onClick={() => handleSearch('combined')}
                    disabled={loading || !query.trim()}
                    className="quick-btn"
                  >
                    Combined
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <p>&copy; 2024 FinanceSpace. AI-powered research platform.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;