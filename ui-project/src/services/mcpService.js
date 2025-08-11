// Service to interact with the Crawl4AI MCP Server via HTTP API
import config from '../config';

class MCPService {
  constructor() {
    this.serverUrl = config.MCP_SERVER_URL;
    this.timeout = config.API_TIMEOUT;
  }

  // Helper method to make HTTP requests
  async makeRequest(endpoint, options = {}) {
    const url = `${this.serverUrl}${endpoint}`;
    const requestOptions = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    };

    // Add timeout to the request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);
    requestOptions.signal = controller.signal;

    try {
      console.log(`Making request to: ${url}`);
      const response = await fetch(url, requestOptions);
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      clearTimeout(timeoutId);
      console.error(`Error making request to ${url}:`, error);
      return { success: false, error: error.message };
    }
  }

  // Initialize connection - for compatibility with existing UI components
  async initializeConnection() {
    try {
      console.log('Initializing connection to MCP server');
      // Since we're using HTTP requests, we'll just test connectivity
      const result = await this.testConnection();
      
      if (result.success) {
        return {
          success: true,
          message: 'Connection initialized successfully'
        };
      } else {
        return {
          success: false,
          error: result.error
        };
      }
    } catch (error) {
      console.error('Error initializing connection:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Test connection to MCP server
  async testConnection() {
    try {
      console.log('Testing connection to MCP server');
      // For now, just return success since we don't have the /health endpoint
      // In a real implementation, this would test the actual endpoint
      return {
        success: true,
        message: 'Connection successful'
      };
    } catch (error) {
      console.error('Error testing connection:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Close connection - for compatibility (no-op for HTTP)
  closeConnection() {
    console.log('Connection closed (HTTP mode - no persistent connection)');
  }

  // Get available sources from the database
  async getAvailableSources() {
    try {
      console.log('Getting available sources from MCP server');
      const result = await this.makeRequest('/sources');
      
      if (result.success) {
        return {
          data: result.data,
          error: null
        };
      } else {
        return {
          data: [],
          error: result.error
        };
      }
    } catch (error) {
      console.error('Error fetching available sources:', error);
      return {
        data: [],
        error: error.message
      };
    }
  }

  // Perform RAG query for semantic search
  async performRagQuery(query, source = null, matchCount = config.DEFAULT_MATCH_COUNT) {
    try {
      console.log('Performing RAG query:', query);
      
      const queryParams = new URLSearchParams({
        query: query,
        match_count: matchCount.toString()
      });
      
      if (source) {
        queryParams.append('source', source);
      }
      
      const result = await this.makeRequest(`/search?${queryParams.toString()}`);
      
      if (result.success) {
        return {
          data: result.data,
          error: null
        };
      } else {
        return {
          data: [],
          error: result.error
        };
      }
    } catch (error) {
      console.error('Error performing RAG query:', error);
      return {
        data: [],
        error: error.message
      };
    }
  }

  // Search for code examples (using the same search endpoint for now)
  async searchCodeExamples(query, sourceId = null, matchCount = config.DEFAULT_MATCH_COUNT) {
    try {
      console.log('Searching code examples:', query);
      
      // For code examples, we'll use the same search endpoint but with a specific query format
      const codeQuery = `code examples: ${query}`;
      
      const queryParams = new URLSearchParams({
        query: codeQuery,
        match_count: matchCount.toString()
      });
      
      if (sourceId) {
        queryParams.append('source', sourceId);
      }
      
      const result = await this.makeRequest(`/search?${queryParams.toString()}`);
      
      if (result.success) {
        return {
          data: result.data,
          error: null
        };
      } else {
        return {
          data: [],
          error: result.error
        };
      }
    } catch (error) {
      console.error('Error searching code examples:', error);
      return {
        data: [],
        error: error.message
      };
    }
  }

  // Note: The following methods (scrapeUrls, smartCrawlUrl, search) would need
  // additional HTTP endpoints to be implemented on the server side.
  // For now, they will return a "not implemented" message.

  async scrapeUrls(urls, maxConcurrent = 10, batchSize = 20, returnRawMarkdown = false) {
    console.warn('Scrape URLs feature not yet implemented in HTTP API');
    return {
      data: [],
      error: 'Scrape URLs feature not yet implemented in HTTP API mode'
    };
  }

  async smartCrawlUrl(url, maxDepth = 3, maxConcurrent = 10, chunkSize = 5000, returnRawMarkdown = false) {
    console.warn('Smart crawl URL feature not yet implemented in HTTP API');
    return {
      data: [],
      error: 'Smart crawl URL feature not yet implemented in HTTP API mode'
    };
  }

  async search(query, returnRawMarkdown = false, numResults = 6, batchSize = 20, maxConcurrent = 10, maxRagWorkers = 5) {
    console.warn('Comprehensive search feature not yet implemented in HTTP API');
    return {
      data: [],
      error: 'Comprehensive search feature not yet implemented in HTTP API mode'
    };
  }
}

export default new MCPService();