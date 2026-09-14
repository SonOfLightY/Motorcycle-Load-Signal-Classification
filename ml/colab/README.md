# Colab Pipeline

Folder ini berisi kode Google Colab yang digunakan untuk proses preprocessing data, ekstraksi fitur, pelatihan model Decision Tree, evaluasi model, dan visualisasi hasil pengujian.

Kode pada folder ini masih berbentuk pipeline eksperimen dari Google Colab, sehingga beberapa bagian masih menggunakan fungsi khusus Colab seperti upload dan download file.

## File

- `preprocessing-decision-tree-pipeline.py`

## Isi Pipeline

Pipeline ini mencakup beberapa tahap utama:

1. Pembacaan file CSV/XLSX dari hasil akuisisi data.
2. Pembersihan nilai numerik, termasuk format desimal Indonesia.
3. Normalisasi label motor dan non-motor.
4. Pembagian data menjadi data training dan testing.
5. Validasi baseline sensor load cell.
6. Penentuan global noise threshold.
7. Segmentasi event berdasarkan perubahan sinyal load cell.
8. Ekstraksi fitur sinyal beban dinamis.
9. Pelatihan model Decision Tree.
10. Evaluasi model menggunakan accuracy, confusion matrix, dan classification report.
11. Export rule Decision Tree untuk implementasi pada ESP32-S3.
12. Pembuatan visualisasi hasil pengujian.

## Catatan

File ini digunakan sebagai dokumentasi proses eksperimen dan pelatihan model. Untuk kebutuhan pengembangan lanjutan, pipeline ini dapat dipisahkan menjadi beberapa script modular.
