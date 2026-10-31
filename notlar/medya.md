# Şu an çalan medya (SMTC, PowerShell)

(CLAUDE.md'den taşındı, 2026-10-31. Genel kurallar CLAUDE.md'de.)

## Şu an çalan medya (`modules/media.py`, `core/media.ps1`)
- Kaynak: Windows medya oturumu (SMTC: GlobalSystemMediaTransportControlsSessionManager). Spotify, tarayıcıdaki
  YouTube, Medya Oynatıcı ve VLC'nin hepsi buraya bilgi verir. Python'da WinRT için paket gerekeceği için
  `media.ps1` sürekli çalışan bir Windows PowerShell 5.1 süreci olarak çalışıyor: 1,5 sn'de bir stdout'a JSON
  satırı yazar (title, artist, album, app=SourceAppUserModelId, status, pos, dur, cover sürümü). Çökerse
  `_reader` 5 sn'den 120 sn'ye kadar artan beklemeyle yeniden başlatır.
- Kapak (`Thumbnail` → `AsStreamForRead`) kullanıcının `%LOCALAPPDATA%\PC_Kumanda\cover.img` dosyasına yazılır.
  Şarkı değişince 6 deneme yapılır (Spotify kapağı geç yayınlıyor). `/media/cover?v=<sürüm>` adresinden sunulur
  (`@route`, PIN yok).
- Kontroller: Windows medya tuşları (`keybd_event`, VK 0xB3 oynat-durdur, 0xB0 sonraki, 0xB1 önceki).
  Hangi uygulama çalıyorsa ona gider.
- Arayüz: skorun solunda yuvarlak kutu (kapak, çalarken ekolayzer animasyonu, şarkı adı ve sanatçı). Dokununca
  medya paneli açılır: büyük kapak, segmentli ilerleme çubuğu (saniyede bir yerelde ilerler), önceki /
  oynat-durdur / sonraki. Medya ve skor birlikte görünürken durum etiketleri gizlenir. 760 px'ten dar ekranda
  kutuda sadece kapak kalır.
- ⚠ PowerShell/WinRT kısmı Windows'ta test edilmedi (Linux'ta sahte veriyle sadece arayüz test edildi).
  Çalışmazsa log'da "medya okunamadı" ya da "medya süreci durdu" satırına bak.
- CSS tuzağı: `.main` ana içerik alanının sınıfı. Başka bir öğeye `main` sınıfı verme (oynat düğmesi uzamıştı).
