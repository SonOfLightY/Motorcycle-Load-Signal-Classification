<div align="center">

# Klasifikasi Sepeda Motor Berbasis Sinyal Beban Dinamis

## Sistem Klasifikasi Sepeda Motor Berbasis Sinyal Beban Dinamis Menggunakan Metode Decision Tree pada Monitoring Parkir Satu Gerbang

### Proyek Skripsi Sarjana  
Program Studi Teknik Komputer — Fakultas Ilmu Komputer  
Universitas Brawijaya

<br>

![Status](https://img.shields.io/badge/status-selesai-brightgreen)
![Platform](https://img.shields.io/badge/platform-ESP32--S3-blue)
![Sensor](https://img.shields.io/badge/sensor-load%20cell%20%7C%20ultrasonik-orange)
![Model](https://img.shields.io/badge/model-Decision%20Tree-purple)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

<br>

[English Version](README.en.md)

</div>

---

## Ringkasan Proyek

Proyek ini merupakan kelanjutan dari Proyek Kerja Lapangan di Direktorat Teknologi Informasi Universitas Brawijaya (DTI UB), yang berangkat dari permasalahan monitoring parkir di lingkungan Universitas Brawijaya.

Permasalahan utama yang diangkat adalah ketidaksesuaian informasi kapasitas parkir. Dalam beberapa kondisi, area parkir yang sebenarnya sudah penuh masih dapat dianggap tersedia, sehingga mahasiswa membuang waktu untuk mencari tempat parkir. Sebaliknya, area parkir yang masih memiliki ruang kosong dapat terlihat penuh, sehingga pemanfaatan lahan parkir menjadi kurang efektif.

Untuk menjawab permasalahan tersebut, proyek ini mengembangkan sistem klasifikasi sepeda motor dan objek non-motor pada skenario parkir satu gerbang. Sistem menggunakan sensor load cell untuk membaca perubahan beban saat objek melintas, sensor ultrasonik untuk mendukung deteksi arah, serta metode Decision Tree untuk proses klasifikasi.

Hasil klasifikasi dan deteksi arah digunakan untuk memperbarui informasi kapasitas parkir secara otomatis dan menampilkannya melalui LED P10.

---

## Judul Penelitian

**Sistem Klasifikasi Sepeda Motor Berbasis Sinyal Beban Dinamis Menggunakan Metode Decision Tree pada Monitoring Parkir Satu Gerbang**

---

## Latar Belakang Singkat

Sistem monitoring parkir menjadi penting karena informasi kapasitas parkir yang tidak akurat dapat mengganggu efektivitas penggunaan lahan parkir. Pada area kampus, kondisi ini dapat menyebabkan pengguna menghabiskan waktu lebih lama untuk mencari tempat parkir atau mengabaikan area parkir yang sebenarnya masih tersedia.

Pada penelitian ini, pendekatan yang digunakan adalah monitoring pada satu gerbang. Objek yang melintas diklasifikasikan sebagai sepeda motor atau non-motor berdasarkan pola sinyal beban dinamis dari sensor load cell. Dengan pendekatan ini, sistem dapat membantu memperbarui kapasitas parkir berdasarkan objek yang benar-benar masuk atau keluar dari area parkir.

---

## Tujuan Proyek

Tujuan dari proyek ini adalah membangun prototipe sistem yang mampu:

- membaca sinyal beban dinamis dari objek yang melintas,
- membedakan sepeda motor dan objek non-motor,
- mendeteksi arah pergerakan objek,
- memperbarui kapasitas parkir secara otomatis,
- menampilkan informasi kapasitas parkir melalui LED P10.

---

## Fitur Utama

- Akuisisi sinyal beban dinamis menggunakan sensor load cell
- Pembacaan sensor load cell menggunakan modul HX711
- Validasi baseline dan deteksi event objek melintas
- Ekstraksi fitur dari nilai raw sensor load cell
- Klasifikasi sepeda motor dan objek non-motor menggunakan Decision Tree
- Implementasi rule klasifikasi secara real-time pada ESP32-S3
- Deteksi arah pergerakan menggunakan dua sensor ultrasonik
- Pembaruan kapasitas parkir menggunakan komunikasi ESP-NOW
- Penampilan informasi kapasitas parkir pada LED P10

---

## Arsitektur Sistem

<!--
Tambahkan gambar arsitektur sistem di folder media dengan nama:
media/system-architecture.png

Setelah gambar tersedia, hapus komentar ini dan aktifkan baris di bawah.
-->

<!-- ![Arsitektur Sistem](media/system-architecture.png) -->

Sistem terdiri dari ESP32-S3 sebagai unit utama, sensor load cell, modul HX711, sensor ultrasonik, komunikasi ESP-NOW, ESP32 receiver, dan LED P10 sebagai media tampilan.

```text
Objek Melintas
      ↓
Sensor Load Cell + HX711
      ↓
ESP32-S3
      ↓
Validasi Baseline + Deteksi Event
      ↓
Ekstraksi Fitur
      ↓
Klasifikasi Decision Tree
      ↓
Deteksi Arah
      ↓
Pembaruan Kapasitas Parkir
      ↓
Pengiriman Data ESP-NOW
      ↓
ESP32 Receiver + LED P10
```

---

## Alur Kerja Sistem

Secara umum, sistem bekerja melalui beberapa tahapan berikut:

1. Objek melewati platform pengukuran.
2. Sensor load cell membaca perubahan beban dalam bentuk nilai raw.
3. Sistem membandingkan pembacaan sensor terhadap baseline.
4. Ketika perubahan nilai melewati threshold, sistem mendeteksi adanya event objek melintas.
5. Data event digunakan untuk menghasilkan fitur sinyal.
6. Fitur tersebut diproses menggunakan rule Decision Tree.
7. Sistem menentukan apakah objek termasuk sepeda motor atau non-motor.
8. Sensor ultrasonik membantu menentukan arah masuk atau keluar.
9. Kapasitas parkir diperbarui berdasarkan hasil klasifikasi dan arah.
10. Informasi kapasitas dikirim ke ESP32 receiver dan ditampilkan pada LED P10.

---

## Komponen Perangkat Keras

| Komponen | Fungsi |
|---|---|
| ESP32-S3 | Unit utama untuk pembacaan sensor, pemrosesan data, dan klasifikasi |
| ESP32 Receiver | Unit penerima data untuk menampilkan kapasitas parkir |
| Sensor Load Cell | Membaca perubahan beban dinamis dari objek yang melintas |
| Modul HX711 | Menguatkan dan mengubah sinyal load cell menjadi data digital |
| Sensor Ultrasonik HC-SR04 | Mendeteksi keberadaan dan arah pergerakan objek |
| LED P10 | Menampilkan informasi kapasitas parkir |
| Platform Pengukuran | Area lintasan objek saat proses pembacaan sensor |

---

## Alur Machine Learning

<!--
Tambahkan gambar alur machine learning di folder media dengan nama:
media/ml-pipeline.png

Setelah gambar tersedia, hapus komentar ini dan aktifkan baris di bawah.
-->

<!-- ![Alur Machine Learning](media/ml-pipeline.png) -->

Model Decision Tree dilatih menggunakan fitur yang diekstraksi dari sinyal beban dinamis.

```text
Data Raw Load Cell
      ↓
Validasi Baseline
      ↓
Penentuan Threshold Universal
      ↓
Perhitungan Delta Raw
      ↓
Segmentasi Event
      ↓
Ekstraksi Fitur
      ↓
Pelatihan Decision Tree
      ↓
Evaluasi Model
      ↓
Konversi Rule ke ESP32-S3
```

---

## Fitur yang Digunakan

Fitur berikut digunakan untuk merepresentasikan karakteristik sinyal beban dinamis pada setiap event:

| Fitur | Keterangan |
|---|---|
| mean_delta_raw | Rata-rata perubahan sinyal selama event |
| max_delta_raw | Nilai maksimum perubahan sinyal selama event |
| variance_delta_raw | Variansi perubahan sinyal |
| std_delta_raw | Standar deviasi perubahan sinyal |
| range_delta_raw | Selisih nilai maksimum dan minimum sinyal |
| duration_ms | Durasi event dalam satuan milidetik |

---

## Hasil Pengujian

| Pengujian | Hasil |
|---|---:|
| Akurasi model Decision Tree | 96,55% |
| Akurasi klasifikasi real-time | 91,82% |
| Akurasi deteksi arah | 97,27% |
| Akurasi perhitungan kapasitas parkir | 89,09% |

Hasil pengujian menunjukkan bahwa sistem dapat melakukan klasifikasi objek dan pembaruan kapasitas parkir secara otomatis pada skenario pengujian yang telah dilakukan.

---

## Dokumentasi dan Publikasi

Dokumen, slide presentasi, demo sistem, dan artikel publikasi dapat diakses melalui tautan berikut.

<p>
  <a href="https://canva.link/vgku0oqrcwyb0u5">
    <img src="https://img.shields.io/badge/Slide%20Presentasi-Canva-00C4CC?style=for-the-badge&logo=canva" alt="Slide Presentasi">
  </a>
</p>

<p>
  <a href="https://drive.google.com/drive/folders/1W88d7SP1vm2doo_kTv0_wtPjQow8c0Vc?usp=drive_link">
    <img src="https://img.shields.io/badge/Demo%20Sistem-Google%20Drive-blue?style=for-the-badge&logo=googledrive" alt="Demo Sistem">
  </a>
</p>

<p>
  <a href="https://j-ptiik.ub.ac.id/index.php/j-ptiik/article/view/16677">
    <img src="https://img.shields.io/badge/Artikel%20Jurnal-J--PTIIK%20UB-red?style=for-the-badge" alt="Artikel Jurnal">
  </a>
</p>

Dokumen skripsi lengkap tersedia pada:

```text
docs/skripsi-zidan-fadil-yahya.pdf
```

---

## Tampilan Prototipe

<!--
Tambahkan foto prototipe di folder media dengan nama:
media/prototype.jpg

Setelah gambar tersedia, hapus komentar ini dan aktifkan baris di bawah.
-->

<!-- ![Tampilan Prototipe](media/prototype.jpg) -->

Bagian ini dapat digunakan untuk menampilkan foto prototipe sistem, seperti platform pengukuran, rangkaian sensor, ESP32-S3, dan LED P10.

---

## Struktur Repositori

```text
docs/        Dokumen skripsi dan file presentasi
firmware/    Source code ESP32-S3 dan ESP32 receiver
ml/          Notebook, script, dan rule model machine learning
hardware/    Dokumentasi wiring dan skematik perangkat keras
media/       Gambar, diagram, dan visual hasil pengujian
data/        Contoh dataset
```

---

## Rencana Isi Folder

### docs/

Berisi dokumen akademik yang berkaitan dengan proyek.

```text
skripsi-zidan-fadil-yahya.pdf
presentation.pdf
```

### firmware/

Berisi source code untuk mikrokontroler.

```text
esp32-s3-main/
esp32-receiver-led-p10/
```

### ml/

Berisi proses pengolahan data dan machine learning.

```text
notebooks/
scripts/
model/
```

### hardware/

Berisi dokumentasi perangkat keras.

```text
wiring.md
schematic.png
```

### media/

Berisi gambar dan visual pendukung README.

```text
prototype.jpg
system-architecture.png
ml-pipeline.png
results-summary.png
```

### data/

Berisi contoh dataset atau contoh fitur yang digunakan pada proses klasifikasi.

```text
sample/
```

---

## Catatan Dataset

Dataset penuh tidak selalu perlu dipublikasikan secara langsung pada repositori ini. Untuk menjaga kerapian dokumentasi dan menghindari data yang tidak diperlukan, repositori ini dapat hanya menyertakan contoh data atau contoh hasil ekstraksi fitur.

Contoh data dapat digunakan untuk memperlihatkan format fitur yang dipakai dalam proses klasifikasi.

---

## Status Proyek

Proyek ini telah diselesaikan sebagai proyek skripsi sarjana.

Pengembangan lanjutan yang dapat dilakukan:

- Penambahan jumlah dataset
- Pengujian dengan variasi sepeda motor dan objek non-motor yang lebih banyak
- Perbaikan desain mekanik platform
- Integrasi dengan dashboard monitoring berbasis cloud
- Perbandingan dengan metode klasifikasi lain
- Pengembangan sistem monitoring berbasis web atau aplikasi

---

## Penulis

**Zidan Fadil Yahya**  
Program Studi Teknik Komputer  
Fakultas Ilmu Komputer  
Universitas Brawijaya

---

## Lisensi

Source code pada repositori ini menggunakan MIT License.

Dokumen skripsi, file presentasi, gambar, dan materi akademik tetap menjadi milik akademik penulis.
