# Kur.bat, otomatik başlatma, tek örnek, otomatik yeniden başlatma, log

(CLAUDE.md'den taşındı, 2026-10-31. Genel kurallar CLAUDE.md'de.)

## Otomatik başlatma (tüm kullanıcılar)
- `Kur.bat` → yönetici izni ister → `kurulum/kur.ps1`:
  - Python'u `sys.executable` ile bulur. Python `C:\Users\...` altında ya da Store'dan kurulmuşsa diğer
    kullanıcılar çalıştıramaz; bu durumda `winget ... --scope machine` ile Python 3.12'yi herkes için kurmayı önerir.
  - `C:\PC_Kumanda`'ya robocopy yapar (`__pycache__`, `logs`, `yerel`, `cache`, `*.csv`, `pc_kumanda_eski.py` hariç).
    Users grubuna (SID `S-1-5-32-545`, Türkçe adı farklı olduğu için SID kullanılıyor) değiştirme izni verir.
  - "PC Kumanda" zamanlanmış görevi: tetikleyici AtLogOn (10 sn gecikmeli), principal GroupId Users, Limited,
    süre sınırı yok, çökerse 5 kez yeniden dener. Her kullanıcı kendi oturumunda çalıştırır. Bu gerekli,
    çünkü varsayılan ses aygıtı kullanıcıya göre değişir.
  - Güvenlik duvarı: "PC Kumanda" kuralı, TCP `config.PORT`, `RemoteAddress LocalSubnet`, tüm profiller.
    Python için eski bir engelleme kuralı varsa uyarır.
  - Python yolunu `kurulum/python_yolu.txt` dosyasına yazar. Kur.bat bu dosyayı okuyup kumandayı bu
    oturum için yönetici olmadan başlatır.
- **Tek örnek:** Windows'ta `allow_reuse_address=False`. İkinci örnek portu alamaz, log'a yazıp çıkar.
  İki kullanıcı aynı anda açıksa (hızlı kullanıcı değiştirme) kumanda ilk oturum açanın oturumunu kontrol eder.
- **Otomatik yeniden başlatma (`core/reloader.py`, `config.AUTO_RELOAD`):** Kökteki, `core/` ve `modules/` içindeki
  `.py` dosyaları (`_` ile başlayanlar ve `pc_kumanda_eski.py` hariç) 2 sn'de bir izlenir. Değişiklik 2 sn sabit kalınca
  hepsi derlenir; sözdizimi hatası varsa yeniden başlatılmaz (log: "yeniden başlatılmadı"). Yoksa `@on_stop` kancaları
  çalışır (media.ps1 sürecini öldürür), aynı Python ile yeni süreç açılır (`PCK_RESTART=1` → `serve()` portu 10 sn
  boyunca tekrar dener), eski süreç soketi kapatıp `os._exit` ile çıkar. Sadece kendi klasörünü izler: geliştirme
  kopyasındaki değişiklik çalışan kopyaya yine Kur.bat ile gider. Windows'ta test edildi (2026-10-31).
- **Log:** pythonw'da konsol yok. Çıktı `%LOCALAPPDATA%\PC_Kumanda\kumanda.log` dosyasına gider (1 MB'ı geçince sıfırlanır).
  Sorun giderirken önce bu dosyayı iste.
