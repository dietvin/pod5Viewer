# ------------------------------------------------------ #
$version = "1.0.3"
#  ADJUST THE VERSION NUMBER IN THE ISS FILE AS WELL !!! #
# ------------------------------------------------------ #

# Define relative paths to the PyInstaller spec file and the Inno Setup ISS file
$specFile = ".\pod5Viewer.spec"  # Relative path to your spec file
$issFile = ".\pod5Viewer.iss"   # Relative path to your ISS file

# Define the relative output directory from PyInstaller

# Convert relative paths to absolute paths
$specFilePath = Resolve-Path -Relative $specFile
$issFilePath = Resolve-Path -Relative $issFile

# Run PyInstaller with the spec file
Write-Output "Running PyInstaller..."
Start-Process -NoNewWindow -Wait -FilePath "pyinstaller" -ArgumentList "$specFilePath", "--noconfirm"

# Check if PyInstaller was successful
if ($LASTEXITCODE -ne 0) {
    Write-Output "PyInstaller failed. Exiting script."
    exit $LASTEXITCODE
}

Write-Output "PyInstaller completed successfully."

# Run Inno Setup to create the installer
Write-Output "Running Inno Setup..."
Start-Process -NoNewWindow -Wait -FilePath "ISCC" -ArgumentList $issFilePath

# Check if Inno Setup was successful
if ($LASTEXITCODE -ne 0) {
    Write-Output "Inno Setup failed. Exiting script."
    exit $LASTEXITCODE
}

Write-Output "Inno Setup completed successfully."

Write-Output "Cleaning up"
Move-Item -Path ".\Output\pod5Viewer_Setup.exe" -Destination ".\pod5Viewer-$version-Setup.exe"
Remove-Item -Path ".\Output" -Recurse -Force
Remove-Item -Path ".\build" -Recurse -Force
Remove-Item -Path ".\dist" -Recurse -Force