# PriceTrackr - Price Tracking System

## Project Overview
A complete zero-cost price tracking system that monitors and compares product prices across multiple e-commerce platforms. Built with FastAPI backend, React frontend, Playwright scrapers, and PostgreSQL database.

## Tech Stack
- **Frontend**: React + Vite + Tailwind CSS (Port 5000)
- **Backend**: FastAPI + PostgreSQL + Redis (Port 8000)
- **Worker**: Playwright + BeautifulSoup scrapers
- **Infrastructure**: Docker Compose ready

## Project Structure
- `/backend` - FastAPI backend with API endpoints, models, and database
- `/frontend` - React SPA with Vite and Tailwind
- `/worker` - Playwright-based web scrapers
- `/infra` - Docker Compose and deployment configs
- `/extension` - Browser extension (future)

## Current Status
- ✅ Backend API structure complete
- ✅ Frontend React app complete with all pages
- ✅ Scraper workers implemented
- ✅ Docker infrastructure ready
- ✅ VS Code workspace configured

## Pages Implemented
1. Dashboard - Overview with stats and recent activity
2. Watchlist - Tracked products and price alerts
3. Add Product - Add new products to track
4. Sales - Ongoing and upcoming sales
5. Settings - App configuration with dark mode

## Features
- Price tracking across multiple e-commerce sites
- Historical price charts and analysis
- Watchlist with custom alerts
- Scam detection and trust scoring
- Sales and deals awareness
- Dark mode support
- Progressive Web App capabilities

## Development
- Frontend runs on port 5000
- Backend API on port 8000
- VS Code workspace: `price-trackr.code-workspace`
- All dependencies managed via npm/pip

## User Preferences
- VS Code friendly setup with workspace configuration
- Clean, minimalist UI design matching provided screenshots
- Light and dark theme support
- No changes to design unless for betterment of UI/vibe
