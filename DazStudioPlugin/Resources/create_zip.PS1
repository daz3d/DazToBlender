param(
    [string]$SourceDir,
    [string]$DestZip
)

if (Test-Path -Path $DestZip) {
    Remove-Item -Path $DestZip -ErrorAction SilentlyContinue
}

Compress-Archive -Path "$SourceDir\*" -DestinationPath $DestZip -Force