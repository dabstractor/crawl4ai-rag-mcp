# Crawl4AI MCP Visualizer UI Test Plan

This document outlines the test plan for verifying the integration between the Crawl4AI MCP Visualizer UI and the Crawl4AI MCP server.

## Test Environment Setup

### Prerequisites
1. Crawl4AI MCP server running at `http://localhost:8051`
2. Node.js v14 or higher
3. npm v6 or higher
4. Modern web browser (Chrome, Firefox, Safari, or Edge)

### Configuration
1. Ensure the MCP server is configured with sample data
2. Set up environment variables in `.env` file:
   - `REACT_APP_MCP_SERVER_URL=http://localhost:8051/sse`
   - `REACT_APP_API_TIMEOUT=30000`

## Test Scenarios

### 1. Connection Management
**Objective**: Verify SSE connection establishment and management

**Test Cases**:
- [ ] Connect to MCP server via SSE
- [ ] Handle connection errors gracefully
- [ ] Reconnect after connection loss
- [ ] Close connection properly

**Expected Results**:
- Connection established successfully
- Error messages displayed for connection failures
- Automatic reconnection attempts
- Clean disconnection

### 2. Dashboard Functionality
**Objective**: Verify dashboard data retrieval and display

**Test Cases**:
- [ ] Load available sources count
- [ ] Display document statistics
- [ ] Show code examples count (when available)
- [ ] Handle empty data scenarios

**Expected Results**:
- Statistics displayed correctly
- Loading states shown during data retrieval
- Error messages for failed requests
- Placeholder data for empty states

### 3. Semantic Search
**Objective**: Verify search functionality using perform_rag_query

**Test Cases**:
- [ ] Submit search query
- [ ] Filter results by source
- [ ] Limit results count
- [ ] Display similarity scores
- [ ] Handle search errors

**Expected Results**:
- Search results returned and displayed
- Source filtering works correctly
- Results count limitation respected
- Similarity scores displayed
- Error handling for failed searches

### 4. Document Explorer
**Objective**: Verify document browsing and filtering

**Test Cases**:
- [ ] Load document list
- [ ] Search documents by keyword
- [ ] Filter by source
- [ ] Sort documents
- [ ] View document details

**Expected Results**:
- Documents displayed in grid layout
- Search filters documents correctly
- Source filtering works
- Sorting functions properly
- Document details accessible

### 5. Source Management
**Objective**: Verify source browsing and management

**Test Cases**:
- [ ] Load available sources
- [ ] Search sources by keyword
- [ ] Display source statistics
- [ ] Refresh source list
- [ ] View source details

**Expected Results**:
- Sources displayed with statistics
- Search filters sources correctly
- Statistics displayed accurately
- Refresh updates source list
- Source details accessible

### 6. Code Example Browser
**Objective**: Verify conditional code example browsing

**Test Cases**:
- [ ] Load code examples (when feature enabled)
- [ ] Search code examples by keyword
- [ ] Filter by source
- [ ] Display code with syntax highlighting
- [ ] Handle disabled feature gracefully

**Expected Results**:
- Code examples displayed when enabled
- Search filters code examples
- Source filtering works
- Code displayed with proper formatting
- Graceful handling when feature is disabled

### 7. Data Visualization
**Objective**: Verify data visualization components

**Test Cases**:
- [ ] Load statistics data
- [ ] Display bar charts
- [ ] Show key metrics
- [ ] Handle visualization errors

**Expected Results**:
- Statistics loaded and displayed
- Charts rendered correctly
- Key metrics shown
- Error handling for visualization failures

### 8. Navigation
**Objective**: Verify tab-based navigation

**Test Cases**:
- [ ] Switch between tabs
- [ ] Maintain state between tab switches
- [ ] Highlight active tab
- [ ] Responsive navigation on mobile

**Expected Results**:
- Tabs switch smoothly
- Component state preserved
- Active tab highlighted
- Navigation works on all screen sizes

## Integration Testing

### Server Communication
**Objective**: Verify all MCP tools are accessible via UI

**Test Cases**:
- [ ] `get_available_sources` integration
- [ ] `perform_rag_query` integration
- [ ] `search_code_examples` integration
- [ ] `scrape_urls` integration
- [ ] `smart_crawl_url` integration
- [ ] `search` integration

**Expected Results**:
- All tools accessible through UI
- Requests formatted correctly
- Responses handled properly
- Errors managed gracefully

### Error Handling
**Objective**: Verify error scenarios are handled properly

**Test Cases**:
- [ ] Server unavailable
- [ ] Invalid responses
- [ ] Timeout scenarios
- [ ] Network errors
- [ ] Invalid input handling

**Expected Results**:
- User-friendly error messages
- Graceful degradation
- Retry mechanisms where appropriate
- Input validation

## Performance Testing

### Load Testing
**Objective**: Verify UI performance under load

**Test Cases**:
- [ ] Large result sets
- [ ] Multiple concurrent requests
- [ ] Long-running operations
- [ ] Memory usage

**Expected Results**:
- UI remains responsive
- Pagination for large datasets
- Proper loading states
- No memory leaks

### Browser Compatibility
**Objective**: Verify UI works across different browsers

**Test Cases**:
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

**Expected Results**:
- Consistent behavior across browsers
- No rendering issues
- All features functional

## Security Testing

### Input Validation
**Objective**: Verify input sanitization

**Test Cases**:
- [ ] SQL injection attempts
- [ ] XSS attacks
- [ ] Malformed input
- [ ] Large input handling

**Expected Results**:
- Input properly sanitized
- No security vulnerabilities
- Graceful handling of malformed input
- Input size limitations enforced

## Test Execution

### Manual Testing
1. Run the development server: `npm start`
2. Open browser at `http://localhost:3000`
3. Execute each test scenario
4. Document results
5. Report issues

### Automated Testing
1. Set up test environment
2. Run automated test suite
3. Analyze results
4. Generate reports

## Success Criteria

The UI is considered successfully integrated with the Crawl4AI MCP server when:
- All core features are functional
- Error handling is robust
- Performance is acceptable
- User experience is smooth
- Security requirements are met

## Rollback Plan

If critical issues are found:
1. Revert to previous stable version
2. Document issues found
3. Create bug reports
4. Fix issues in development branch
5. Re-test with fixes