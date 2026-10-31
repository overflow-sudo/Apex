# PC Kumanda'yı kaldırır: zamanlanmış görev + güvenlik duvarı kuralı + çalışan örnekler.
# C:\PC_Kumanda klasörü istenirse silinir.
$ErrorActionPreference = 'Continue'
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
    Where-Object { $_.CommandLine -like '*pc_kumanda.py*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Unregister-ScheduledTask -TaskName 'PC Kumanda' -Confirm:$false -ErrorAction SilentlyContinue
Get-NetFirewallRule -DisplayName 'PC Kumanda' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
Write-Host 'Görev ve güvenlik duvarı kuralı kaldırıldı.' -ForegroundColor Green
if (Test-Path 'C:\PC_Kumanda') {
    $c = Read-Host 'C:\PC_Kumanda klasörü de silinsin mi? (E/H)'
    if ($c -match '^[EeYy]') { Remove-Item 'C:\PC_Kumanda' -Recurse -Force; Write-Host 'Silindi.' }
}
Read-Host 'Kapatmak için Enter'
