## Rodar local

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

## Rodar /tests
Coloque no terminal vscode
1° rode este -> python -m pytest tests/test_s3_smoke.py tests/test_rekognition_smoke.py -q
2° rode este -> python -m pytest tests/test_s3_smoke.py tests/test_rekognition_smoke.py -vv -s

## Docker

docker build -t face-event-backend:latest .
docker run -it --rm -p 8080:8080 --env-file .env face-event-backend:latest
