---
name: panel-tr
description: Panel TR — Türkçe, kanıta dayalı sentetik odak grubu. Bir reels, web sitesi, gönderi ya da teklif yayımlanmadan önce onu Türk kullanıcı kartlarına (yaş bandı 18-24 … 55+, metropol / Anadolu / köy, yoğun / hafif Instagram, şüpheciler ve düşük teknolojili kişiler dahil; Pro'da ayrıca işletme sahibi ve pazarlama karar vericisi alıcılar) gösterir. Kişiler sadece gerçekten göreceklerini değerlendirir (reels için kareler + ekran yazıları, site için Firefox/WebKit ekran görüntüleri, gönderi için görseller) ve Türkçe cevap verir — ilk 3 saniyede durur mu, ne anlatıyor, güvenilirlik 1-5, DM / takip / satın alma, fiyat (alıcı), en büyük itiraz, tek somut düzeltme. Gruplar ayrı subagent'larda koşar, sayıları script sayar, rapor zorunlu bir dürüstlük kutusuyla biter. Use it as the last check before posting or delivering a reel, landing page, post or offer, for A/B choices (Pro), and when the user says "panel", "odak grubu", "kaçı alır", "test et", "farklı yaş gruplarına göster", "synthetic focus group".
---

# Panel TR (sentetik odak grubu)

**Ne işe yarar:** gerçek bir kitleden önce sorunları yakalamak — anlaşılmayan teklif, okunmayan küçük yazı,
ilk 3 saniyede kimseyi durdurmayan açılış, belli bir yaş grubunu iten bir şey. **Ne değildir:** satış tahmini
ya da pazar araştırması. Sayılar sentetik cevapların sayımıdır, asla "pazarın %'si" değildir.

Sürümler (`EDITION` dosyası): **Lite** = 10 izleyici kartı, tek seçenek, hazır hızlı rapor.
**Pro** = 30 izleyici + 24 alıcı kartı (10 segment), A/B modu, segment tabloları ve grafikleri, ayrı rapor yazarı.
Pro'ya özel adımlar aşağıda **(Pro)** diye işaretli; Lite'ta script bunları kibarca reddeder.

## Dosyalar

```
SKILL.md                    bu dosya
EDITION                     lite | pro
config.example.yaml         kopyala -> config.yaml (yollar, tarayıcı, taban oranlar); mutlak yol gerekmez
requirements.txt            PyYAML, Pillow, playwright (site modu için)
personas/viewers.yaml       izleyici kartları (Lite 10, Pro 30)
personas/buyers.yaml        alıcı kartları (sadece Pro, 24)
sources/index.yaml + *.md   kartların atıf yaptığı kamuya açık kaynak özetleri (TÜİK, DataReportal, ...)
prompts/persona_batch.md    bir grup subagent'ının talimatı (panel.py plan doldurur)
prompts/aggregator.md       (Pro) rapor yazarı talimatı (panel.py report-prompt doldurur)
scripts/make_stimulus.py    video/site/gönderi -> kareler, ekran görüntüleri, stimulus.md
scripts/panel.py            doctor | validate | cite | init-run | plan [--dry-run] | report-prompt (Pro)
scripts/aggregate.py        responses/*.json -> tablolar, grafikler, dürüstlük kontrolleri, hızlı rapor
examples/demo-kafe-reel/    kurgusal bir kafe reels'iyle uçtan uca örnek koşu
```

Aşağıda `S` = bu skill'in klasörü (genelde `~/.claude/skills/panel-tr`), `PY` = `python3` (tercihen
`S/.venv/bin/python`). Koşu klasörleri `config.yaml` içindeki `runs_dir` altına yazılır (varsayılan
`~/panel-tr-runs`).

## Adımlar

0. **İlk kurulumda / sorun olunca:** `PY S/scripts/panel.py doctor` (bağımlılıklar, ffmpeg, tarayıcı, sürüm).
   Kartlar değiştiyse: `PY S/scripts/panel.py validate` 0 hata demeli. `PY S/scripts/panel.py cite V07` bir
   kartı atıf yaptığı kaynak satırlarıyla yan yana basar.
1. **Koşu klasörü:** `RUN=$(PY S/scripts/panel.py init-run --slug kafe-reels-v2)` → `RUN/inputs/` şablonları.
2. **Girdileri yaz** (`RUN/inputs/`), nötr Türkçeyle, kendi incelemenden:
   - `context.txt` — kişi bunu nerede ve nasıl görüyor ("Reels akışında karşına çıkıyor; paylaşan hesap @x;
     açıklama metni var/yok"). Paylaşan hesabı sadece uygulamada görünecekse yaz. **Kimin yaptığını, neyi
     hedeflediğini ya da hangi sürümü tercih ettiğini asla yazma.**
   - `onscreen.txt` (video) — ekrandaki her yazı, zaman aralığıyla, ekranda göründüğü gibi.
   - `audio.txt` (video) — duyulanlar, olgu olarak: canlı ses ya da hangi parça, hangi saniyeden, konuşma/efekt
     var mı, görüntüyle uyumlu mu. Kişilere "BİZİM ANALİZİMİZ — sen duymadın" başlığıyla gösterilir.
   - `caption.txt` (gönderi/reels) — yayımlanacak açıklama metni, varsa.
3. **Uyaran** (her seçenek için bir tane; A/B = `stimulus_A`, `stimulus_B`):
   ```
   PY S/scripts/make_stimulus.py video IN.mp4 RUN/stimulus --onscreen RUN/inputs/onscreen.txt --audio RUN/inputs/audio.txt [--caption RUN/inputs/caption.txt] [--transcript]
   PY S/scripts/make_stimulus.py site https://ornek.com RUN/stimulus        # ya da yerel bir .html
   PY S/scripts/make_stimulus.py post a.jpg,b.jpg,c.jpg RUN/stimulus --caption RUN/inputs/caption.txt
   ```
   Video: 0,0/0,5/…/2,5 sn kareleri, sonra saniyede bir + son kare; `sheet_00_ilk3sn.jpg` ve her karenin altında
   zamanı yazan 2-3 numaralı sayfa; `--transcript` konuşma varsa (faster-whisper / openai-whisper kuruluysa)
   metni ekler. Site: Playwright **Firefox** (varsayılan) ya da **WebKit** — masaüstü 1440×900 ve mobil 390×844,
   ilk ekran + tüm sayfa iki ekranlık dilimler halinde, ayrıca görünür metin. **Chrome / Chromium / Chrome for
   Testing asla açılmaz.** Sayfaları kendin aç ve `onscreen.txt`'in karelerle uyduğunu kontrol et.
4. **Paneli planla:**
   ```
   PY S/scripts/panel.py plan --run RUN --panel viewer --n 10 --batches 2 --stimulus RUN/stimulus --context-file RUN/inputs/context.txt [--action "…"] [--seed 7] [--dry-run]
   PY S/scripts/panel.py plan --run RUN --panel viewer --n 30 --batches 6 …                                   (Pro)
   PY S/scripts/panel.py plan --run RUN --panel buyer --n 24 --batches 5 --segments kafe_restoran,emlak,… …   (Pro)
   PY S/scripts/panel.py plan … --stimulus-a RUN/stimulus_A --stimulus-b RUN/stimulus_B                     (Pro, A/B)
   ```
   Boyutlar: hızlı kontrol 10 kişi (2×5); tam kontrol (Pro) 30 izleyici (6×5) ve/veya 24 alıcı (5×~5).
   İzleyici seçimi Instagram Türkiye yaş dağılımına göre ağırlıklı (config: `viewer_age_weights`, kaynak
   NapoleonCat), her yaş bandından en az bir kişi; ~%20 "hedef dışı" kişi (`--out-share`); `--local İzmir`
   o şehirden kişileri öne alır; `--ids` ile elle seçilir. Her panelde en az bir şüpheci/hedef dışı kişi kalır.
   A/B (Pro): seçenekler "Seçenek 1/2" diye gösterilir; tek gruplar önce A'yı, çift gruplar önce B'yi görür;
   anahtar sadece `plan.json`'da durur, hiçbir prompt'ta yok.
   Varsayılan aksiyon sorusu uymuyorsa `--action` ile değiştir ("Bu reels'i görünce bu hafta sonu gider miydin?").
5. **Grupları koştur — her grup için ayrı, taze bir subagent, hepsi paralel.** Agent aracında
   general-purpose agent kullan, **fork değil** (fork bizim bağlamımızı ve beklentimizi taşır). Prompt:
   "Read `<RUN>/batches/batch_NN.md` and do exactly what it says. Write only the JSON file it names."
   Her subagent sadece kendi prompt dosyasını ve görselleri görür. Sonra her `RUN/responses/batch_NN.json`
   dosyasının var olduğunu kontrol et; başarısız grubu aynı prompt'la bir kez yeniden koştur.
6. **Say:** `PY S/scripts/aggregate.py RUN --title "…" [--real-people "…"]` → `RUN/data/panel_data.md`,
   `chart_aksiyon.png`, `chart_ilk3sn.png`, `all_answers.md` ve kontroller: şema, dayanak (gösterilmeyen bir
   kareye atıf = kişi bir şey uydurdu), kart yankısı (kişi kendi kartını tekrarladı), tek seslilik (grup içi vs
   gruplar arası kelime örtüşmesi). **Lite** burada `RUN/PANEL_REPORT.md` hızlı raporunu da yazar.
   **Pro** ayrıca her boyut için tablo ve segment grafikleri (`chart_aksiyon_<boyut>.png`) ve A/B tercihini yazar.
7. **(Pro) Rapor:** `PY S/scripts/panel.py report-prompt --run RUN --title "…" --real-people "…"` →
   `RUN/aggregator_prompt.md`. Bir taze subagent'a ver ("Read … and do it") → `RUN/PANEL_REPORT.md`
   (kümelenmiş itirazlar, öncelikli düzeltmeler, segment yorumu). Raporu `all_answers.md` ile karşılaştırarak oku
   (alıntılar gerçek, sayılar değişmemiş olmalı).
8. **Kullanıcıya söyle** (Türkçe): sayılarla 3-5 satır sonuç, ilk 3 düzeltme, dürüstlük kutusu cümlesi ve 3-5
   gerçek kişinin kim olması gerektiği. Panel kullanıcının ya da müşterinin zevkinin önüne geçmez.

## Kurallar

- **Önce kanıt.** Her kart özelliği `[ANAHTAR:Fnn]` (sources/ içindeki bir olgu satırı) ya da `[varsayım]` ile
  biter. `panel.py validate` her atfı kontrol eder. Bugün özelliklerin yaklaşık yarısı `[varsayım]` (kişilik ve
  zevk için kamuya açık ölçülmüş veri yok) — rapor bu oranı basar. Kendi araştırmanızı eklemek için
  `sources/` altına "Fnn ..." satırlı bir .md yazıp `sources/index.yaml`'a anahtarını ekleyin.
- **Kartlarda kurgu/pazarlama teorisi yok.** Kartlar kişi hakkında olgular taşır (iş, şehir, bütçe, alışkanlık),
  bizim görüşlerimizi değil ("ilk 2 saniye önemli" gibi). Yoksa panel kendi inançlarımızı bize geri söyler.
- **Bilerek çeşitlilik:** şüpheciler, fiyat hassaslar, düşük teknolojililer, köyde yaşayanlar, muhafazakârlar,
  Facebook ağırlıklı yaşlılar, hedef dışı kişiler kalır. Onların "hayır"ı hedefleme bilgisidir.
- **Sadece gösterileni değerlendir.** Kişiler kareleri, ekran görüntülerini, görselleri ve bizim yazdığımız
  yazı/ses olgularını görür. Videoyu izlemediler, sesi duymadılar; her cevap ≥ 2 kareye dayanır; değerlendiremediği
  şey `goremedigim` alanına gider. Ses her zaman "bizim analizimiz"dir, asla "duydum" değil.
- **Kör test:** context/onscreen/audio dosyalarında yapan, "bizim sürüm" ya da umulan cevap yok; A/B etiketleri
  nötr ve sıra dengeli.
- **Kibar değil, kalibre:** prompt gerçek bir taban oran taşır (config.yaml `calibration`; varsayılanlar
  Click Analytic / Socialinsider etkileşim oranları ve Hunter soğuk e-posta yanıt oranı, bkz. `sources/EB_*.md`).
  Kendi hesabınızın gerçek oranını biliyorsanız onu yazın. Çoğunluğun "DM atarım" dediği bir panel kırmızı
  bayraktır, başarı değil.
- **Bağımsız bağlamlar:** grup başına bir subagent; grup içinde her kişi sırayla, önceki kişinin cümlelerini
  kullanmadan yazılır. aggregate.py tek seslilik uyarısı verirse daha küçük gruplarla (3) tekrar koştur.
- **Sayıları script sayar, kelimeleri model yazar.** Rapor yazarı sayı uyduramaz, yeniden sayamaz.
- **Dürüstlük kutusu her raporda zorunlu:** sentetik ≠ pazar verisi; 3-5 gerçek kişiyle doğrula (ilk 3 sn'de
  durur muydun? tek cümleyle ne anlatıyor? sonra ne yapardın?).
- Cevaplar Türkçe ve kişinin kendi ağzından; alıntılarda Türkçe İ/ı korunur.
- Maliyet: grup başına ~6-8 görsel; 10 kişilik koşu ≈ 2 paralel subagent; 30 kişilik ≈ 6 subagent + 1 rapor yazarı.
  Taslaklar için hızlı kontrol (10), son hal için tam panel (Pro, 24-30).
- Gizlilik: koşu klasörleri yereldir; müşteri materyalini başka yere yüklemez. Paylaşmadan önce müşteri adı ve
  kişisel veri içeren girdileri temizleyin.

## Çıktı klasörü

```
RUN/inputs/{context,onscreen,audio,caption}.txt
RUN/stimulus[_A|_B]/{stimulus.md,stimulus.json,sheet_*.jpg,frames/|shots/|post/}
RUN/plan.json  RUN/batches/batch_NN.md  RUN/responses/batch_NN.json
RUN/data/{panel_data.md,panel_data.json,all_answers.md,chart_*.png}
RUN/PANEL_REPORT.md            (Lite: hızlı rapor; Pro: rapor yazarının raporu, hızlı rapor data/quick_report.md)
RUN/aggregator_prompt.md       (Pro)
```
