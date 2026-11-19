# Booking Yna API

## Credentials (easy)
Open **`../env-profiles/`** — copy `DEV.env.example` → `DEV.env`, fill secrets, then:

```powershell
copy ..\env-profiles\DEV.env .env
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```
