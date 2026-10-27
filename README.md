# Panel TR — Türkçe sentetik odak grubu (Claude Code skill)

> **Pro sürümü yakında (henüz satışta değil).** Çıkınca haber almak için [Pro bekleme listesi](https://github.com/redirhan/redirhan/issues/1) konusuna 👍 bırakın ya da kısa bir yorum yazın.

Reels'inizi, açılış sayfanızı, gönderinizi ya da teklifinizi yayımlamadan önce **Türkiye'den 10-54 farklı
kişiye** gösterin: 19 yaşında Eskişehirli bir öğrenci, Ordu'da fındık bahçesinde çalışan bir genç, Facebook'u
Instagram'dan çok kullanan Denizlili bir esnaf, Gaziantepli iki çocuk annesi, fiyatı görmeden hiçbir şeye
inanmayan bir emekli… Her biri kendi ağzından söyler: **ilk 3 saniyede durur muyum, bu ne, ne kadar güvenilir,
ne yaparım, beni ne rahatsız etti, tek bir şey değişse ne olsun.**

Panel TR bir [Claude Code](https://docs.claude.com/en/docs/claude-code) skill'idir. Kişileri Claude'un
subagent'ları canlandırır; sayıları bir Python betiği sayar; rapor her zaman bir dürüstlük kutusuyla biter.

> ### Panel TR ne değildir
> - **Pazar araştırması ya da satış tahmini değildir.** Cevaplar bir dil modelinin kişi kartlarıyla canlandırdığı
>   **sentetik** cevaplardır. "10 kişiden 4'ü belki dedi" gerçek kitlenin %40'ı demek değildir.
> - Gerçek insanlarla görüşmenin yerini tutmaz; önüne geçmez. Rapor, kararı vermeden önce kime (3-5 gerçek
>   kişi) ne sormanız gerektiğini yazar.
> - Kişiler videoyu izlemez, sesi duymaz: sadece kareleri, ekran görüntülerini ve sizin yazdığınız ses
>   açıklamasını görür.
> - Kart özelliklerinin yaklaşık yarısı `[varsayım]` işaretlidir (kişilik ve zevk için kamuya açık ölçülmüş
>   veri yok). Yaş, cinsiyet, platform kullanımı, fiyatlar ve kurallar kaynaklıdır (TÜİK, DataReportal,
>   NapoleonCat, Click Analytic, Resmî Gazete…). Rapor bu oranı her seferinde basar.
>
> **Ne işe yarar:** gözden kaçan sorunları gerçek kitleden önce yakalamak — anlaşılmayan teklif, okunmayan
> küçük yazı, kimseyi durdurmayan açılış, belli bir yaş grubunu iten bir şey.

## Sürümler

| | **Lite** (ücretsiz, MIT) | **Pro** (ücretli, EULA) |
|---|---|---|
| İzleyici kartları | 10 (5 yaş bandı) | 30 (5 yaş bandı, 20+ il; metropol, Anadolu, ilçe/köy) |
| Alıcı kartları (işletme sahibi, pazarlamacı, ajans) | — | 24, 10 segment (kafe/restoran, bar/mekân, moda/perakende, emlak, spor salonu, etkinlik, içerik üreticisi, kurumsal pazarlama, ajans, e-ticaret) |
| Video / site / gönderi uyaranı | ✓ | ✓ |
| Hızlı rapor + 2 grafik | ✓ | ✓ |
| A/B testi (kör, sıra dengeli) | — | ✓ |
| Segment tabloları ve grafikleri (yaş, cinsiyet, şehir tipi, Instagram kullanımı, segment, teknoloji…) | — | ✓ |
| Rapor yazarı (kümelenmiş itirazlar, öncelikli düzeltmeler) | — | ✓ |
| Fiyat beklentisi sorusu (alıcı paneli) | — | ✓ |

## Gereksinimler

- [Claude Code](https://docs.claude.com/en/docs/claude-code) (subagent'lar ve görsel okuma için)
- macOS ya da Linux, Python 3.10+
- Video için `ffmpeg` (macOS: `brew install ffmpeg`, Debian/Ubuntu: `sudo apt install ffmpeg`)
- Web sitesi için Playwright + **Firefox** (ya da WebKit). Chrome/Chromium kullanılmaz.

## Kurulum

```bash
# 1) Skill klasörüne çıkarın
mkdir -p ~/.claude/skills
unzip panel-tr-lite-v1.0.zip -d ~/.claude/skills/        # ya da panel-tr-pro-v1.0.zip
cd ~/.claude/skills/panel-tr

# 2) Python ortamı
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install firefox             # sadece site modu için (WebKit: ... install webkit)

# 3) (İsteğe bağlı) ayarlar
cp config.example.yaml config.yaml                         # koşu klasörü, tarayıcı, taban oranlar

# 4) Kontrol
.venv/bin/python scripts/panel.py doctor
.venv/bin/python scripts/panel.py validate
```

Belirli bir projede kullanmak isterseniz klasörü o projenin `.claude/skills/panel-tr/` yoluna da koyabilirsiniz.

## Hızlı başlangıç

Claude Code'da şunu yazmanız yeterli:

> `~/Desktop/acilis_reels.mp4` dosyasını Panel TR'den geçir. Instagram Reels akışında görülecek, paylaşan hesap
> @kafem. Hızlı kontrol yeterli.

Claude skill'i yükler, ekrandaki yazıları ve sesi sizinle birlikte not eder, uyaranı hazırlar, 2 bağımsız subagent
ile 10 kişiyi koşturur, sayar ve `PANEL_REPORT.md` raporunu getirir. Elle yapmak isterseniz:

```bash
S=~/.claude/skills/panel-tr; PY=$S/.venv/bin/python
RUN=$($PY $S/scripts/panel.py init-run --slug acilis-reels)          # ~/panel-tr-runs/<tarih>_acilis-reels
# RUN/inputs/context.txt, onscreen.txt, audio.txt, caption.txt dosyalarını doldurun
$PY $S/scripts/make_stimulus.py video ~/Desktop/acilis_reels.mp4 $RUN/stimulus \
    --onscreen $RUN/inputs/onscreen.txt --audio $RUN/inputs/audio.txt --caption $RUN/inputs/caption.txt
$PY $S/scripts/panel.py plan --run $RUN --panel viewer --n 10 --batches 2 \
    --stimulus $RUN/stimulus --context-file $RUN/inputs/context.txt
# Claude Code'da her RUN/batches/batch_NN.md için ayrı bir general-purpose subagent:
#   "Read RUN/batches/batch_01.md and do exactly what it says. Write only the JSON file it names."
$PY $S/scripts/aggregate.py $RUN --title "Açılış reels'i v1"
```

Site için: `make_stimulus.py site https://ornek.com RUN/stimulus` (ya da yerel bir `.html`).
Gönderi için: `make_stimulus.py post a.jpg,b.jpg RUN/stimulus --caption caption.txt`.

## Örnek koşu (kurgusal)

`examples/demo-kafe-reel/` — uydurma bir kafe ("Mavi Kozalak Kahve", Eskişehir) için Pillow ile çizilmiş 12 saniyelik
sessiz bir açılış reels'i, Lite paneliyle (10 kişi, 2 grup) uçtan uca koşturuldu:

- İlk 3 saniyede duran: **0/10** · aksiyon evet **0** / belki **4** / hayır **6** · güvenilirlik ort. **2,8/5**
- En sık istek (10 kişiden 7'si, kendi sözleriyle): **çizim yerine gerçek görüntü** — mekânın içi, kahvenin
  dökülüşü, dükkânın önü ya da sahibinin yüzü ("çizimle güven gelmez", V16).
- Tek kişiden gelen ama somut bulgular: **fiyat yok** — "ikincisi bedava" ama ilki kaç lira? (V23), tarih kutusu
  küçük ve teklif süreli (V09), 6. saniyede **boş turuncu kutu** (V19), adres/saat satırları 55+ için **okunmuyor** (V27).
- Kontroller: 0 dayanak hatası (kimse gösterilmeyen bir kareden söz etmedi), gruplar tek sesli değil. Grup 2 bir
  kişi kartı düzeltildikten sonra taze bir subagent'la yeniden koşturuldu; toplamlar aynı kaldı (cümleler değişti).

Rapor: [`examples/demo-kafe-reel/PANEL_REPORT.md`](examples/demo-kafe-reel/PANEL_REPORT.md) ·
tüm cevaplar: `data/all_answers.md` · grafikler: `data/chart_aksiyon.png`, `data/chart_ilk3sn.png`.

## Kendi kitlenize uyarlama

- **Taban oran:** `config.yaml` → `calibration`. Kendi hesabınızın gerçek etkileşim oranını yazarsanız panel daha
  gerçekçi olur.
- **Yaş ağırlıkları:** `config.yaml` → `viewer_age_weights` (Instagram Insights'taki yaş dağılımınız).
- **Kendi kaynaklarınız ve kartlarınız:** `sources/` altına her satırı `Fnn ...` diye başlayan bir `.md` ekleyin,
  `sources/index.yaml`'a iki harfli anahtarını yazın, kartlarda `[ANAHTAR:Fnn]` diye atıf yapın; `panel.py validate`.
  Müşteri verisi kullanacaksanız onu kendi bilgisayarınızda tutun; paylaşılan bir pakete koymayın.

## SSS

**Bu, gerçek bir ankete göre ne kadar doğru?**
Doğruluk iddiası yok. Panel TR bir "ön eleme"dir: gerçek kişilere göstermeden önce bariz sorunları bulur. Kendi
denemelerimizde en faydalı çıktı sayılar değil, somut düzeltmeler oldu (okunmayan yazı, eksik fiyat, boş kare).

**Neden herkes "hayır" diyor?**
Prompt gerçek bir taban oran taşır: ortalama bir reels'te izleyenlerin çok azı bir şey yapar. Çoğunluğun "DM atarım"
dediği bir panel kırmızı bayraktır. Panel kibar olmak için değil, sorun bulmak için var.

**Claude aboneliğimden ne kadar harcar?**
10 kişilik hızlı kontrol ≈ 2 subagent, her biri ~6-8 görsel okur. 30 kişilik tam panel ≈ 6 subagent + 1 rapor yazarı.
Panel TR'nin kendisi hiçbir ücretli API çağırmaz.

**Verilerim bir yere gidiyor mu?**
Hayır. Betikler her şeyi yerel koşu klasörüne yazar. Görseller sadece sizin Claude Code oturumunuzun gördüğü
kadarıyla Claude'a gider.

**Neden Chrome değil?**
Site modu bilerek sadece Playwright'ın Firefox ya da WebKit tarayıcısını açar. Chrome/Chromium yolu yoktur.

**Windows'ta çalışır mı?**
macOS ve Linux'ta test edildi. Windows'ta WSL ile çalışması beklenir ama desteklenmiyor.

**Lite'tan Pro'ya geçince ne değişir?**
Aynı betikler; Pro paketinde 54 kart, A/B, segment grafikleri ve rapor yazarı açılır. Koşu klasörleriniz aynen kalır.

## Lisans

- **Lite:** MIT (`LICENSE`). Kartlar, kaynak özetleri ve betikler serbestçe kullanılabilir ve dağıtılabilir.
- **Pro:** ticari EULA (`LICENSE` = `EULA.md`): kişisel ve ajans kullanımı serbest, raporlar sizindir; skill
  dosyalarının yeniden satışı ve dağıtımı yasak.
- Üçüncü taraf bileşenler: `THIRD_PARTY_NOTICES.md`.

Redirhan Labs
