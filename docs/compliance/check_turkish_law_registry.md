# Türk Mevzuatı HSSE – Kontrol ve Otomatik Kayıt Talimatı

**Tablo formatı:** `MevzuatNo | MevzuatTur | MevzuatTertip | MevzuatAdi`
**Kaynak:** yalnızca `mevzuat.gov.tr` resmi sayfaları.

---

## 1) Bağlantı Kuralı

Her satır için otomatik olarak şu kalıp kullanılır:

```
https://www.mevzuat.gov.tr/mevzuat?MevzuatNo={MevzuatNo}&MevzuatTur={MevzuatTur}&MevzuatTertip={MevzuatTertip}
```

> **MevzuatTur kodları:** Kanun=1, Yönetmelik=7, Tebliğ=9 (yalnız sayı).

---

## 2) Otomatik Veri Çekme / Kayıt (Registry)

### Üst düzey meta (başlık, RG tarihi/sayısı vb.):

```bash
python scripts/tools/update_turkish_regulations.py
```

### Tüm metin + maddeler (MADDE/paragraf/bent) ile **tam içerik**:

```bash
python scripts/tools/update_turkish_regulations.py --full
```

Seçili MevzuatNo’lar için:

```bash
python scripts/tools/update_turkish_regulations.py --only 6331 18928 --full
```

Çıktı (varsayılan): `.docs/compliance/turkish_regulations.json`
Farklı konuma yazdırmak için:

```bash
python scripts/tools/update_turkish_regulations.py --output "H:/Downloads/turkish_regulations.json" --full
```

---

## 3) JSON Şeması (özet)

```jsonc
{
    "last_run": "2025-11-11T11:22:33Z",
    "registry_size": 36,
    "search_index": {
        "18782-9-5::MADDE 8/5-a": {
            "key": "18782-9-5",
            "ref": "MADDE 8/5-a",
            "text": "Bir çalışan temsilcisi görevlendirilecekse en çok üyeye sahip yetkili sendika temsilcisi çalışan temsilcisi olarak atanır."
        }
    },
    "items": {
        "18782-9-5": {
            "mevzuat_no": "18782",
            "mevzuat_tur": "9",
            "mevzuat_tertip": "5",
            "mevzuat_adi": "…",
            "url": "https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=18782&MevzuatTur=9&MevzuatTertip=5",
            "final_url": "…",
            "status": "ok",
            "content_hash": "sha256:…",
            "last_checked": "ISO-8601 UTC",
            "last_changed": "ISO-8601 UTC",
            "meta": { "title": "…", "RG Tarih": "…", "RG Sayı": "…" },
            "maddeler": [
                {
                    "madde_no": "8",
                    "baslik": "…",
                    "paragraflar": [
                        {
                            "no": "5",
                            "metin": "… (varsa, bentlerden önceki paragraf metni)",
                            "bentler": [
                                {
                                    "no": "a",
                                    "metin": "Bir çalışan temsilcisi görevlendirilecekse … atanır."
                                },
                                { "no": "b", "metin": "…" }
                            ]
                        }
                    ]
                }
            ]
        }
    }
}
```

> Not: HTML yapıları yıllara ve türlere göre değişebildiğinden çıkarım **heuristic**tir. Bent/harf tespitinde `a)`, `b)` vb. düzenli ifadeler kullanılır; bazı metinlerde paragraflar yalnızca `(1)`, `(2)` biçiminde olabilir.

---

## 4) İşletim Notları

-   **Kaynak kısıtı:** Yalnızca `mevzuat.gov.tr` adresine istek atılır.
-   **Hata yönetimi:** Erişilemeyen kayıtlar `status="error"` olarak saklanır; diğerleri işlenmeye devam eder.
-   **Performans:** Senkron istek, 30 sn zaman aşımı (`--timeout` ile değiştirilebilir).
-   **Tekrarlanabilirlik:** JSON atomik yazılır; bozuk dosyalar `.corrupt` olarak yedeklenir.
-   **Arama kolaylığı:** `search_index` altında düz anahtarlar ile (örn. `"18782-9-5::MADDE 8/5-a"`) ofline sorgu yapılabilir.

---

## 5) Giriş Tablosu (Örnek)

Aşağıdaki tablo, betiğin girişidir. Herhangi bir değişiklikten sonra yukarıdaki komutları yeniden çalıştırın.

| MevzuatNo | MevzuatTur | MevzuatTertip | MevzuatAdi                                                                                                              |
| --------: | ---------- | ------------: | ----------------------------------------------------------------------------------------------------------------------- |
|      2872 | 1          |             5 | Çevre Kanunu                                                                                                            |
|      1475 | 1          |             5 | İş Kanunu                                                                                                               |
|      4857 | 1          |             5 | İş Kanunu                                                                                                               |
|      6331 | 1          |             5 | İş Sağlığı ve Güvenliği Kanunu                                                                                          |
|      4734 | 1          |             5 | Kamu İhale Kanunu                                                                                                       |
|      4735 | 1          |             5 | Kamu İhale Sözleşmeleri Kanunu                                                                                          |
|      2918 | 1          |             5 | Karayolları Trafik Kanunu                                                                                               |
|      6098 | 1          |             5 | Türk Borçlar Kanunu                                                                                                     |
|      4708 | 1          |             5 | Yapı Denetimi Hakkında Kanun                                                                                            |
|     12459 | 7          |             5 | Alt İşverenlik Yönetmeliği                                                                                              |
|     17050 | 7          |             5 | Asbestle Çalışmalarda Sağlık ve Güvenlik Önlemleri Hakkında Yönetmelik                                                  |
| 200712937 | 7          |             5 | Binaların Yangından Korunması Hakkında Yönetmelik                                                                       |
|     18647 | 7          |             5 | Çalışanların Gürültü ile İlgili Risklerden Korunmaları Hakkında Yönetmelik                                              |
|     18371 | 7          |             5 | Çalışanların İş Sağlığı ve Güvenliği Eğitimlerinin Usul ve Esasları Hakkında Yönetmelik                                 |
|     18335 | 7          |             5 | Çalışanların Patlayıcı Ortamların Tehlikelerinden Korunması Hakkında Yönetmelik                                         |
|     39291 | 7          |             5 | Çalışanların Sağlık Gözetimine Yönelik Tıbbi Tetkiklerin Usul ve Esasları Hakkında Yönetmelik                           |
|      5457 | 7          |             5 | Çocuk ve Genç İşçilerin Çalıştırılma Usul ve Esasları Hakkında Yönetmelik                                               |
|  20168375 | 7          |             5 | Geçici Koruma Sağlanan Yabancıların Çalışma İzinlerine Dair Yönetmelik                                                  |
|     18763 | 7          |             5 | Geçici veya Belirli Süreli İşlerde İş Sağlığı ve Güvenliği Hakkında Yönetmelik                                          |
|     18552 | 7          |             5 | Hijyen Eğitimi Yönetmeliği                                                                                              |
|     20992 | 7          |             5 | İlkyardım Yönetmeliği                                                                                                   |
|     18318 | 7          |             5 | İş Ekipmanlarının Kullanımında Sağlık ve Güvenlik Şartları Yönetmeliği                                                  |
|    169238 | 7          |             5 | İş Güvenliği Uzmanlarının Görev, Yetki, Sorumluluk ve Eğitimleri Hakkında Yönetmelik                                    |
|     17031 | 7          |             5 | İş Sağlığı ve Güvenliği Kurulları Hakkında Yönetmelik                                                                   |
|     16925 | 7          |             5 | İş Sağlığı ve Güvenliği Risk Değerlendirmesi Yönetmeliği                                                                |
|     18493 | 7          |             5 | İşyerlerinde Acil Durumlar Hakkında Yönetmelik                                                                          |
|     17253 | 7          |             5 | İşyerlerinde İşin Durdurulmasına Dair Yönetmelik                                                                        |
|     20857 | 7          |             5 | İşyerlerinde İşveren veya İşveren Vekili Tarafından Yürütülecek İş Sağlığı ve Güvenliği Hizmetlerine İlişkin Yönetmelik |
|     18592 | 7          |             5 | İşyeri Bina ve Eklentilerinde Alınacak Sağlık ve Güvenlik Önlemlerine İlişkin Yönetmelik                                |
|     18615 | 7          |             5 | İşyeri Hekimi ve Diğer Sağlık Personelinin Görev, Yetki, Sorumluluk ve Eğitimleri Hakkında Yönetmelik                   |
|     18695 | 7          |             5 | Kanserojen veya Mutajen Maddelerle Çalışmalarda Sağlık ve Güvenlik Önlemleri Hakkında Yönetmelik                        |
|     39898 | 7          |             5 | Kazı Destek Yapıları Hakkında Yönetmelik                                                                                |
|     18709 | 7          |             5 | Kimyasal Maddelerle Çalışmalarda Sağlık ve Güvenlik Önlemleri Hakkında Yönetmelik                                       |
|     18540 | 7          |             5 | Kişisel Koruyucu Donanımların İşyerlerinde Kullanılması Hakkında Yönetmelik                                             |
|     12907 | 7          |             5 | Makina Emniyeti Yönetmeliği                                                                                             |
|     18588 | 7          |             5 | Sağlık Kuralları Bakımından Günde Azami Yedi Buçuk Saat veya Daha Az Çalışılması Gereken İşler Hakkında Yönetmelik      |
|     18829 | 7          |             5 | Sağlık ve Güvenlik İşaretleri Yönetmeliği                                                                               |
|     31300 | 7          |             5 | Şantiye Şefleri Hakkında Yönetmelik                                                                                     |
|     18581 | 7          |             5 | Tehlikeli ve Çok Tehlikeli Sınıfta Yer Alan İşlerde Çalıştırılacakların Mesleki Eğitimlerine Dair Yönetmelik            |
|     18989 | 7          |             5 | Tozla Mücadele Yönetmeliği                                                                                              |
|     18928 | 7          |             5 | Yapı İşlerinde İş Sağlığı ve Güvenliği Yönetmeliği                                                                      |
|    187828 | 9          |             5 | İş Sağlığı ve Güvenliği ile İlgili Çalışan Temsilcisinin Nitelikleri ve Seçilme Usul ve Esaslarına İlişkin Tebliğ       |
