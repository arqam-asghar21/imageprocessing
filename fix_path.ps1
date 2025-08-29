Write-Host "Fixing path issue by copying project to C:\klipps_project..." -ForegroundColor Green

# Create directory
New-Item -ItemType Directory -Path "C:\klipps_project" -Force

# Copy all files
Copy-Item -Path "C:\Users\Arqam Asghar\Desktop\imageprocessing\*" -Destination "C:\klipps_project\" -Recurse -Force

Write-Host "Project copied successfully to C:\klipps_project" -ForegroundColor Green
Write-Host "Now you can run the project from C:\klipps_project" -ForegroundColor Yellow 