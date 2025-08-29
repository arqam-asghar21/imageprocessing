# PowerShell script to move project to C:\klipps_project
Write-Host "Moving project to C:\klipps_project to avoid path issues..." -ForegroundColor Green

# Create the new directory
New-Item -ItemType Directory -Path "C:\klipps_project" -Force

# Copy all files to the new location
Copy-Item -Path "C:\Users\Arqam Asghar\Desktop\imageprocessing\*" -Destination "C:\klipps_project\" -Recurse -Force

Write-Host "Project moved successfully to C:\klipps_project" -ForegroundColor Green
Write-Host "You can now run the project from C:\klipps_project" -ForegroundColor Yellow 