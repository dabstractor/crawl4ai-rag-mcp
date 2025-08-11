# Project Structure

This document explains the file and directory structure of the Crawl4AI MCP Visualizer UI project.

## Root Directory

```
crawl4ai-mcp-visualizer/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Dashboard.js
│   │   ├── Dashboard.css
│   ├── services/
│   │   └── mcpService.js
│   ├── App.js
│   ├── App.css
│   ├── index.js
│   ├── index.css
│   └── config.js
├── .env
├── .env.example
├── .gitignore
├── package.json
├── README.md
└── .taskmaster/
```

## Directories

### `/public`
Contains the static HTML file that serves as the entry point for the React application.

### `/src`
Contains all the source code for the React application.

#### `/src/components`
Contains React components that make up the UI. Each component typically has:
- A `.js` file with the component implementation
- A `.css` file with component-specific styles

#### `/src/services`
Contains service files that handle API calls and business logic.

### `/.taskmaster`
Contains Task Master AI configuration and task files for project management.

## Key Files

### `package.json`
Defines project dependencies, scripts, and metadata.

### `src/index.js`
The entry point of the React application that renders the root component.

### `src/App.js`
The main application component that serves as the root of the component tree.

### `src/config.js`
Configuration settings for the application, including API endpoints and defaults.

### `src/services/mcpService.js`
Service class for interacting with the Crawl4AI MCP Server API.

### `.env`
Environment variables for configuration (not committed to version control).

### `.env.example`
Example environment variables file showing what variables can be configured.

## Development Workflow

1. All UI development should follow the tasks defined in `.taskmaster/tasks/tasks.json`
2. Use `npm start` to run the development server
3. Use `npm run build` to create a production build
4. Follow the component structure pattern for new features
5. Update documentation when adding new features or modifying existing ones