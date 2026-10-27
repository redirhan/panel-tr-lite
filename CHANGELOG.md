# Değişiklik günlüğü / Changelog

## 1.0.0 — 2026-10-27

İlk satış sürümü. / First public release.

- Lite (ücretsiz, MIT): 10 izleyici kartı, tek seçenekli panel, hazır hızlı rapor (`PANEL_REPORT.md`) ve 2 grafik.
- Pro (ücretli, EULA): 30 izleyici + 24 alıcı kartı (10 segment), A/B modu (sıra dengeli, kör), her boyut için
  segment tabloları ve grafikleri, ayrı rapor yazarı prompt'u (kümelenmiş itirazlar, öncelikli düzeltmeler).
- Her kart özelliği `sources/` içindeki kamuya açık bir kaynağa (TÜİK, DataReportal, NapoleonCat, Click Analytic,
  Socialinsider, Hunter, Resmî Gazete, Armut/Bionluk fiyat sayfaları …) ya da `[varsayım]` etiketine bağlı;
  `panel.py validate` hepsini kontrol eder.
- Uyaran üretimi: video (ffmpeg kareleri + iletişim sayfaları), site (Playwright Firefox ya da WebKit; Chrome yok),
  gönderi (görseller + açıklama).
- Yollar ve taban oranlar `config.yaml` içinde; mutlak yol yok; macOS ve Linux.
- Dürüstlük kontrolleri: şema, dayanak (gösterilmeyen kareye atıf), kart yankısı, tek seslilik.
- `panel.py doctor`, `init-run`, `plan --dry-run` komutları.
- Örnek: kurgusal bir kafe reels'iyle uçtan uca Lite koşusu (`examples/demo-kafe-reel/`).
