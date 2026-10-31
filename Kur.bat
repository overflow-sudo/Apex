@echo off
chcp 65001 >nul
title PC Kumanda - Kurulum
echo.
echo  PC KUMANDA // kurulum ve guncelleme
echo  ------------------------------------
echo  Program C:\PC_Kumanda klasorune kopyalanacak ve bu bilgisayarda
echo  oturum acan HER kullanici icin otomatik baslayacak.
echo  Guncellemeden sonra da bu dosyayi tekrar calistir.
echo.
echo  Yonetici izni istenecek...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = Start-Process powershell -Verb RunAs -Wait -PassThru -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','\"%~dp0kurulum\kur.ps1\"'; exit $p.ExitCode"
if errorlevel 1 (
  echo.
  echo  Kurulum tamamlanmadi.
  pause
  exit /b 1
)
set /p PYW=<"C:\PC_Kumanda\kurulum\python_yolu.txt"
echo.
echo  Kumanda simdi bu oturum icin baslatiliyor...
start "" /D "C:\PC_Kumanda" "%PYW%" "C:\PC_Kumanda\pc_kumanda.py"
timeout /t 3 >nul
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  for /f "tokens=* delims= " %%b in ("%%a") do echo  Telefondan ac: http://%%b:8765
)
echo.
rem Modlar bu PC'ye gore ayarlanmadiysa (yerel\bu_pc.json'da "profiles" yok) kurulum sayfasini ac
timeout /t 6 >nul
findstr /m /c:"profiles" "C:\PC_Kumanda\yerel\bu_pc.json" >nul 2>&1
if errorlevel 1 (
  echo  ILK KURULUM: Modlarin hangi ekrani ve ses aygitini kullanacagini secmen gerekiyor.
  echo  Tarayicida acilan sayfada "Ayarlamaya basla" dugmesine tikla.
  echo  Istersen telefondan da yapabilirsin: Modlar sekmesi.
  echo.
  start "" http://localhost:8765
)
echo  Kayitlar: %LOCALAPPDATA%\PC_Kumanda\kumanda.log
echo.
pause
