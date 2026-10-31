@echo off
chcp 65001 >nul
title PC Kumanda - Kaldir
echo  PC Kumanda otomatik baslatma kaldirilacak. Yonetici izni istenecek...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -Wait -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','\"%~dp0kurulum\kaldir.ps1\"'"
