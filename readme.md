# Invoice Automation POC

A simple Proof of Concept for automating invoice processing using OCR/AI, built with a modular monolithic architecture.

## Architecture

**Backend:** Python + FastAPI  
**Frontend:** React  
**Database:** SQLite  

## Project Structure

```
invoice-automation-poc/
├── app/                          # Backend application
│   ├── main.py                   # FastAPI entry point
│   ├── config.py                 # Configuration management
│   ├── api/                      # API routes
│   │   └── routes/
│   │       └── invoice.py        # Invoice endpoints
│   ├── core/                     # Core modules
│   │   ├── ai.py                 # AI/ML integration
│   │   ├── ocr.py                # OCR processing
│   │   └── exceptions.py         # Custom exceptions
│   ├── modules/                  # Business logic modules
│   │   └── invoice/
│   │       ├── extractor.py      # Invoice data extraction
│   │       ├── models.py         # SQLAlchemy models
│   │       ├── repository.py     # Database operations
│   │       ├── schemas.py        # Pydantic schemas
│   │       ├── service.py        # Business logic
│   │       └── validator.py      # Data validation
│   └── utils/                    # Utility functions
│       ├── file_handler.py       # File operations
│       └── helpers.py            # Helper functions
│
├── frontend/                     # React frontend
│   ├── package.json              # NPM dependencies
│   ├── index.html                # HTML entry point
│   └── src/
│       ├── components/           # Reusable components
│       ├── pages/                # Page components
│       ├── services/             # API services
│       ├── App.jsx               # Root component
│       └── main.jsx              # React entry point
│
├── data/                         # Data storage
│   ├── uploads/                  # Temporary uploaded files
│   └── invoice.db                # SQLite database
│
├── .env                          # Environment variables
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
└── README.md                     # Documentation
```

## Getting Started

### Backend Setup

1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables in `.env`

4. Run the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Run development server:
   ```bash
   npm run dev
   ```

## Features

- Upload PDF or image invoices
- OCR/AI-powered invoice data extraction
- Review and edit extracted data
- Save invoices to SQLite database
- Display invoice history locally

## Notes

- Invoice line items are required
- SQLite is the primary database
- No authentication in this POC
- Simple modular monolithic architecture



flowchart TD
    A[PDF upload] --> B[extract_invoice]
    B --> C[extractor: OCR]
    C --> D[extractor: AI]
    D --> E[ExtractedInvoiceResponse]
    E --> F[User reviews/edits in UI]
    F --> G[validate_extracted_invoice optional]
    G --> H[User submits ApprovedInvoiceRequest]
    H --> I[approve_and_save_invoice]
    I --> J[validate_invoice]
    J -->|errors| K[InvoiceValidationError]
    J -->|valid| L[repository.save_invoice]
    L --> M[ApprovedInvoiceResponse in SQLite]
    M --> N[list_saved_invoices / get_saved_invoice]
