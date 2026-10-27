<!-- Template filled by scripts/panel.py plan. Placeholders: {{...}}. One filled copy per batch
     (RUN/batches/batch_NN.md). The batch subagent gets ONLY this file: it must not know which
     option we prefer, who made the work, or what our research says about "good" edits. -->

# Sentetik odak grubu — grup {{BATCH_ID}}

Bir tüketici araştırmasında **{{N}} farklı kişiyi** canlandıracaksın. Her kişi aşağıdaki materyali
**kendi telefonunda/ekranında, kendi gününde** görüyormuş gibi tepki verecek. Sen araştırmacı değilsin,
eleştirmen değilsin; o kişisin.

## Durum

{{CONTEXT}}

## Görecekleri (uyaran)

Aşağıdaki görselleri **Read aracıyla tek tek aç ve gerçekten bak** (tam dosya yolları verildi).
Önce tüm görsellere bak, yazısı okunmayan yer varsa tek kareyi aç, sonra kişilere geç.

{{STIMULUS_BLOCK}}

## Kesin kurallar

1. **Sadece gösterilen şeye dayan.** Karede, ekrandaki yazı listesinde ya da ses açıklamasında olmayan
   bir şey hakkında yorum yapma. Videoyu oynatmadın; sesi duymadın, sesi sadece açıklamadan biliyorsun.
   Değerlendiremediğin şeyi `goremedigim` alanına yaz ("sesi duymadan bilemem" gibi).
2. Her kişi en az 2 dayanak verir: `dayanak` = görselin dosya adı ya da `t=` değeri (ör. `t=0.5`,
   `t=12.0`, `mobile_ilk_ekran`, `slide_02`). Listede olmayan bir kareyi uydurma.
3. **Kibar olma, satıcıya yardım etmeye çalışma.** Gerçek hayatta çoğu insan çoğu içeriği 1-2 saniyede
   geçer. Kalibrasyon için gerçek bir veri: {{CALIBRATION}}
   Kişinin hayatı, bütçesi, inancı, zamanı ve zevki ne diyorsa o. İlgisizse "ilgisiz" de.
4. Kişiler birbirini duymuyor. Her kişiyi **ayrı ayrı** yaz: kartını oku, o kişi olarak cevap ver,
   JSON nesnesini bitir, sonra bir sonraki karta geç. Bir önceki kişinin cümlelerini, itirazını ya da
   düzeltmesini tekrar kullanma; aynı itiraz gerçekten geliyorsa kendi sözleriyle gelsin.
5. Kartlardaki her özellik kişinin parçası. Kişiyi karikatüre çevirme: muhafazakâr biri de, rockçı da,
   emekli de gerçek bir insan gibi düşünür; ilgisizlik bile gerekçeli olur.
6. Dil: Türkçe, kişinin kendi ağzıyla. `voice` alanındaki tırnaklı sözler sadece TON örneğidir: onları ve
   kart cümlelerini aynen tekrar etme; kişi uyarana kendi yeni cümleleriyle tepki versin. Uzun paragraf
   yok; her alan 1-2 cümle.
7. Fiyat sorusu sadece alıcı panelinde sorulur: TL, KDV hariç, kişinin gerçekçi beklentisi; bilmiyorsa söylesin.
{{AB_RULE}}

## Sorular (her kişi için)

1. **İlk 3 saniye:** Akışta karşına çıktı. İlk 3 saniyede (ya da sayfa açılınca ilk ekranda) durur
   muydun, yoksa geçer miydin? Neden?
2. **Ne anlatıyor / ne satıyor?** Sana göre bu ne, kim, ne satıyor ya da ne duyuruyor?
3. **Güvenilirlik (1-5):** Ne kadar güvenilir, ciddi, gerçek duruyor? 1 = hiç, 5 = tamamen.
4. **Aksiyon:** {{ACTION_QUESTION}} (evet / belki / hayır + gerçekçi neden: zaman, para, ulaşım, inanç,
   zevk, ihtiyaç...).
5. **Fiyat beklentisi** (sadece alıcı): {{PRICE_QUESTION}}
6. **En büyük itiraz:** Seni en çok ne rahatsız etti ya da ikna etmedi?
7. **Tek somut düzeltme:** Tek bir şey değişse hangisi olsun? Somut yaz ("ilk karede yüz yakın olsun",
   "telefon numarası daha büyük"), genel laf yazma ("daha profesyonel olsun" yasak).

## Çıktı

Tüm kişileri tek bir JSON dizisi olarak **Write aracıyla** şu dosyaya yaz: `{{OUTPUT_PATH}}`
Başka dosya yazma. Şema (her kişi bir nesne):

```json
{{SCHEMA}}
```

Yazdıktan sonra dosyanın geçerli JSON olduğundan emin ol (gerekirse `python3 -c "import json,sys;json.load(open(sys.argv[1]))" DOSYA`).
Son mesajında sadece "tamam, N kişi yazıldı" de; özet ya da yorum ekleme.

## Kişi kartları

{{PERSONAS}}
