# Üçüncü taraf bildirimleri / Third-party notices

Panel TR, aşağıdaki açık kaynak bileşenleri **paketin içine koymaz**; kullanıcı bunları `pip` ya da kendi paket
yöneticisiyle kurar. Panel TR does not bundle these; the user installs them.

| Bileşen / Component | Lisans / Licence | Nasıl kullanılıyor / How it is used |
|---|---|---|
| PyYAML | MIT | persona ve config dosyalarını okumak |
| Pillow | MIT-CMU (HPND) | iletişim sayfaları, ekran görüntüsü dilimleri, grafikler |
| Playwright for Python | Apache-2.0 | site modu, sadece Firefox ya da WebKit tarayıcı |
| FFmpeg / ffprobe | LGPL-2.1+ / GPL (derlemeye göre) | video karelerini çıkarmak; ayrı bir komut olarak çağrılır |
| faster-whisper (isteğe bağlı) | MIT | konuşma transkripti |
| openai-whisper (isteğe bağlı) | MIT | konuşma transkripti |

Kaynak özetleri (`sources/`): kamuya açık yayınlardan (TÜİK haberleri, DataReportal, NapoleonCat, Click Analytic,
Socialinsider, Hunter, Resmî Gazete metinleri, Armut/Bionluk/ajans fiyat sayfaları vb.) kısa, kendi cümlelerimizle
yazılmış özetler ve kısa alıntılardır; her satırda kaynak bağlantısı vardır. Bu yayınların hakları sahiplerine aittir.
`sources/YG_yerel_gozlem.md` kendi gözlemlerimizdir; işletme adları anonimleştirilmiştir.

Örnek koşudaki "Mavi Kozalak Kahve" kurgusaldır; gerçek bir işletmeyle ilgisi yoktur. Videosu Pillow ile çizilmiştir.
