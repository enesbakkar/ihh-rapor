# İHH ATOM Haftalık Rapor Sistemi — Kurulum Rehberi

## Ne yaptık?

| Bileşen | Ne işe yarar |
|---|---|
| `pwa/index.html` | Telefonuna ana ekrana ekleyeceğin uygulama |
| `backend/send_report.py` | İHH formunu dolduran Python scripti |
| `.github/workflows/send-report.yml` | Her Pazar 21:00'da otomatik çalışan iş akışı |

---

## Adım 1: GitHub Repo Oluştur

```bash
# GitHub'da yeni repo: enesbakkar/ihh-rapor
# Public veya Private olabilir
```

Bu klasörü repo'ya push et:
```bash
git init
git add .
git commit -m "İHH ATOM Rapor Sistemi"
git remote add origin https://github.com/enesbakkar/ihh-rapor.git
git push -u origin main
```

---

## Adım 2: GitHub Secrets Ekle

GitHub repo → Settings → Secrets → Actions → New repository secret

### `ANTHROPIC_API_KEY`
claude.ai hesabından API key al:
https://console.anthropic.com/settings/keys

### `GDRIVE_FOLDER_ID`
```
1t4mPCM-O5HExvKxUKyTez6OJhm0LBR7e
```

### `GOOGLE_SERVICE_ACCOUNT_JSON`
1. https://console.cloud.google.com/ aç
2. Yeni proje oluştur: "ihh-rapor"
3. Google Drive API'yi etkinleştir
4. IAM & Admin → Service Accounts → Create Service Account
5. JSON key indir
6. Bu JSON'un **tüm içeriğini** secret olarak ekle
7. Drive klasörünü service account email ile paylaş (editor olarak)

---

## Adım 3: GitHub Actions PAT Token

PWA'dan GitHub Actions'ı tetiklemek için:
1. github.com → Settings → Developer Settings → Personal access tokens → Fine-grained
2. "ihh-rapor" repo için `actions: write` izni ver
3. Token'ı kopyala

`pwa/index.html` içinde şu satırı bul ve token'ı yaz:
```javascript
'Authorization': 'token GITHUB_PAT_PLACEHOLDER',
```
Şu şekilde değiştir:
```javascript
'Authorization': 'token github_pat_XXXXXXXXXXXXX',
```

---

## Adım 4: Cloudflare DNS — rapor.firnastechnologies.com

firnastechnologies.com'u GitHub Pages'e yönlendir:

### GitHub Pages Ayarı
1. Repo → Settings → Pages
2. Source: Deploy from branch → main → /pwa
3. Custom domain: `rapor.firnastechnologies.com`

### Cloudflare DNS
```
Type: CNAME
Name: rapor
Target: enesbakkar.github.io
Proxy: OFF (gri bulut)
```

---

## Adım 5: Telefona Ekle

1. Tarayıcıda `rapor.firnastechnologies.com` aç
2. Safari (iPhone): Alt menü → Paylaş → Ana Ekrana Ekle
3. Chrome (Android): Sağ üst menü → Ana Ekrana Ekle

Artık uygulama gibi açılır! 🎉

---

## Nasıl kullanırsın?

### Hafta içinde (anlık):
1. Uygulamayı aç
2. "Anlık Not Ekle" butonuna bas
3. Kategori seç (İcra, Sohbet, Ziyaret vb.)
4. Kısa not yaz → Ekle

### Pazar günü 20:45:
- Telefona bildirim gelir: "Rapor hazırlanıyor"
- Uygulamayı aç → Önizle sekmesi
- "AI ile Hazırla" → Claude notları resmi rapora çevirir
- Kontrol et, gerekirse düzenle
- "Gönder" → İHH formu otomatik dolar, Drive'a arşivlenir

### Sayılar sekmesi:
- İcra, komisyon, katılım sayılarını gir
- Bunlar haftalık değişir, her hafta güncelle

---

## Zamanlama

GitHub Actions her Pazar saat 18:00 UTC'de çalışır.
Bu, İstanbul saatiyle **21:00**'a denk gelir.

Sen "Gönder" butonuna basmadan da otomatik tetiklenebilir,
ama önizleme akışıyla sen onaylayarak gönderiyorsun.

---

## Sorun giderme

**Form gönderilmedi mi?**
GitHub → Actions sekmesinden log'lara bak.

**Drive'a arşivlenmiyor mu?**
Service account email'ini Drive klasörüne eklediğinden emin ol.

**Bildirim gelmiyor mu?**
Uygulama açıkken bir kez "İzin Ver" seçmen gerekiyor.
