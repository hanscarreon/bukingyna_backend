# Booking Yna API

## Credentials (easy)
Open **`../env-profiles/`** — copy `DEV.env.example` → `DEV.env`, fill secrets, then:

```powershell
copy ..\env-profiles\DEV.env .env
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Health: http://127.0.0.1:8000/health  
- Docs: http://127.0.0.1:8000/docs  
- DEV seed admin: `superadmin@example.com` / `Admin@12345` (`AUTH_PROVIDER=local`)

## Auth endpoints
- `POST /auth/email/register`
- `POST /auth/email/login` (`client`: `mobile` | `admin`)
- `POST /auth/email/forgot-password`
- `POST /auth/mobile/start` (DEV returns `dev_otp`)
- `POST /auth/mobile/verify-otp`
- `POST /auth/mobile/set-pin`
- `POST /auth/mobile/pin-login`
- `POST /auth/logout`
- `GET /auth/me`

Set `AUTH_PROVIDER=supabase` and fill Supabase keys in env-profiles for UAT/PROD.
