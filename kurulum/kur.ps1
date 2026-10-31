# PC Kumanda kurulumu / güncellemesi — Kur.bat tarafından YÖNETİCİ olarak çalıştırılır.
# 1) Python'u bulur (tüm kullanıcıların erişebileceği bir yerde olmalı)
# 2) Projeyi C:\PC_Kumanda'ya kopyalar, Users grubuna yazma izni verir
# 3) "PC Kumanda" zamanlanmış görevi: herhangi bir kullanıcı oturum açınca pythonw ile başlar
# 4) Güvenlik duvarında portu yerel ağa açar
$ErrorActionPreference = 'Stop'
$Kaynak = Split-Path -Parent $PSScriptRoot
$Hedef  = 'C:\PC_Kumanda'
$Gorev  = 'PC Kumanda'
$Users  = 'S-1-5-32-545'   # BUILTIN\Users (Türkçe Windows'ta adı farklı olduğu için SID)

function Adim($t) { Write-Host "`n>> $t" -ForegroundColor White }
function Uyari($t) { Write-Host "   ! $t" -ForegroundColor Yellow }
function Tamam($t) { Write-Host "   ok $t" -ForegroundColor Green }

try {
    # ---------- 1) Python ----------
    Adim 'Python aranıyor'
    $exe = $null
    foreach ($c in @('python', 'py')) {
        try {
            $argv = if ($c -eq 'py') { @('-3', '-c', 'import sys;print(sys.executable)') } else { @('-c', 'import sys;print(sys.executable)') }
            $out = & $c @argv 2>$null | Select-Object -First 1
            if ($LASTEXITCODE -eq 0 -and $out -and (Test-Path $out.Trim())) { $exe = $out.Trim(); break }
        } catch {}
    }
    if (-not $exe) {
        foreach ($p in Get-ChildItem "$env:ProgramFiles\Python3*\python.exe" -ErrorAction SilentlyContinue) { $exe = $p.FullName }
    }
    $kullaniciya_ozel = $exe -and ($exe -like "$env:SystemDrive\Users\*" -or $exe -like '*WindowsApps*')
    if (-not $exe -or $kullaniciya_ozel) {
        if ($exe) { Uyari "Python sadece senin hesabına kurulu: $exe" ; Uyari 'Diğer kullanıcılar bunu çalıştıramaz.' }
        else { Uyari 'Python bulunamadı.' }
        $cevap = Read-Host '   Python 3.12 tüm kullanıcılar için kurulsun mu? (E/H)'
        if ($cevap -notmatch '^[EeYy]') { throw 'Python tüm kullanıcılar için kurulu olmadan devam edilemiyor.' }
        if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { throw 'winget yok. Python''u python.org''dan "Install for all users" seçeneğiyle kur, sonra Kur.bat''ı tekrar çalıştır.' }
        winget install -e --id Python.Python.3.12 --scope machine --silent --accept-package-agreements --accept-source-agreements
        $exe = "$env:ProgramFiles\Python312\python.exe"
        if (-not (Test-Path $exe)) { throw "Kurulum sonrası Python bulunamadı: $exe" }
    }
    $pyw = Join-Path (Split-Path $exe) 'pythonw.exe'
    if (-not (Test-Path $pyw)) { throw "pythonw.exe yok: $pyw" }
    Tamam $pyw

    # ---------- 2) Çalışan örnekleri durdur + kopyala ----------
    Adim 'Çalışan kumanda örnekleri durduruluyor'
    Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
        Where-Object { $_.CommandLine -like '*pc_kumanda.py*' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Tamam "durduruldu: PID $($_.ProcessId)" }
    Start-Sleep -Milliseconds 800

    if ($Kaynak -ne $Hedef) {
        Adim "Dosyalar kopyalanıyor: $Kaynak -> $Hedef"
        # yerel\ (bu PC'nin aygıt seçimleri) ve cache\ ezilmez: güncelleme ayarları sıfırlamaz
        robocopy $Kaynak $Hedef /E /NJH /NJS /NDL /NP /XD __pycache__ logs yerel cache /XF *.csv pc_kumanda_eski.py monitor_adlari.json | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "robocopy hatası ($LASTEXITCODE)" }
        Tamam 'kopyalandı'
        # robocopy eski dosyaları silmez: kaynaktan kaldırılan modül/eklenti çalışan kopyada kalırsa iki kez yüklenir.
        # Sadece modules\*.py, eklentiler\<ad>\ ve taşınan eski klasörler temizlenir (cache\ ve yerel\ hiç silinmez).
        $eskiler = @()
        $eskiler += Get-ChildItem "$Hedef\modules\*.py" -ErrorAction SilentlyContinue |
            Where-Object { -not (Test-Path (Join-Path "$Kaynak\modules" $_.Name)) }
        $eskiler += Get-ChildItem "$Hedef\eklentiler" -Directory -ErrorAction SilentlyContinue |
            Where-Object { -not (Test-Path (Join-Path "$Kaynak\eklentiler" $_.Name)) }
        foreach ($k in @('native', 'minecraft_mod')) {          # 2026-10-31: eklentiler\minecraft\ altına taşındı
            if ((Test-Path "$Hedef\$k") -and -not (Test-Path "$Kaynak\$k")) { $eskiler += Get-Item "$Hedef\$k" }
        }
        foreach ($e in $eskiler) {
            Remove-Item $e.FullName -Recurse -Force -ErrorAction SilentlyContinue
            Tamam "eski dosya silindi: $($e.FullName.Substring($Hedef.Length + 1))"
        }
    } else {
        Adim 'Zaten C:\PC_Kumanda içinden çalışıyor, kopyalama atlandı'
    }
    icacls $Hedef /grant "*$($Users):(OI)(CI)M" /T /Q | Out-Null
    Tamam 'Users grubuna değiştirme izni verildi'
    Set-Content -Path (Join-Path $Hedef 'kurulum\python_yolu.txt') -Value $pyw -Encoding ASCII

    # ---------- 3) Zamanlanmış görev ----------
    Adim "Zamanlanmış görev: '$Gorev'"
    $script = Join-Path $Hedef 'pc_kumanda.py'
    $a = New-ScheduledTaskAction -Execute $pyw -Argument "`"$script`"" -WorkingDirectory $Hedef
    $t = New-ScheduledTaskTrigger -AtLogOn
    $t.Delay = 'PT10S'
    $p = New-ScheduledTaskPrincipal -GroupId $Users -RunLevel Limited
    $s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
            -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew `
            -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable
    Register-ScheduledTask -TaskName $Gorev -Action $a -Trigger $t -Principal $p -Settings $s `
        -Description 'PC Kumanda: telefondan ekran/ses kontrolü. Her kullanıcının oturumunda başlar.' -Force | Out-Null
    Tamam 'her kullanıcı oturum açınca başlayacak'

    # ---------- 4) Güvenlik duvarı ----------
    $port = 8765
    $m = Select-String -Path (Join-Path $Hedef 'config.py') -Pattern '^\s*PORT\s*=\s*(\d+)' | Select-Object -First 1
    if ($m) { $port = [int]$m.Matches[0].Groups[1].Value }
    Adim "Güvenlik duvarı: TCP $port (sadece yerel ağ)"
    Get-NetFirewallRule -DisplayName 'PC Kumanda' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    New-NetFirewallRule -DisplayName 'PC Kumanda' -Direction Inbound -Protocol TCP -LocalPort $port `
        -Action Allow -Profile Any -RemoteAddress LocalSubnet | Out-Null
    Tamam 'kural eklendi'
    $engel = $null
    try { $engel = Get-NetFirewallApplicationFilter -ErrorAction SilentlyContinue | Where-Object { $_.Program -like '*python*' } |
        Get-NetFirewallRule | Where-Object { $_.Action -eq 'Block' -and $_.Direction -eq 'Inbound' -and $_.Enabled -eq 'True' } } catch {}
    if ($engel) { Uyari "Python için engelleme kuralı var, telefon bağlanamayabilir: $($engel.DisplayName -join ', ')" }

    Write-Host "`nKurulum tamam. Bu pencere kapanınca kumanda bu oturum için başlatılacak." -ForegroundColor Green
    Start-Sleep -Seconds 3
    exit 0
} catch {
    Write-Host "`nHATA: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host 'Kapatmak için Enter'
    exit 1
}
