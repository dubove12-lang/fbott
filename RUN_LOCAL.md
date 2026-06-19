# Run locally

```powershell
cd C:\Users\LubeN\copytrading
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

$env:HYDROMANCER_API_KEY="your_key_here"

python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

`http://127.0.0.1:8000`
