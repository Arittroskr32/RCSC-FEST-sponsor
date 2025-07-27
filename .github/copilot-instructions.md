<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Fest Sponsor Management Application

This is a Flask-based web application for managing event sponsors, partners, vendors, and participants with MongoDB Atlas integration.

## Architecture
- **Backend**: Python Flask with MongoDB Atlas
- **Frontend**: HTML5, CSS3, vanilla JavaScript
- **Authentication**: Flask sessions with werkzeug password hashing
- **Deployment**: GitHub + Heroku

## Key Components
1. **Admin authentication system** with session management
2. **CRUD operations** for sponsors, partners, vendors, and participants
3. **Search functionality** across all entity types
4. **Dashboard** with real-time statistics
5. **RESTful API endpoints** for all operations

## Development Guidelines
- Use consistent naming conventions (snake_case for Python, camelCase for JavaScript)
- Follow Flask best practices for route organization
- Implement proper error handling and user feedback
- Maintain responsive design for mobile compatibility
- Use environment variables for sensitive configuration

## Database Schema
All entities follow similar structure:
- Basic info: name, email, phone
- Entity-specific fields (company, organization, service_type, etc.)
- Timestamps: created_at, created_by
- Unique constraints on email and name combinations

## Security Considerations
- All routes (except login) require authentication
- Password hashing with werkzeug
- Input validation and sanitization
- Environment variables for secrets
- CSRF protection consideration for forms
