@echo off
echo Starting Mobile App from path without spaces...

REM Create a temporary directory without spaces
mkdir "C:\temp_klipps" 2>nul

REM Copy the mobile app to temp location
xcopy "C:\Users\Arqam Asghar\Desktop\imageprocessing\klipps_app\*" "C:\temp_klipps\" /E /I /H /Y

REM Change to temp directory and run Flutter
cd /d "C:\temp_klipps"
flutter run

REM Clean up
cd /d "C:\Users\Arqam Asghar\Desktop\imageprocessing"
rmdir /s /q "C:\temp_klipps" 2>nul

pause 