# Statistics and Data Visualization Feature

## Overview
The statistics feature provides comprehensive analytics and visualizations for document processing and query activity.

## Backend API Endpoints

All endpoints under `/api/v1/statistics/` require authentication.

### 1. Dashboard Statistics
`GET /api/v1/statistics/dashboard`

Returns overall system statistics.

### 2. Document Statistics  
`GET /api/v1/statistics/documents?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

Returns document processing statistics with optional date filtering.

### 3. Query Statistics
`GET /api/v1/statistics/queries?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

Returns query response statistics with optional date filtering.

## Frontend Dashboard

**File**: `ui/pages/statistics.py`

Run independently with: `streamlit run ui/pages/statistics.py`

### Features
- Overview metrics (documents, queries, response times)
- Interactive visualizations (pie, line, bar, gauge charts)
- Time range filtering
- Real-time data refresh

## Database Changes

Renamed metadata fields to avoid SQLAlchemy conflicts:
- `Document.metadata` → `Document.doc_metadata`
- `DocumentChunk.metadata` → `DocumentChunk.chunk_metadata`
