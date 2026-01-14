## Rodar local

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

## Docker

docker build -t face-event-backend:latest .
docker run -it --rm -p 8080:8080 --env-file .env face-event-backend:latest
