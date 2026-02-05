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

### Running Options

#### Option 1: Run Independently
```bash
streamlit run ui/pages/statistics.py
```

#### Option 2: Using Streamlit Multipage Apps (Recommended)
For better integration, move the statistics page to follow Streamlit's native multipage structure:
1. Create a `pages/` subdirectory under `ui/`
2. Rename `statistics.py` to `1_📊_Statistics.py` (or similar)
3. Streamlit will automatically create navigation

For more info, see [Streamlit Multipage Apps](https://docs.streamlit.io/library/get-started/multipage-apps)

### Features
- Overview metrics (documents, queries, response times)
- Interactive visualizations (pie, line, bar, gauge charts)
- Time range filtering
- Real-time data refresh

## Database Changes

Renamed metadata fields to avoid SQLAlchemy conflicts:
- `Document.metadata` → `Document.doc_metadata`
- `DocumentChunk.metadata` → `DocumentChunk.chunk_metadata`
