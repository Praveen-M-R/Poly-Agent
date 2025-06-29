# Poly-Agent Frontend

Modern React frontend for the Poly-Agent application - Monitor, Analyze, Visualize.

## Overview

This is a new, redesigned frontend for the Poly-Agent application, built with React and modern web technologies. It provides a clean, user-friendly interface for accessing both the health monitoring features and GitHub organization analytics tools.

## Features

- **Modern UI**: Clean, responsive design with a focus on usability
- **Integrated Experience**: Seamlessly combines health checks and GitHub analytics
- **Mobile-Friendly**: Fully responsive design that works on all device sizes

## Project Structure

```
src/
├── assets/           # Static assets like images, fonts, etc.
├── components/       # Reusable UI components
├── pages/            # Page components for different routes
├── styles/           # CSS files for styling the application
├── App.js            # Main application component with routing
└── index.js          # Entry point of the application
```

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- npm or yarn

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd Poly-Agent_frontend
```

2. Install dependencies:

```bash
npm install
# or
yarn install
```

3. Start the development server:

```bash
npm start
# or
yarn start
```

The application will be available at http://localhost:3000.

## Available Scripts

- `npm start` - Starts the development server
- `npm build` - Creates a production build
- `npm test` - Runs tests
- `npm eject` - Ejects from Create React App

## Backend Integration

This frontend is designed to work with the Poly-Agent Django backend. It communicates with the backend API endpoints for:

- Health checks data and management
- GitHub organization and repository analytics
- Authentication and user management

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 