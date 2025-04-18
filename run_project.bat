@echo off
echo Starting Music App Server...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Apply migrations
echo Applying database migrations...
python manage.py migrate

REM Start the server
echo.
echo Starting the Django server...
echo Access the application at http://127.0.0.1:8000/
echo Access the Spotify features at http://127.0.0.1:8000/spotify/login/
echo.
python manage.py runserver

pause 