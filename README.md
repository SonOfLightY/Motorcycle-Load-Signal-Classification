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

Proyek ini dikembangkan sebagai kelanjutan dari Proyek Kerja Lapangan di Direktorat Teknologi Informasi Universitas Brawijaya (DTI UB). Latar belakang proyek ini berasal dari permasalahan monitoring parkir di lingkungan Universitas Brawijaya, khususnya terkait ketidaksesuaian informasi kapasitas parkir dengan kondisi sebenarnya di lapangan.

Dalam beberapa kondisi, area parkir yang sebenarnya sudah penuh masih dapat dianggap tersedia, sehingga mahasiswa perlu menghabiskan waktu lebih lama untuk mencari tempat parkir. Sebaliknya, area parkir yang masih memiliki ruang kosong dapat terlihat seolah-olah sudah penuh, sehingga pemanfaatan lahan parkir menjadi kurang efektif.

Untuk menjawab permasalahan tersebut, proyek ini mengembangkan prototipe sistem monitoring parkir satu gerbang yang mampu mengklasifikasikan objek yang melintas sebagai sepeda motor atau objek non-motor. Sistem memanfaatkan sinyal beban dinamis dari sensor load cell, sensor ultrasonik untuk mendukung deteksi arah, serta metode Decision Tree untuk proses klasifikasi.

Hasil klasifikasi dan deteksi arah kemudian digunakan untuk memperbarui informasi kapasitas parkir secara otomatis dan menampilkannya melalui LED P10.

---

## Judul Penelitian

**Sistem Klasifikasi Sepeda Motor Berbasis Sinyal Beban Dinamis Menggunakan Metode Decision Tree pada Monitoring Parkir Satu Gerbang**

---

## Latar Belakang Singkat

Monitoring kapasitas parkir merupakan salah satu bagian penting dalam pengelolaan area parkir, terutama pada lingkungan kampus dengan tingkat mobilitas mahasiswa yang tinggi. Informasi kapasitas parkir yang tidak akurat dapat menyebabkan pengguna membuang waktu untuk mencari ruang parkir, atau membuat area parkir yang masih tersedia menjadi tidak dimanfaatkan secara optimal.

Pendekatan yang digunakan pada proyek ini adalah monitoring pada satu gerbang. Objek yang melewati gerbang diklasifikasikan berdasarkan pola sinyal beban dinamis yang terbaca oleh sensor load cell. Dengan pendekatan ini, sistem tidak hanya mendeteksi adanya objek yang melintas, tetapi juga membedakan apakah objek tersebut termasuk sepeda motor atau bukan.

Klasifikasi tersebut penting karena tidak semua objek yang melintasi area pengukuran seharusnya memengaruhi kapasitas parkir sepeda motor. Oleh karena itu, sistem dirancang agar kapasitas parkir hanya diperbarui berdasarkan objek yang sesuai dan arah pergerakannya.

---

## Tujuan Proyek

Tujuan dari proyek ini adalah membangun prototipe sistem yang mampu:

- membaca sinyal beban dinamis dari objek yang melintas,
- mengklasifikasikan objek sebagai sepeda motor atau non-motor,
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

![Arsitektur Sistem](media/system-architecture.jpeg)

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

Secara umum, sistem bekerja melalui tahapan berikut:

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

![Alur Machine Learning](media/ml-pipeline.jpeg)

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

Hasil pengujian menunjukkan bahwa sistem dapat melakukan klasifikasi objek, mendeteksi arah pergerakan, dan memperbarui kapasitas parkir secara otomatis pada skenario pengujian yang telah dilakukan.

---

## Dokumentasi dan Publikasi

Dokumentasi proyek, slide presentasi, demo sistem, dan artikel publikasi dapat diakses melalui tautan berikut.

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

Artikel jurnal digunakan sebagai dokumentasi akademik utama yang dapat diakses secara publik. Dokumen skripsi lengkap tidak disertakan langsung pada repositori ini.

---

## Tampilan Prototipe

![Tampilan Prototipe](media/prototype.jpeg)

Bagian ini dapat digunakan untuk menampilkan foto prototipe sistem, seperti platform pengukuran, rangkaian sensor, ESP32-S3, dan LED P10.

---

## Struktur Repositori

```text
firmware/    Source code ESP32-S3 dan ESP32 receiver
ml/          Notebook, script, dan rule model machine learning
hardware/    Dokumentasi wiring dan skematik perangkat keras
media/       Gambar, diagram, dan visual hasil pengujian
data/        Contoh dataset atau contoh hasil ekstraksi fitur
```

---

## Rencana Isi Folder

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

Dataset penuh tidak selalu perlu dipublikasikan secara langsung pada repositori ini. Untuk menjaga kerapian dokumentasi dan menghindari data mentah yang tidak diperlukan, repositori ini dapat hanya menyertakan contoh data atau contoh hasil ekstraksi fitur.

Contoh data digunakan untuk memperlihatkan format fitur yang dipakai dalam proses klasifikasi.

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

Artikel jurnal, slide presentasi, gambar, dan materi akademik tetap menjadi milik akademik penulis. Dokumen skripsi lengkap tidak dipublikasikan langsung pada repositori ini.
