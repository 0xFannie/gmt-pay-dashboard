@echo off
echo ===============================================
echo   GMT Pay Card Sales Dashboard
echo   Product: fsl.com/gmtpay
echo ===============================================
echo.
echo Starting dashboard...
echo Dashboard will open in your browser automatically.
echo Access URL: http://localhost:8501
echo.
echo Press Ctrl+C to stop the dashboard.
echo.
python -m streamlit run dashboard_v3_dynamic.py
pause

