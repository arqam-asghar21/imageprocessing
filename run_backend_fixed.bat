@echo off
echo Starting Backend Server...
cd /d "C:\Users\Arqam Asghar\Desktop\imageprocessing\imageprocessing"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause 