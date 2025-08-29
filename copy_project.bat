@echo off
echo Copying project to C:\klipps_project to fix path issues...
mkdir "C:\klipps_project" 2>nul
xcopy "C:\Users\Arqam Asghar\Desktop\imageprocessing\*" "C:\klipps_project\" /E /I /H /Y
echo Project copied successfully!
echo Now you can run from C:\klipps_project
pause 