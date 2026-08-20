# Generates desktop/src-tauri/icons/icon.png (1024) and icon.ico (256)
Add-Type -AssemblyName System.Drawing

function New-SciIcon([int]$size) {
    $bmp = New-Object System.Drawing.Bitmap($size, $size)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias

    # Rounded-square navy background
    $radius = [int]($size * 0.20)
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $rect = New-Object System.Drawing.Rectangle(0, 0, $size, $size)
    $path.AddArc($rect.X, $rect.Y, $radius * 2, $radius * 2, 180, 90)
    $path.AddArc($rect.Right - $radius * 2, $rect.Y, $radius * 2, $radius * 2, 270, 90)
    $path.AddArc($rect.Right - $radius * 2, $rect.Bottom - $radius * 2, $radius * 2, $radius * 2, 0, 90)
    $path.AddArc($rect.X, $rect.Bottom - $radius * 2, $radius * 2, $radius * 2, 90, 90)
    $path.CloseFigure()
    $bg = New-Object System.Drawing.Drawing2D.LinearGradientBrush($rect, ([System.Drawing.Color]::FromArgb(15, 26, 51)), ([System.Drawing.Color]::FromArgb(29, 48, 89)), 45)
    $g.FillPath($bg, $path)

    # Rising bar chart (teal/green)
    $teal = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(45, 212, 191))
    $u = $size / 100.0
    $g.FillRectangle($teal, [int](30*$u), [int](58*$u), [int](10*$u), [int](14*$u))
    $g.FillRectangle($teal, [int](45*$u), [int](48*$u), [int](10*$u), [int](24*$u))
    $g.FillRectangle($teal, [int](60*$u), [int](38*$u), [int](10*$u), [int](34*$u))

    # Magnifying glass ring + handle (white)
    $white = New-Object System.Drawing.Pen([System.Drawing.Color]::White, [Math]::Max(2, $size * 0.035))
    $cx = [int](45*$u); $cy = [int](45*$u); $r = [int](24*$u)
    $g.DrawEllipse($white, $cx - $r, $cy - $r, $r * 2, $r * 2)
    $hx = $cx + [int]($r * 0.72); $hy = $cy + [int]($r * 0.72)
    $g.DrawLine($white, $hx, $hy, [int](82*$u), [int](82*$u))

    $g.Dispose()
    return $bmp
}

$dir = Join-Path $PSScriptRoot "..\..\desktop\src-tauri\icons"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

$big = New-SciIcon 1024
$big.Save((Join-Path $dir "icon.png"), [System.Drawing.Imaging.ImageFormat]::Png)

$small = New-SciIcon 256
$fs = [System.IO.File]::Create((Join-Path $dir "icon.ico"))
# Minimal single-image ICO: header + directory entry + PNG payload
$ms = New-Object System.IO.MemoryStream
$small.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
$png = $ms.ToArray()
$bw = New-Object System.IO.BinaryWriter($fs)
$bw.Write([uint16]0)          # reserved
$bw.Write([uint16]1)          # type = icon
$bw.Write([uint16]1)          # count
$bw.Write([byte]0)            # width (0 = 256)
$bw.Write([byte]0)            # height
$bw.Write([byte]0)            # colors
$bw.Write([byte]0)            # reserved
$bw.Write([uint16]1)          # planes
$bw.Write([uint16]32)         # bpp
$bw.Write([uint32]$png.Length)
$bw.Write([uint32]22)         # offset to payload
$bw.Write($png)
$bw.Dispose(); $fs.Dispose(); $ms.Dispose()
$small.Dispose(); $big.Dispose()

Write-Host "Icons written to $dir"
