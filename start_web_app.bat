@echo off
echo Starting FastAPI Web Application with Database Integration...
cd imageprocessing
python -m uvicorn main:app --reload --host localhost --port 8000
pause 