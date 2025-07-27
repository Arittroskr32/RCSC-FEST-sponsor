<<<<<<< HEAD
# Fest Sponsor Management Application

A comprehensive web application for managing event sponsors, partners, vendors, and participants. Built with Python Flask backend and modern HTML/CSS frontend, with MongoDB Atlas for cloud database storage.

## Features

### 🔐 Admin Authentication
- Secure login system for admin users
- Session management
- Default credentials: `admin` / `admin123` (change in production)

### 👥 Entity Management
The application provides CRUD operations for four main entity types:

#### 1. **Sponsors** 🤝
- Search existing sponsors by name, email, or company
- Add new sponsors with contact details and sponsorship amounts
- View all sponsors with creation timestamps
- Track total sponsor count

#### 2. **Partners** 🤝
- Manage strategic, media, technology, and community partners
- Track partnership types and relationships
- Full search and management capabilities

#### 3. **Vendors** 🏪
- Organize vendor information by service type
- Track cost estimates for different services
- Manage catering, decoration, sound, lighting, photography, security, and transportation vendors

#### 4. **Participants** 👨‍👩‍👧‍👦
- Register students, professionals, volunteers, speakers, judges, and organizers
- Track registration fees and participant organizations
- Comprehensive participant management

### 📊 Dashboard
- Real-time statistics for all entity types
- Quick action buttons for easy navigation
- Clean, intuitive interface

### 🔍 Advanced Search
- Real-time search across all entity types
- Search by name, email, company, or organization
- Instant results display

### 🌐 Cloud Integration
- MongoDB Atlas integration for cloud database
- Multi-user support (perfect for your 4 friends!)
- Scalable architecture

## Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: MongoDB Atlas (Cloud)
- **Deployment**: GitHub + Heroku
- **Authentication**: Flask sessions with werkzeug password hashing

## Installation & Setup

### Prerequisites
- Python 3.8+
- MongoDB Atlas account
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd fest-sponsor-app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   MONGO_URI=your-mongodb-atlas-connection-string
   SECRET_KEY=your-secret-key-change-this-in-production
   FLASK_ENV=development
   ```

4. **Set up MongoDB Atlas**
   - Create a MongoDB Atlas cluster
   - Get your connection string
   - Update the `MONGO_URI` in your `.env` file

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - Login with default credentials: `admin` / `admin123`

## Deployment to GitHub + Heroku

### 1. GitHub Setup
1. Create a new repository on GitHub
2. Push your code to the repository
3. The `.github/workflows/deploy.yml` file is already configured for CI/CD

### 2. Heroku Deployment
1. Create a Heroku account
2. Create a new Heroku app
3. Set up the following environment variables in Heroku:
   - `MONGO_URI`: Your MongoDB Atlas connection string
   - `SECRET_KEY`: A secure secret key for Flask sessions

4. Add Heroku API key to GitHub Secrets:
   - Go to your GitHub repository settings
   - Add `HEROKU_API_KEY` to repository secrets
   - Update the app name in `.github/workflows/deploy.yml`

### 3. MongoDB Atlas Configuration
1. Create a MongoDB Atlas cluster
2. Set up database user credentials
3. Whitelist Heroku's IP addresses (or use 0.0.0.0/0 for all IPs)
4. Get your connection string and add it to Heroku environment variables

## Usage Guide

### First Time Setup
1. Access the application
2. Login with default admin credentials
3. **Important**: Change the default admin password in production
4. Start adding your sponsors, partners, vendors, and participants

### Managing Entities
1. **Search**: Use the search functionality to check if an entity already exists
2. **Add**: Fill out the form to add new entities
3. **View All**: Click "Show All" to see complete lists
4. **Delete**: Remove entities that are no longer needed

### Multi-User Access
- Share the application URL with your 4 friends
- All data is stored in MongoDB Atlas cloud database
- Everyone can access and manage the same data in real-time

## Security Considerations

### For Production Use:
1. **Change default credentials**:
   ```python
   # In app.py, update DEFAULT_ADMIN
   DEFAULT_ADMIN = {
       'username': 'your-admin-username',
       'password': generate_password_hash('your-secure-password'),
       'role': 'admin'
   }
   ```

2. **Use environment variables**:
   - Never commit sensitive data to GitHub
   - Use strong, unique secret keys
   - Secure your MongoDB Atlas credentials

3. **HTTPS**: Ensure your deployment uses HTTPS (Heroku provides this automatically)

## API Endpoints

The application provides RESTful API endpoints for all operations:

- `GET /api/{entity}/count` - Get count of entities
- `POST /api/{entity}/search` - Search entities
- `POST /api/{entity}/add` - Add new entity
- `GET /api/{entity}/list` - List all entities
- `DELETE /api/{entity}/delete/{id}` - Delete entity

Where `{entity}` can be: `sponsors`, `partners`, `vendors`, `participants`

## File Structure

```
fest-sponsor-app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (not in git)
├── .github/
│   └── workflows/
│       └── deploy.yml    # GitHub Actions deployment
├── templates/
│   ├── base.html         # Base template
│   ├── login.html        # Login page
│   ├── dashboard.html    # Dashboard
│   ├── sponsors.html     # Sponsor management
│   ├── partners.html     # Partner management
│   ├── vendors.html      # Vendor management
│   └── participants.html # Participant management
└── static/
    ├── css/
    │   └── style.css     # Stylesheet
    └── js/
        ├── main.js       # Main JavaScript
        └── entity-management.js # Entity management functions
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues or questions:
1. Check the existing issues on GitHub
2. Create a new issue with detailed description
3. Include error messages and steps to reproduce

## License

This project is open source and available under the [MIT License](LICENSE).

---

**Ready to manage your fest like a pro!** 🎉

Start by setting up your MongoDB Atlas database and deploying to Heroku for cloud access with your friends.
=======
# RCSC-FEST-sponsor
>>>>>>> 2e4a709ca27d57f91d17788ee32ed211706e6011
