# Knowledge Corpus Yerleşimi

Bu dizin, regülasyon ve prosedür korpusunu RAG/CAG için normalize etmek amacıyla kullanılır. Her alt klasörde .md veya temiz .txt dosyalar, tercihen madde numarası/başlık ile saklanır.

## Alt Klasörler
- `regulations_tr/` — 6331 ve ilgili yönetmelikler (PPE, confined space, fall protection, vb. için alt başlıklar açılabilir).
- `ifc_ess/` — ESS1–ESS10 metinleri; ESS2/ESS4 OHS odaklı bölümler ayrı dosyalanabilir.
- `iso_standards/` — ISO 45001 (ve gerekirse ISO 14001) madde bazlı döküm.
- `procedures/` — SOP/SWP/PTW şablonları ve saha talimatları.

## Dosya Adlandırma
- `standard-clause--title.md` örn: `tr6331-17--training.md`, `osha-1910.146--confined-space.md`, `iso45001-8.1.3--ppe.md`, `ess2-2.2.1--ohs.md`.
- İçerikte başlık, madde numarası ve kaynak belirtin. UTF-8, düz metin/Markdown.

## Chunklama/Etiketleme İpuçları
- Başlık satırında standard/madde numarasını koruyun; RAG chunker başlıkları kaybetmemeli.
- Dosya sonuna `Tags:` satırı ekleyerek kategori/aktivite (ör. `Tags: ppe, excavation, training`) belirtilebilir.

## Hazırlık Akışı (öneri)
1. PDF/DOCX → düz metin/Markdown dönüştür (elle veya dış araç).
2. Madde başlıklarını hiyerarşik olarak koru.
3. Bu dizine kopyala; `git-lfs` kullanılmıyorsa metin harici büyük dosyaları ekleme.
4. `scripts/dev/docs_check.py` benzeri doğrulama araçlarıyla boş/bozuk dosyaları temizle.
