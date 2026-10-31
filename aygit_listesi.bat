@echo off
cd /d "%~dp0"
SoundVolumeView.exe /scomma ses_aygitlari.csv
MultiMonitorTool.exe /scomma monitorler.csv
echo Tamam - ses_aygitlari.csv ve monitorler.csv olusturuldu.
timeout /t 3 >nul
