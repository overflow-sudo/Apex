# Sistem paneli (CPU/GPU/RAM/VRAM/sıcaklık, PDH, LHM)

(CLAUDE.md'den taşındı, 2026-10-31. Genel kurallar CLAUDE.md'de.)

## Sistem paneli
- CPU: PDH `\Processor Information(_Total)\% Processor Utility` (Görev Yöneticisi ile aynı değer),
  yoksa `\Processor(_Total)\% Processor Time`.
- GPU: `\GPU Engine(*)\Utilization Percentage`. Örnekler luid+engtype'a göre toplanır, en büyüğü alınır
  (Görev Yöneticisi mantığı).
- VRAM: `\GPU Adapter Memory(*)\Dedicated Usage`. Toplam VRAM registry'den okunur
  (`HardwareInformation.qwMemorySize`, görüntü sınıfı anahtarı).
- Sıcaklık: LibreHardwareMonitor gerekli. Options → Remote Web Server → Run (port 8085), "Run On Windows Startup"
  ve "Start Minimized" açık olmalı. LHM yönetici olarak çalışır. Kapalıysa kartlarda "—" görünür.
  CPU için tercih sırası: package > tctl > tdie > core average. GPU için: gpu core > core > edge.
- ⚠ PDH/ctypes kodu Linux'ta sahte veriyle test edildi, Windows'ta ilk çalıştırmada doğrulanmalı.
  Değer gelmezse log'da "PDH sayacı eklenemedi" satırını ara.
