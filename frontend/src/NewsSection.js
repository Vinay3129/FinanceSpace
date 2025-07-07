import { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function NewsSection({ theme }) {
  const [newsCategory, setNewsCategory] = useState('business');
  const [newsRegion, setNewsRegion] = useState('global');
  const [newsArticles, setNewsArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Categories based on theme
  const categories = theme === 'finance' 
    ? ['business', 'economy', 'markets', 'cryptocurrency'] 
    : ['science', 'technology', 'astronomy', 'space'];

  // Regions
  const regions = [
    { id: 'global', name: 'Global' },
    { id: 'us', name: 'United States' },
    { id: 'eu', name: 'Europe' },
    { id: 'asia', name: 'Asia' },
    { id: 'in', name: 'India' }
  ];

  useEffect(() => {
    // Set default category based on theme
    if (theme === 'finance') {
      setNewsCategory('business');
    } else {
      setNewsCategory('science');
    }
    
    // Load news on theme or category change
    loadNews();
  }, [theme, newsCategory, newsRegion]);

  const loadNews = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`${API}/news`, {
        params: {
          category: newsCategory,
          region: newsRegion !== 'global' ? newsRegion : null
        }
      });
      
      setNewsArticles(response.data.articles);
    } catch (err) {
      console.error('Error loading news:', err);
      setError('Failed to load news. Please try again later.');
      setNewsArticles([]);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="news-section">
      <div className="news-header">
        <h2>Latest {theme === 'finance' ? 'Financial' : 'Space'} News</h2>
        
        <div className="news-filters">
          <div className="category-filters">
            {categories.map(category => (
              <button
                key={category}
                className={`filter-btn ${newsCategory === category ? 'active' : ''}`}
                onClick={() => setNewsCategory(category)}
              >
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </button>
            ))}
          </div>
          
          <div className="region-selector">
            <select 
              value={newsRegion}
              onChange={(e) => setNewsRegion(e.target.value)}
              className="region-select"
            >
              {regions.map(region => (
                <option key={region.id} value={region.id}>
                  {region.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
      
      <div className="news-content">
        {loading ? (
          <div className="loading-card">
            <div className="loading-spinner"></div>
            <p>Loading news...</p>
          </div>
        ) : error ? (
          <div className="error-card">
            <h3>Error</h3>
            <p>{error}</p>
          </div>
        ) : newsArticles.length === 0 ? (
          <div className="empty-state">
            <p>No news articles found. Try a different category or region.</p>
          </div>
        ) : (
          <div className="news-grid">
            {newsArticles.map((article, index) => (
              <div key={index} className="news-card">
                {article.image_url && (
                  <div className="news-image">
                    <img src={article.image_url} alt={article.title} />
                  </div>
                )}
                <div className="news-content">
                  <h3>
                    <a href={article.url} target="_blank" rel="noopener noreferrer">
                      {article.title}
                    </a>
                  </h3>
                  {article.description && (
                    <p className="news-description">{article.description}</p>
                  )}
                  <div className="news-meta">
                    <span className="news-source">{article.source}</span>
                    {article.published_at && (
                      <span className="news-date">{formatDate(article.published_at)}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default NewsSection;