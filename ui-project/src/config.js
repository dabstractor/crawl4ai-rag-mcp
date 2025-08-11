// Configuration for the Crawl4AI MCP Visualizer
const config = {
  // MCP Server URL - now using HTTP API endpoints
  MCP_SERVER_URL: process.env.REACT_APP_MCP_SERVER_URL || 'http://localhost:8051/api',
  
  // Timeout for API requests (in milliseconds)
  API_TIMEOUT: process.env.REACT_APP_API_TIMEOUT || 30000,
  
  // Default number of results to display
  DEFAULT_MATCH_COUNT: process.env.REACT_APP_DEFAULT_MATCH_COUNT || 10,
  
  // Port to serve the UI on (avoiding 8051 which is used by MCP server)
  PORT: process.env.REACT_APP_PORT || 3741,
};

export default config;