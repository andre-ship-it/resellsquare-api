# ResellSquare API Deployment

This service is a Flask API with deterministic pricing extraction:
- Primary source: direct eBay sold/completed listing HTML parsing
- Fallback source: DDG search parsing

No OpenAI API key is required for this version.

## 1. Local Run

```bash
cd /Users/user/resell-square
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
lsof -tiTCP:8080 -sTCP:LISTEN | xargs kill -9 2>/dev/null
python3 app.py
```

Server should start on `http://localhost:8080`.

## 2. Local API Test

```bash
curl -i -X POST "http://localhost:8080/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"pokemon charizard card","cost_price":25,"shipping_cost":5}'
```

Validation test (expected `400`):

```bash
curl -i -X POST "http://localhost:8080/api/search" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 3. Railway Deploy

## Service Settings
- Runtime: Python
- Start Command:

```bash
gunicorn -w 2 -k gthread -b 0.0.0.0:$PORT app:app
```

- Build command (optional):

```bash
pip install -r requirements.txt
```

## Environment Variables
- `PORT` is provided by Railway automatically.
- No `OPENAI_API_KEY` needed for current implementation.

## 4. Post-Deploy Verification

1. Open `https://<your-railway-domain>/`
2. Test endpoint:

```bash
curl -i -X POST "https://<your-railway-domain>/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"pokemon charizard card","cost_price":25,"shipping_cost":5}'
```

## 5. Troubleshooting

- `Address already in use`:

```bash
lsof -tiTCP:8080 -sTCP:LISTEN | xargs kill -9 2>/dev/null
```

- `502` with source `ebay_agent`:
  - Query returned no parsable sold-price data from both eBay HTML and DDG.
  - Retry with a more specific product query.

- Dependency issues:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```
