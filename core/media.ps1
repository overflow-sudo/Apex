# PC Kumanda - now playing reader (Windows media session / SMTC).
# Started by modules/media.py; prints one JSON line every ~1.5 s to stdout.
# Uses WinRT from Windows PowerShell 5.1, no extra packages.
param([string]$CoverPath)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$type) {
    $task = $asTaskGeneric.MakeGenericMethod($type).Invoke($null, @($op))
    $task.Wait(-1) | Out-Null
    $task.Result
}

$null = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStreamWithContentType, Windows.Storage.Streams, ContentType = WindowsRuntime]
$mgr = Await ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager])

$lastKey = ''
$coverVer = 0
$hasCover = $false
$coverTries = 0

while ($true) {
    $out = @{ ok = $true }
    try {
        $s = $mgr.GetCurrentSession()
        if ($s -ne $null) {
            $p = Await ($s.TryGetMediaPropertiesAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
            $info = $s.GetPlaybackInfo()
            $tl = $s.GetTimelineProperties()
            $status = $info.PlaybackStatus.ToString()
            $pos = $tl.Position.TotalSeconds
            if ($status -eq 'Playing' -and $tl.LastUpdatedTime.Year -gt 2000) {
                $pos += ([DateTimeOffset]::Now - $tl.LastUpdatedTime).TotalSeconds
            }
            $key = "$($s.SourceAppUserModelId)|$($p.Title)|$($p.Artist)"
            if ($key -ne $lastKey) {
                $lastKey = $key
                $hasCover = $false
                $coverTries = 0
                $coverVer++
            }
            # Spotify etc. sometimes publish the thumbnail a moment after the track changes: retry a few times
            if (-not $hasCover -and $coverTries -lt 6 -and $p.Thumbnail -ne $null) {
                $coverTries++
                try {
                    $ras = Await ($p.Thumbnail.OpenReadAsync()) ([Windows.Storage.Streams.IRandomAccessStreamWithContentType])
                    $st = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($ras)
                    $ms = New-Object System.IO.MemoryStream
                    $st.CopyTo($ms)
                    $st.Dispose()
                    if ($ms.Length -gt 100) {
                        [System.IO.File]::WriteAllBytes($CoverPath, $ms.ToArray())
                        $hasCover = $true
                        $coverVer++
                    }
                } catch { }
            }
            $out.title = $p.Title
            $out.artist = $p.Artist
            $out.album = $p.AlbumTitle
            $out.app = $s.SourceAppUserModelId
            $out.status = $status
            $out.pos = [math]::Round($pos, 1)
            $out.dur = [math]::Round($tl.EndTime.TotalSeconds, 1)
            $out.cover = $(if ($hasCover) { $coverVer } else { 0 })
        }
    } catch {
        $out = @{ ok = $false; error = $_.Exception.Message }
    }
    [Console]::Out.WriteLine(($out | ConvertTo-Json -Compress))
    [Console]::Out.Flush()
    Start-Sleep -Milliseconds 1500
}
