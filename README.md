# resellsquare-api

ResellSquare Market Price Analysis API.

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

## API

`POST /api/search`

Example request body:

```json
{
  "query": "pokemon charizard card",
  "cost_price": 25,
  "shipping_cost": 5
}
```
