// Utility for handling SSE connections to MCP server
import config from '../config';

class SSEClient {
  constructor() {
    this.eventSource = null;
    this.callbacks = new Map();
    this.requestId = 0;
    this.pendingRequests = new Map();
  }

  // Initialize SSE connection
  connect(url = config.MCP_SERVER_URL) {
    if (this.eventSource) {
      this.disconnect();
    }

    try {
      this.eventSource = new EventSource(url);
      
      this.eventSource.onopen = (event) => {
        console.log('SSE connection opened');
        this.handleEvent('open', event);
      };

      this.eventSource.onerror = (event) => {
        console.error('SSE connection error:', event);
        this.handleEvent('error', event);
      };

      // Listen for tool response events
      this.eventSource.addEventListener('tool_response', (event) => {
        this.handleToolResponse(event);
      });

      // Listen for other relevant events
      this.eventSource.addEventListener('status', (event) => {
        this.handleEvent('status', event);
      });

      return true;
    } catch (error) {
      console.error('Error establishing SSE connection:', error);
      return false;
    }
  }

  // Disconnect SSE connection
  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this.callbacks.clear();
      this.pendingRequests.clear();
    }
  }

  // Register callback for specific events
  on(eventType, callback) {
    if (!this.callbacks.has(eventType)) {
      this.callbacks.set(eventType, []);
    }
    this.callbacks.get(eventType).push(callback);
  }

  // Remove callback for specific events
  off(eventType, callback) {
    if (this.callbacks.has(eventType)) {
      const callbacks = this.callbacks.get(eventType);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  // Handle incoming events
  handleEvent(eventType, event) {
    if (this.callbacks.has(eventType)) {
      this.callbacks.get(eventType).forEach(callback => {
        try {
          callback(event);
        } catch (error) {
          console.error(`Error in ${eventType} callback:`, error);
        }
      });
    }
  }

  // Handle tool response events
  handleToolResponse(event) {
    try {
      const data = JSON.parse(event.data);
      const { request_id, response } = data;
      
      // If this is a response to a pending request, resolve it
      if (this.pendingRequests.has(request_id)) {
        const { resolve, reject, timeoutId } = this.pendingRequests.get(request_id);
        clearTimeout(timeoutId);
        this.pendingRequests.delete(request_id);
        resolve(response);
      }
      
      // Also trigger general tool_response callbacks
      this.handleEvent('tool_response', event);
    } catch (error) {
      console.error('Error handling tool response:', error);
      this.handleEvent('tool_response_error', { error });
    }
  }

  // Send a request to the MCP server
  async sendRequest(toolName, argumentsObj = {}, timeout = config.API_TIMEOUT) {
    const requestId = ++this.requestId;
    
    return new Promise((resolve, reject) => {
      // Set up timeout
      const timeoutId = setTimeout(() => {
        this.pendingRequests.delete(requestId);
        reject(new Error(`Request timeout after ${timeout}ms`));
      }, timeout);
      
      // Store pending request
      this.pendingRequests.set(requestId, { resolve, reject, timeoutId });
      
      // Send request via HTTP POST (SSE is for receiving responses)
      this.sendHttpRequest(toolName, argumentsObj, requestId)
        .catch(error => {
          clearTimeout(timeoutId);
          this.pendingRequests.delete(requestId);
          reject(error);
        });
    });
  }

  // Send HTTP request to MCP server (SSE is unidirectional, so we need HTTP for requests)
  async sendHttpRequest(toolName, argumentsObj, requestId) {
    try {
      // Extract base URL without /sse suffix for HTTP requests
      const baseUrl = config.MCP_SERVER_URL.replace('/sse', '');
      const url = `${baseUrl}/tools/${toolName}`;
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          arguments: argumentsObj,
          request_id: requestId
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // The actual response will come via SSE as a tool_response event
      // We just need to ensure the request was accepted
      return { success: true };
    } catch (error) {
      console.error(`Error sending HTTP request to ${toolName}:`, error);
      throw error;
    }
  }

  // Get connection status
  isConnected() {
    return this.eventSource && this.eventSource.readyState === EventSource.OPEN;
  }

  // Get number of pending requests
  getPendingRequestCount() {
    return this.pendingRequests.size;
  }
}

export default new SSEClient();