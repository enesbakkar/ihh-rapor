"""
İHH Haftalık Rapor Otomasyonu
- Playwright ile ihh.org.tr formunu doldurur ve gönderir
- Google Drive'a Google Doc olarak arşivler
"""

import os
import json
import time
import sys
from datetime import datetime, timedelta
import anthropic

# ── Payload okuma ──
def load_payload():
    payload_file = os.environ.get('PAYLOAD_FILE', '/tmp/payload.json')
    try:
        with open(payload_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if data:
            return data
    except Exception as e:
        print(f"Payload dosyası okunamadı: {e}")
    return {}

# ── Hafta etiketi ──
def get_week_label():
    now = datetime.now()
    # Bu haftanın Pazartesi - Pazar aralığı
    day_of_week = now.weekday()  # 0=Pazartesi
    monday = now - timedelta(days=day_of_week)
    sunday = monday + timedelta(days=6)
    fmt = lambda d: d.strftime('%d%m%y')
    return f"{fmt(monday)}-{fmt(sunday)}", monday, sunday

# ── Form doldur ve gönder ──
def fill_and_send_form(payload: dict, dry_run: bool = False):
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

    url = "https://ihh.org.tr/basvuru/istanbulgen%C3%A7ihhhaftal%C4%B1krapor"

    print("🌐 Tarayıcı başlatılıyor...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()

        print(f"📄 Form sayfası açılıyor: {url}")
        page.goto(url, wait_until='networkidle', timeout=30000)
        time.sleep(3)

        print("📝 Form alanları dolduruluyor...")

        # İsim Soyisim
        _fill_field(page, 'İsim Soyisim', payload.get('isim', 'Enes Bakkar'))

        # Birim
        _fill_field(page, 'Birim', payload.get('birim', 'ATOM'))

        # Güncel İcra Üyesi Sayısı
        _fill_field(page, 'Güncel İcra Üyesi Sayınız', str(payload.get('icra_sayi', '')))

        # Güncel Komisyon Üyesi Sayısı
        _fill_field(page, 'Güncel Komisyon Üyesi Sayınız', str(payload.get('komisyon_sayi', '')))

        # İlçe/Üniversite Karşılık Sayısı
        _fill_field(page, 'İlçe/Üniversite Karşılık Sayınız', str(payload.get('ilce_karsil', '')))

        # Haftalık İcra Toplantısı (select)
        icra_toplanti = payload.get('icra_toplanti', 'Yapılmadı')
        _select_option(page, icra_toplanti)

        # İcra toplantısına katılan kişi sayısı
        _fill_field(page, 'Haftalık icra toplantısına kaç kişi katıldı', str(payload.get('icra_katilim', '0')))

        # Sohbete katılan kişi sayısı
        _fill_field(page, 'Biriminizden Haftalık Sohbete Kaç Kişi Katıldı', str(payload.get('sohbet_katilim', '0')))

        # Sosyal faaliyet
        sosyal = payload.get('sosyal', 'Yapılmadı')
        _fill_field(page, 'Birim Olarak Sosyal Faaliyet Yapıldı mı', sosyal)

        # Eğitim çalışması
        egitim = payload.get('egitim', 'Yapılmadı')
        _fill_field(page, 'Birim Olarak Eğitim Çalışması Yapıldı mı', egitim)

        # İlçe/Üniversite Ziyareti
        _fill_field(page, 'İlçe/Üniversite Ziyareti Gerçekleştirildi mi', payload.get('ziyaret', 'Yapılmadı'))

        # Kuran eğitimi sayısı
        _fill_field(page, 'Kuran-ı Kerim Eğitimini Ekiplerimizden Kaç Kişi Yaptı', str(payload.get('kuran', '0')))

        # Bu haftaki çalışmalar
        _fill_field(page, 'Hafta İçerisinde Gerçekleştirdiğiniz Çalışmalarınızı Yazınız', payload.get('calisma', ''))

        # Stajyer çalışmaları - SABİT: Yok
        _fill_field(page, 'Biriminizdeki Stajyerin Hafta İçerisinde Gerçekleştirdiği Çalışmaları Yazınız', 'Yok')

        # Gelecek hafta planları
        _fill_field(page, 'Bir Sonraki Hafta İçerisinde Planladığınız Çalışmaları Yazınız', payload.get('planlama', ''))

        print("✅ Tüm alanlar dolduruldu")

        if dry_run:
            print("🧪 DRY RUN — form gönderilmedi")
            # Screenshot al
            page.screenshot(path='/tmp/form_preview.png', full_page=True)
            print("📸 Screenshot kaydedildi: /tmp/form_preview.png")
        else:
            # KVKK onayı
            try:
                kvkk = page.locator('input[type="checkbox"]').first
                if kvkk and not kvkk.is_checked():
                    kvkk.check()
                    print("✅ KVKK onayı işaretlendi")
            except Exception as e:
                print(f"KVKK checkbox: {e}")

            # Gönder butonu
            print("📤 Form gönderiliyor...")
            send_btn = page.locator('button:has-text("Gönder"), input[type="submit"], button[type="submit"]').first
            send_btn.click()
            time.sleep(5)

            # Başarı kontrolü
            page_text = page.inner_text('body')
            if any(word in page_text.lower() for word in ['teşekkür', 'başarı', 'gönderildi', 'alındı', 'iletildi']):
                print("🎉 Form başarıyla gönderildi!")
            else:
                print("⚠️ Form gönderildi ama başarı mesajı bulunamadı")
                page.screenshot(path='/tmp/form_result.png')

        browser.close()
        return True


def _fill_field(page, label_text: str, value: str):
    """Label text'e göre input/textarea bul ve doldur"""
    if not value:
        return
    try:
        # Önce textarea dene
        field = page.locator(f'textarea').filter(has=page.locator(f'[placeholder*="{label_text[:10]}"]')).first
        if not field.is_visible():
            raise Exception("not found")
        field.fill(value)
        return
    except:
        pass

    try:
        # Label ile bul
        field = page.get_by_label(label_text, exact=False)
        if field.count() > 0:
            field.first.fill(value)
            return
    except:
        pass

    try:
        # Placeholder ile bul
        field = page.get_by_placeholder(label_text[:15], exact=False)
        if field.count() > 0:
            field.first.fill(value)
            return
    except:
        pass

    print(f"  ⚠️ Alan bulunamadı: {label_text[:30]}")


def _select_option(page, value: str):
    """İcra toplantısı select dropdown"""
    try:
        select = page.locator('select').first
        option_map = {
            'Yüz yüze': 'Yüzyüze Yapıldı',
            'Çevirim içi': 'Online Yapıldı',
            'Yapılmadı': 'Yapılmadı'
        }
        mapped = option_map.get(value, value)
        select.select_option(label=mapped)
        print(f"  ✅ İcra toplantısı seçildi: {mapped}")
    except Exception as e:
        print(f"  ⚠️ Select hatası: {e}")


# ── Google Drive'a arşivle ──
def archive_to_drive(payload: dict, week_label: str, monday: datetime, sunday: datetime):
    import google.auth
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials

    service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '')
    folder_id = os.environ.get('GDRIVE_FOLDER_ID', '1t4mPCM-O5HExvKxUKyTez6OJhm0LBR7e')

    if not service_account_json:
        print("⚠️ Google Drive credentials bulunamadı, arşivleme atlandı")
        return

    print("📁 Google Drive'a arşivleniyor...")

    try:
        sa_info = json.loads(service_account_json)
        creds = Credentials.from_service_account_info(
            sa_info,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        service = build('drive', 'v3', credentials=creds)

        # Doküman içeriği (mevcut format ile aynı)
        fmt_date = lambda d: d.strftime('%d.%m.%y')
        doc_content = f"""ATOM

İstanbul Genç İHH  
Haftalık Birim Raporları

{week_label} {fmt_date(monday)} - {fmt_date(sunday)}

| | |
| :-: | :-: |
| Birim: | ATOM |
| İsim Soyisim: | Enes Bakkar |
| İcra Sayı: | {payload.get('icra_sayi', '')} |
| Komisyon Sayısı: | {payload.get('komisyon_sayi', '')} |
| İlçe/Üniversite Karşılık Sayınız: | {payload.get('ilce_karsil', '')} |
| Haftalık İcra: | {payload.get('icra_toplanti', '')} |
| İcra Katılım Sayısı: | {payload.get('icra_katilim', '0')} |
| Haftalık Sohbet Katılım Sayısı: | {payload.get('sohbet_katilim', '0')} |
| Sosyal Faaliyet Yapıldı mı? | {payload.get('sosyal', 'Yapılmadı')} |
| Eğitim Çalışması Yapıldı mı? | {payload.get('egitim', 'Yapılmadı')} |
| İlçe/Üniversite Ziyareti: | {payload.get('ziyaret', 'Yapılmadı')} |
| Kuran-ı Kerim Eğitimi Sayısı: | {payload.get('kuran', '0')} |
| Hafta İçerisindeki Çalışmalar: | {payload.get('calisma', '')} |
| Biriminizdeki Stajyerin Çalışmaları: | Yok |
| Haftaya Planlanan Çalışmalar: | {payload.get('planlama', '')} |
"""

        # Dosya adı
        fmt_short = lambda d: d.strftime('%d%m%y')
        file_title = f"{week_label} - {fmt_short(monday)}-{fmt_short(sunday)}"

        # Google Doc olarak oluştur
        file_metadata = {
            'name': file_title,
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [folder_id]
        }

        from googleapiclient.http import MediaInMemoryUpload
        media = MediaInMemoryUpload(
            doc_content.encode('utf-8'),
            mimetype='text/plain',
            resumable=False
        )

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink'
        ).execute()

        print(f"✅ Arşivlendi: {file.get('name')} → {file.get('webViewLink')}")
        return file

    except Exception as e:
        print(f"❌ Google Drive hatası: {e}")
        import traceback
        traceback.print_exc()
        return None


# ── Ana akış ──
def main():
    print("=" * 50)
    print("İHH ATOM Haftalık Rapor Otomasyonu")
    print(f"Zaman: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("=" * 50)

    dry_run = os.environ.get('DRY_RUN', 'false').lower() == 'true'
    if dry_run:
        print("🧪 DRY RUN modu aktif")

    # Payload yükle
    payload = load_payload()
    print(f"📦 Payload: {json.dumps(payload, ensure_ascii=False, indent=2)[:200]}...")

    # Hafta bilgisi
    week_label, monday, sunday = get_week_label()
    if not payload.get('week_label'):
        payload['week_label'] = week_label

    # Zorunlu alanlar kontrolü
    if not payload.get('calisma'):
        print("⚠️ 'calisma' alanı boş — rapor metni yok!")

    # Form doldur ve gönder
    try:
        success = fill_and_send_form(payload, dry_run=dry_run)
    except Exception as e:
        print(f"❌ Form gönderme hatası: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Drive'a arşivle
    if success and not dry_run:
        archive_to_drive(payload, payload.get('week_label', week_label), monday, sunday)

    print("\n✅ Tüm işlemler tamamlandı!")


if __name__ == '__main__':
    main()
