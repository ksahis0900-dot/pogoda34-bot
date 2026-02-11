[Reflection.Assembly]::LoadWithPartialName("System.Drawing")

$files = Get-ChildItem "images/*.png"
foreach ($f in $files) {
    Write-Host "Compressing $($f.Name)..."
    $img = [System.Drawing.Image]::FromFile($f.FullName)
    $jpgEncoder = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.FormatID -eq [System.Drawing.Imaging.ImageFormat]::Jpeg.Guid }
    $encoderParams = New-Object System.Drawing.Imaging.EncoderParameters(1)
    $encoderParams.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, 80)
    
    $outPath = $f.FullName -replace "\.png$", ".jpg"
    $img.Save($outPath, $jpgEncoder, $encoderParams)
    $img.Dispose()
    
    Remove-Item $f.FullName
}
Write-Host "Done!"
