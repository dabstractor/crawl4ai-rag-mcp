# Crawl4AI MCP Visualizer UI

A user interface for visualizing crawled websites, embedding descriptions, and other useful information contained within the Crawl4AI MCP system.

## Overview

This project provides a web-based interface to explore and interact with content collected by the Crawl4AI MCP server. The UI connects to the existing Crawl4AI MCP server and provides an intuitive way to explore crawled content without requiring technical expertise.

![Crawl4AI MCP Visualizer Dashboard](docs/dashboard.png)
*Dashboard showing key statistics and quick actions*

## Features

### 📊 Dashboard
- Key statistics and quick actions
- Real-time overview of crawled content
- System status indicators

### 🔍 Semantic Search
- Advanced search using RAG capabilities
- Similarity scoring for results
- Source filtering options
- Configurable result counts

### 📄 Document Explorer
- Browse crawled documents with metadata
- Search and filter by keywords
- Sort by various criteria
- Document preview and details

### 🌐 Source Management
- View and manage content sources
- Source statistics and summaries
- Refresh source information
- Source-based filtering

### 💻 Code Examples
- Browse code snippets (when enabled)
- Syntax highlighting for code display
- Search code examples by content
- Source-based organization

### 📈 Data Visualization
- Statistical overview of crawled content
- Visual representations of data distribution
- Key metrics display
- Chart-based insights

## Prerequisites

- Crawl4AI MCP Server running at `http://localhost:8051`
- Node.js (v14 or higher)
- npm (v6 or higher)
- Modern web browser

## Development Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd crawl4ai-mcp-visualizer
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Configure Environment
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

Edit `.env` to match your configuration:
```bash
REACT_APP_MCP_SERVER_URL=http://localhost:8051/sse
REACT_APP_API_TIMEOUT=30000
REACT_APP_DEFAULT_MATCH_COUNT=10
REACT_APP_PORT=3000
```

### 4. Start Development Server
```bash
npm start
```

The UI will be available at `http://localhost:3000`

## Project Structure

```
crawl4ai-mcp-visualizer/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Dashboard.js
│   │   ├── SearchInterface.js
│   │   ├── DocumentExplorer.js
│   │   ├── SourceManagement.js
│   │   ├── CodeExampleBrowser.js
│   │   ├── DataVisualization.js
│   │   ├── Navigation.js
│   │   └── ConnectionTest.js
│   ├── services/
│   │   └── mcpService.js
│   ├── utils/
│   │   └── sseClient.js
│   ├── App.js
│   ├── App.css
│   ├── index.js
│   ├── index.css
│   └── config.js
├── .env.example
├── .gitignore
├── package.json
└── README.md
```

## Architecture

### Component Architecture
- **Dashboard**: Overview and quick actions
- **SearchInterface**: Semantic search functionality
- **DocumentExplorer**: Document browsing and filtering
- **SourceManagement**: Source management interface
- **CodeExampleBrowser**: Code example browser (conditional)
- **DataVisualization**: Statistical visualizations
- **Navigation**: Tab-based navigation system
- **ConnectionTest**: Connection testing utilities

### Service Layer
- **MCPService**: Main service for MCP tool integration
- **SSEClient**: Server-Sent Events client for real-time communication

### Data Flow
1. User interacts with UI components
2. Components call MCPService methods
3. MCPService uses SSEClient for server communication
4. Server responses are processed and displayed

## API Integration

The UI integrates with the following Crawl4AI MCP tools:

### Core Tools
- `get_available_sources` - Source information retrieval
- `perform_rag_query` - Semantic search
- `scrape_urls` - URL scraping
- `smart_crawl_url` - Intelligent website crawling
- `search` - Comprehensive search

### Conditional Tools
- `search_code_examples` - Code example search (requires `USE_AGENTIC_RAG=true`)

## Configuration

### Environment Variables
- `REACT_APP_MCP_SERVER_URL` - MCP server URL (default: `http://localhost:8051/sse`)
- `REACT_APP_API_TIMEOUT` - Request timeout in milliseconds (default: 30000)
- `REACT_APP_DEFAULT_MATCH_COUNT` - Default number of search results (default: 10)
- `REACT_APP_PORT` - Port to serve UI on (default: 3000)

### Feature Flags
- `USE_AGENTIC_RAG` - Enable code example extraction
- `USE_KNOWLEDGE_GRAPH` - Enable knowledge graph features

## Development Tasks

Task management is handled through Task Master AI. See `.taskmaster/tasks/` for current development tasks.

### Current Task Status
1. ✅ Set up UI development environment
2. ✅ Integrate with MCP server
3. ✅ Implement dashboard UI components
4. ✅ Implement document explorer
5. ✅ Implement source management
6. ✅ Implement semantic search interface
7. ✅ Implement code example browser
8. ✅ Implement data visualization

## Testing

See [TEST_PLAN.md](TEST_PLAN.md) for comprehensive testing guidelines.

### Manual Testing
```bash
npm start
# Open browser at http://localhost:3000
```

### Development Tools
- Component development with hot reloading
- Error boundaries for graceful failure
- Responsive design testing
- Accessibility checking

## Contributing

### Development Workflow
1. Clone the repository
2. Set up development environment
3. Check `.taskmaster/tasks/` for available tasks
4. Create a feature branch
5. Implement your changes
6. Test thoroughly
7. Submit a pull request

### Code Standards
- Follow React best practices
- Use functional components with hooks
- Implement proper error handling
- Maintain responsive design
- Write clean, documented code

### Pull Request Process
1. Ensure all tests pass
2. Update documentation as needed
3. Follow commit message conventions
4. Request code review
5. Address feedback
6. Merge when approved

## Deployment

### Production Build
```bash
npm run build
```

### Deployment Options
- Static file hosting
- Docker container
- Cloud platform deployment
- Custom server setup

## Troubleshooting

### Common Issues
1. **Connection Refused**: Ensure MCP server is running
2. **CORS Errors**: Check server configuration
3. **Missing Data**: Verify server has crawled content
4. **Performance Issues**: Check network and server resources

### Debugging Tools
- Connection test component
- Browser developer tools
- Network tab monitoring
- Console logging

## License

[To be determined]

## Acknowledgments

- Built with React
- Powered by Crawl4AI MCP
- Inspired by modern UI/UX principles
- Designed for developer productivity

## Support

For issues and feature requests, please [open an issue](link-to-issue-tracker) on the repository.