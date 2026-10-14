@echo off
title AMA Ceramics - Cloud & Mobile Sync Server
echo ===================================================
echo   AMA CERAMICS - CLOUD & MOBILE SYNC BACKEND
echo ===================================================
echo.
echo Starting FastAPI sync server on 0.0.0.0:8000...
echo Both PC and Android phones on the Wi-Fi network can connect.
echo.
python server/main.py
pause
