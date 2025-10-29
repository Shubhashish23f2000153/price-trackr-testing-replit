# 🏷️ PriceTrackr - Zero-Cost Price Tracking System

A self-hosted, open-source global price tracker that monitors and compares product prices across multiple e-commerce platforms. Built with zero paid dependencies and designed for VPS deployment.

## ✨ Features

- 📊 **Real-time Price Tracking** - Monitor prices across Amazon, Flipkart, and more
- 📈 **Historical Price Charts** - Visualize price trends over time
- 🔔 **Smart Alerts** - Get notified when prices drop below your threshold
- 🛡️ **Scam Detection** - Built-in trust scoring for e-commerce sites
- 🎯 **Sale Awareness** - Track ongoing and upcoming sales
- 🌓 **Dark Mode** - Beautiful UI with light/dark theme support
- 📱 **Progressive Web App** - Works offline with service worker
- 🔌 **Browser Extension** - Quick price checks while browsing

## 🏗️ Architecture

### Tech Stack

- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Scraper**: Playwright + BeautifulSoup
- **Deployment**: Docker Compose
- **Proxy**: Nginx

### Directory Structure

```
price-trackr/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── crud/        # Database operations
│   │   └── utils/       # Utilities
│   └── Dockerfile
├── worker/              # Scraper workers
│   └── playwright_scraper/
│       └── scrapers/    # Site-specific scrapers
├── frontend/            # React frontend
│   └── src/
│       ├── pages/       # Page components
│       └── components/  # Reusable components
├── extension/           # Browser extension
├── infra/              # Infrastructure
│   └── docker-compose.yml
└── docs/               # Documentation
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd price-trackr
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run with Docker Compose**
   ```bash
   cd infra
   docker compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:5000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

#### Worker
```bash
cd worker
pip install -r requirements.txt
playwright install chromium
python playwright_scraper/runner.py
```

## 📖 API Endpoints

### Products
- `POST /api/products/track` - Add product to track
- `GET /api/products/{id}` - Get product details
- `GET /api/products/{id}/history` - Get price history

### Watchlist
- `POST /api/watchlist/` - Add to watchlist
- `GET /api/watchlist/` - Get watchlist
- `DELETE /api/watchlist/{id}` - Remove from watchlist

### Sales
- `GET /api/sales/` - Get active sales
- `POST /api/sales/` - Create sale entry

### Scam Check
- `GET /api/scam/check?domain=example.com` - Check domain trust score

## 🔧 Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:testpassword@postgres:5432/pricetrackr

# Redis
REDIS_URL=redis://redis:6379/0

# API
CORS_ORIGINS=http://localhost:5000,http://localhost:3000

# Scraper
USER_AGENT=Mozilla/5.0...
SCRAPER_DELAY_MIN=2
SCRAPER_DELAY_MAX=5
```

## 🎨 VS Code Setup

Open the workspace file for optimal development experience:

```bash
code price-trackr.code-workspace
```

The workspace includes:
- Multi-root folder structure
- Recommended extensions
- Pre-configured debug configurations
- Format on save settings

## 🚢 Deployment

### VPS Deployment

1. **Provision a VPS**
   - Minimum: 2vCPU, 4GB RAM, 50GB SSD
   - Ubuntu 20.04 LTS or newer

2. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```

3. **Clone and configure**
   ```bash
   git clone <repo-url> /opt/price-trackr
   cd /opt/price-trackr
   cp .env.example .env
   # Edit .env
   ```

4. **Start services**
   ```bash
   cd infra
   docker compose up -d
   ```

5. **Set up systemd service** (optional)
   ```bash
   sudo cp infra/systemd/price-trackr.service /etc/systemd/system/
   sudo systemctl enable price-trackr
   sudo systemctl start price-trackr
   ```

### SSL with Certbot

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📝 Adding New Scrapers

1. Create a new scraper file in `worker/playwright_scraper/scrapers/`
2. Extend the `BaseScraper` class
3. Implement `extract_data()` and `extract_data_fallback()` methods
4. Register in `scrapers/__init__.py`

Example:
```python
from ..base_scraper import BaseScraper

class NewSiteScraper(BaseScraper):
    def extract_data(self, page):
        # Implement extraction logic
        pass
```

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

This project is open-source and available under the MIT License.

## ⚠️ Disclaimer

This tool collects publicly available price information for comparison purposes only. Always verify prices on the actual e-commerce site before making purchases. This application does not store payment information or handle transactions.

## 🙏 Acknowledgments

- Built with open-source technologies
- Zero paid APIs or services
- Community-driven development

---

**Made with ❤️ for the open-source community**
