# 🦷 OralHealth - Evidence-Based Oral Health Recommendations

[![Django](https://img.shields.io/badge/Django-4.2.7-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Xera DB](https://img.shields.io/badge/Part%20of-Xera%20DB-purple.svg)](https://xeradb.com)

## 🌟 Overview

**OralHealth** is a comprehensive web application that provides evidence-based oral health recommendations from leading international guidelines. As part of the **Xera DB ecosystem**, it follows the same professional design patterns and robust architecture while focusing specifically on oral health evidence.

### 🚀 Key Features

- **🌍 Multi-Country Coverage**: UK, US, Canada, Australia, and New Zealand guidelines
- **📊 GRADE Evidence Assessment**: All recommendations include evidence quality ratings
- **🔍 Advanced Search**: Filter by country, topic, strength, and evidence quality
- **🧪 Cochrane Integration**: Summary of Findings tables from Cochrane Oral Health reviews
- **🌐 Multi-Language Support**: Real-time translation to 30+ languages
- **🎨 Professional UI**: Consistent with Xera DB design system
- **⚡ REST API**: Programmatic access to all data
- **📱 Responsive Design**: Mobile-friendly interface

## 🏗️ Architecture

### Database Schema
```
Country → Organization → Guideline → Chapter → Recommendation
                                              ↓
                                    RecommendationReference
Topic ←------- Recommendation
RecommendationStrength ←------- Recommendation
EvidenceQuality ←------- Recommendation

CochraneReview → CochraneSoFEntry
```

### Key Models
- **Recommendation**: Core evidence-based recommendations
- **Guideline**: Source guidelines from different countries
- **Topic**: Categorization system (e.g., Fluoride, Oral Hygiene)
- **CochraneSoFEntry**: Summary of Findings from systematic reviews

## 🔧 Technical Stack

- **Backend**: Django 4.2.7, Django REST Framework
- **Database**: PostgreSQL 13+
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5
- **Translation**: Google Translate API + LibreTranslate (fallback)
- **Caching**: Django Cache Framework
- **Deployment**: Gunicorn, Nginx, Supervisor
- **Design**: Xera DB Unified Theme System

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 13+
- pip
- virtualenv (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/choxos/oralhealth.git
   cd oralhealth
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database and translation**
   ```bash
   # Create PostgreSQL database
   createdb oralhealth_dev
   
   # Create .env file
   cp .env.example .env
   # Edit .env with your database credentials and translation settings
   
   # Optional: Add Google Translate API key for enhanced translation
   # Or use the free LibreTranslate service (default)
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Web Interface: http://localhost:8000
   - Admin Panel: http://localhost:8000/admin
   - API Documentation: http://localhost:8000/api

## 📊 Data Population

### UK Guidelines
```bash
# Populate UK "Delivering better oral health" guidelines
python manage.py populate_uk_guidelines
```

### Cochrane Reviews
```bash
# Import Cochrane Summary of Findings data
python manage.py import_cochrane_sof ~/Documents/Github/CoE-Cochrane/validated/SoF
```

### Future Guidelines
- US: ADA guidelines, CDC recommendations
- Canada: Canadian Dental Association guidelines
- Australia: NHMRC oral health guidelines
- New Zealand: Ministry of Health oral health guidelines

## 🔍 API Documentation

### Core Endpoints

- `GET /api/recommendations/` - List all recommendations
- `GET /api/recommendations/{id}/` - Get specific recommendation
- `GET /api/guidelines/` - List all guidelines
- `GET /api/topics/` - List all topics
- `GET /api/countries/` - List all countries
- `GET /api/search/?q=query` - Search recommendations
- `GET /api/translate/?text=...&target=es` - Translate text
- `GET /api/stats/` - Get database statistics

### Translation API

The translation API supports real-time text translation:

```bash
curl "https://oralhealth.xeradb.com/api/translate/?text=Brush%20teeth%20twice%20daily&target=es&source=en"
```

**Supported Languages:** Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi, Turkish, Dutch, Swedish, Danish, Norwegian, Finnish, Polish, Czech, Hungarian, Romanian, Greek, Hebrew, Thai, Vietnamese, Indonesian, Malay, Ukrainian, Bulgarian, Croatian, Slovak, Slovenian, Lithuanian, Latvian, Estonian

### Example API Call

```bash
curl "https://oralhealth.xeradb.com/api/recommendations/?country=UK&topic=fluoride"
```

### Response Format

```json
{
  "count": 150,
  "next": "https://oralhealth.xeradb.com/api/recommendations/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Fluoride Toothpaste Recommendation",
      "text": "Use fluoride toothpaste with 1000-1500 ppm fluoride twice daily",
      "strength": "strong",
      "evidence_quality": "high",
      "guideline": {
        "title": "Delivering better oral health",
        "country": "UK",
        "organization": "Public Health England"
      },
      "topics": ["Fluoride", "Oral Hygiene"],
      "created_at": "2023-11-20T10:00:00Z"
    }
  ]
}
```

## 🌍 Translation Feature

### Supported Translation Providers
1. **Google Translate API** (Primary) - High accuracy, requires API key
2. **LibreTranslate** (Fallback) - Free, open-source alternative

### Setup Translation
```bash
# For enhanced translation (optional)
export GOOGLE_TRANSLATE_API_KEY="your-api-key"

# Free alternative (default)
export LIBRETRANSLATE_URL="https://libretranslate.de"
```

### Usage
- Click the translation widget in the top-right corner
- Select your preferred language
- Content translates in real-time
- Language preference saved in URL

## 🐳 Deployment

### Production Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for complete VPS deployment instructions.

### Quick Docker Setup
```bash
# Build and run with Docker Compose
docker-compose up -d

# Access at http://localhost:8000
```

### Environment Variables
```bash
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@localhost:5432/oralhealth_production
ALLOWED_HOSTS=oralhealth.xeradb.com,www.oralhealth.xeradb.com
GOOGLE_TRANSLATE_API_KEY=your-google-translate-api-key
```

## 📁 Project Structure

```
oralhealth/
├── guidelines/          # UK guidelines app
├── cochrane/           # Cochrane reviews app
├── search/             # Search functionality
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
├── oralhealth/         # Main project settings
├── requirements.txt    # Python dependencies
├── manage.py          # Django management script
├── DEPLOYMENT.md      # Deployment guide
└── README.md          # This file
```

## 🔒 Security Features

- **CSRF Protection**: Django CSRF middleware
- **SQL Injection Protection**: Django ORM
- **XSS Protection**: Template auto-escaping
- **Secure Headers**: Security middleware
- **SSL/HTTPS**: Let's Encrypt integration
- **Input Validation**: Form validation and sanitization

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test guidelines

# Coverage report
coverage run --source='.' manage.py test
coverage report
```

## 📈 Performance

- **Database Optimization**: Optimized queries with select_related/prefetch_related
- **Caching**: 7-day translation cache, template fragment caching
- **Static Files**: WhiteNoise for production static file serving
- **CDN Ready**: Static files optimized for CDN deployment
- **Database Indexing**: Strategic indexes on frequently queried fields

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation for API changes
- Use meaningful commit messages

## 📋 Roadmap

### Phase 1 (Current)
- ✅ UK guidelines integration
- ✅ Cochrane SoF data integration
- ✅ Multi-language translation
- ✅ REST API
- ✅ Search functionality

### Phase 2 (Next)
- [ ] US (ADA/CDC) guidelines
- [ ] Canadian guidelines
- [ ] Australian guidelines
- [ ] New Zealand guidelines
- [ ] User accounts and favorites
- [ ] Advanced analytics

### Phase 3 (Future)
- [ ] Mobile application
- [ ] Clinical decision support
- [ ] Practice integration APIs
- [ ] Continuing education modules

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Dr. Ahmad Sofi-Mahmudi**
- Meta-researcher in Open Science
- Email: ahmad.pub@gmail.com
- Google Scholar: [Profile](https://scholar.google.com/citations?user=gTWPaFYAAAAJ&hl=en)
- LinkedIn: [asofimahmudi](https://linkedin.com/in/asofimahmudi)
- X: [@ASofiMahmudi](https://x.com/ASofiMahmudi)

## 🙏 Acknowledgments

- **UK Department of Health**: For "Delivering better oral health" guidelines
- **Cochrane Oral Health**: For systematic review data
- **Xera DB Community**: For shared theme and architecture patterns
- **Django Community**: For the excellent web framework
- **Open Source Contributors**: For translation services and tools

## 🔗 Links

- **Live Application**: [oralhealth.xeradb.com](https://oralhealth.xeradb.com)
- **API Documentation**: [oralhealth.xeradb.com/api](https://oralhealth.xeradb.com/api)
- **Xera DB Ecosystem**: [xeradb.com](https://xeradb.com)
- **GitHub Repository**: [github.com/choxos/oralhealth](https://github.com/choxos/oralhealth)

---

**Part of the Xera DB Ecosystem** - Advancing Open Science Through Data 🔬✨