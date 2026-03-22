# pdf-splitter-api
PDF splitting API for mail automation project
API pour découper les PDFs de courrier scannés en documents individuels basés sur les pages blanches.

## Endpoints

### GET /
Informations sur l'API

### GET /health
Health check

### POST /split-pdf
Découpe un PDF en plusieurs documents

**Body (JSON):**
```json
{
  "pdf": "base64_encoded_pdf",
  "text_array": ["page 1 text", "page 2 text", ...]  // optionnel
}
