# XPOM-KZ Logistics Management System

## Overview
XPOM-KZ is a comprehensive logistics management web application built for the logistics department of "Хром-КЗ" company. The system automates order intake and management for deliveries within Astana and across Kazakhstan. It features a modern, minimalist public interface for customers to create and track orders, alongside a powerful administrative dashboard for logistics staff to manage operations, drivers, and analytics.

## Recent Changes
**Calendar Feature Added (August 13, 2025):**
- Created modern minimalist admin panel with sidebar navigation
- Added interactive shipment calendar using FullCalendar.js
- Implemented calendar event management with color-coded status indicators
- Added shipment scheduling functionality with date selection
- Created order-to-driver assignment system within calendar
- Added database columns for pickup/delivery scheduling
- Sample data created for calendar demonstration

**Migration Completed (August 13, 2025):**
- Successfully migrated project from Replit Agent to Replit environment
- All required Python packages installed and configured
- PostgreSQL database provisioned and connected
- Application running on Gunicorn server (port 5000)
- Missing error templates (404.html, 500.html) created
- Default admin account created: admin@xpom-kz.com / admin123
- Full functionality restored and verified

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templating with Bootstrap 5 for responsive design
- **UI/UX Design**: Modern minimalist interface with clean white backgrounds and primary blue color scheme
- **JavaScript**: Vanilla JavaScript with Chart.js for analytics visualization
- **CSS Framework**: Bootstrap 5 with custom CSS variables for consistent theming
- **Icons**: Font Awesome for consistent iconography throughout the application

### Backend Architecture
- **Framework**: Flask (Python web framework) with modular structure
- **Authentication**: Flask-Login for session management with role-based access control
- **Form Handling**: Flask-WTF for secure form processing with CSRF protection
- **Database ORM**: SQLAlchemy with declarative base for database operations
- **Security**: CSRF protection, password hashing with Werkzeug, and proxy fix middleware

### Data Models
- **User Model**: Handles authentication with roles (employee, logist) and user profiles
- **Order Model**: Core business entity with tracking numbers, status management, and customer details
- **Driver Model**: Manages driver information and vehicle assignments
- **OrderStatusHistory**: Tracks status changes for audit trail and customer updates

### Application Structure
- **app.py**: Application factory with extension initialization
- **models.py**: SQLAlchemy database models and relationships
- **routes.py**: Request handling and business logic routing
- **forms.py**: WTForms for input validation and form rendering
- **utils.py**: Helper functions for formatting and template filters
- **main.py**: Application entry point for development server

### Authentication & Authorization
- **Role-based Access**: Two-tier system with employees (limited access) and logists (full access)
- **Session Management**: Flask-Login handles user sessions and login persistence
- **Password Security**: Werkzeug password hashing for secure credential storage

### Order Management System
- **Tracking System**: Unique tracking number generation (AST-YYYY-XXX, KZ-YYYY-XXX)
- **Status Workflow**: Multi-stage order processing from 'new' to 'delivered'
- **Customer Interface**: Public order creation and tracking without authentication required
- **Admin Interface**: Comprehensive order management with status updates and driver assignment

## External Dependencies

### Core Dependencies
- **Flask**: Web framework for request handling and routing
- **SQLAlchemy**: Database ORM for data persistence and relationships
- **Flask-Login**: User session management and authentication
- **Flask-WTF**: Form handling with CSRF protection
- **WTForms**: Form validation and rendering
- **Werkzeug**: Password hashing and security utilities

### Database
- **SQLite**: Default database for development with configurable DATABASE_URL
- **Connection Pool**: Configured with pool recycling and pre-ping for reliability

### External Integrations
- **Telegram Bot API**: Automated notifications to logistics team via requests library
- **Environment Variables**: 
  - `TELEGRAM_BOT_TOKEN`: Bot authentication for message sending
  - `TELEGRAM_CHAT_ID`: Target chat for order notifications
  - `DATABASE_URL`: Database connection string
  - `SESSION_SECRET`: Flask session encryption key

### Frontend Libraries
- **Bootstrap 5**: Responsive CSS framework from CDN
- **Font Awesome 6**: Icon library for UI elements
- **Chart.js**: Data visualization for analytics dashboard

### Development Tools
- **ProxyFix**: Werkzeug middleware for handling reverse proxy headers
- **Logging**: Built-in Python logging configured for debugging
- **Debug Mode**: Flask development server with hot reload capability