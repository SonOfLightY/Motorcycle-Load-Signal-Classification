<div align="center">

# Motorcycle Classification Based on Dynamic Load Signals

## Motorcycle Classification System Based on Dynamic Load Signals Using Decision Tree for One-Gate Parking Monitoring

### Undergraduate Thesis Project  
Computer Engineering — Faculty of Computer Science  
Brawijaya University

<br>

![Status](https://img.shields.io/badge/status-completed-brightgreen)
![Platform](https://img.shields.io/badge/platform-ESP32--S3-blue)
![Sensor](https://img.shields.io/badge/sensor-load%20cell%20%7C%20ultrasonic-orange)
![Model](https://img.shields.io/badge/model-Decision%20Tree-purple)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

<br>

[Versi Indonesia](README.md)

</div>

---

## Project Overview

This project was developed as a continuation of my internship project at the Directorate of Information Technology, Universitas Brawijaya (DTI UB). The project was motivated by a parking monitoring problem within the Universitas Brawijaya campus area, especially related to the mismatch between displayed parking capacity information and the actual condition in the field.

In some situations, parking areas that are already full may still appear to have available capacity, causing students to spend more time searching for a parking space. On the other hand, parking areas that still have available spaces may appear to be full, resulting in less effective use of parking facilities.

To address this problem, this project develops a one-gate parking monitoring prototype that classifies passing objects as either motorcycles or non-motor objects. The system uses dynamic load signals from load cell sensors, ultrasonic sensors to support direction detection, and a Decision Tree method for the classification process.

The classification and direction detection results are then used to automatically update parking capacity information and display it on a P10 LED panel.

---

## Research Title

**Sistem Klasifikasi Sepeda Motor Berbasis Sinyal Beban Dinamis Menggunakan Metode Decision Tree pada Monitoring Parkir Satu Gerbang**

English interpretation:

**Motorcycle Classification System Based on Dynamic Load Signals Using the Decision Tree Method for One-Gate Parking Monitoring**

---

## Background

Parking capacity monitoring is an important part of parking area management, especially in a campus environment with high student mobility. Inaccurate parking capacity information may cause users to spend unnecessary time searching for parking spaces or leave available parking areas underutilized.

This project uses a one-gate monitoring approach. Objects passing through the gate are classified based on dynamic load signal patterns captured by load cell sensors. With this approach, the system does not only detect whether an object passes through the measurement area, but also determines whether the object is a motorcycle or not.

This classification is important because not every object passing through the measurement area should affect motorcycle parking capacity. Therefore, the system is designed so that parking capacity is updated only based on relevant objects and their movement direction.

---

## Project Objectives

The objective of this project is to build a prototype system capable of:

- reading dynamic load signals from passing objects,
- classifying objects as motorcycles or non-motor objects,
- detecting object movement direction,
- updating parking capacity automatically,
- displaying parking capacity information on a P10 LED panel.

---

## Key Features

- Dynamic load signal acquisition using load cell sensors
- Load cell reading using HX711 modules
- Baseline validation and passing-object event detection
- Feature extraction from raw load cell readings
- Motorcycle and non-motor object classification using Decision Tree
- Real-time classification rule implementation on ESP32-S3
- Direction detection using two ultrasonic sensors
- Parking capacity update using ESP-NOW communication
- Parking capacity display using a P10 LED panel

---

## System Architecture

![Arsitektur Sistem](media/system-architecture.jpeg)

The system consists of an ESP32-S3 as the main controller, load cell sensors, HX711 modules, ultrasonic sensors, ESP-NOW communication, an ESP32 receiver, and a P10 LED panel as the display unit.

```text
Passing Object
      ↓
Load Cell Sensors + HX711
      ↓
ESP32-S3
      ↓
Baseline Validation + Event Detection
      ↓
Feature Extraction
      ↓
Decision Tree Classification
      ↓
Direction Detection
      ↓
Parking Capacity Update
      ↓
ESP-NOW Data Transmission
      ↓
ESP32 Receiver + P10 LED Display
```

---

## System Workflow

In general, the system works through the following stages:

1. An object passes over the measurement platform.
2. The load cell sensors read load changes as raw values.
3. The system compares sensor readings against the baseline.
4. When the signal change exceeds the threshold, the system detects a passing-object event.
5. The event data is used to generate signal features.
6. The extracted features are processed using Decision Tree rules.
7. The system determines whether the object is a motorcycle or a non-motor object.
8. Ultrasonic sensors support movement direction detection.
9. Parking capacity is updated based on the classification and direction results.
10. The updated capacity information is sent to the ESP32 receiver and displayed on the P10 LED panel.

---

## Hardware Components

| Component | Function |
|---|---|
| ESP32-S3 | Main controller for sensor reading, data processing, and classification |
| ESP32 Receiver | Receiver unit for displaying parking capacity |
| Load Cell Sensors | Capture dynamic load changes from passing objects |
| HX711 Module | Amplifies and converts load cell signals into digital data |
| HC-SR04 Ultrasonic Sensors | Detect object presence and movement direction |
| P10 LED Display | Displays parking capacity information |
| Measurement Platform | Physical area where objects pass during sensor reading |

---

## Machine Learning Pipeline

![Alur Machine Learning](media/ml-pipeline.jpeg)

The Decision Tree model was trained using features extracted from dynamic load signal data.

```text
Raw Load Cell Data
      ↓
Baseline Validation
      ↓
Universal Threshold Determination
      ↓
Delta Raw Calculation
      ↓
Event Segmentation
      ↓
Feature Extraction
      ↓
Decision Tree Training
      ↓
Model Evaluation
      ↓
Rule Conversion to ESP32-S3
```

---

## Extracted Features

The following features are used to represent the characteristics of each dynamic load signal event:

| Feature | Description |
|---|---|
| mean_delta_raw | Average signal change during an event |
| max_delta_raw | Maximum signal change during an event |
| variance_delta_raw | Variance of the signal change |
| std_delta_raw | Standard deviation of the signal change |
| range_delta_raw | Difference between maximum and minimum signal values |
| duration_ms | Duration of the detected event in milliseconds |

---

## Evaluation Results

| Evaluation | Result |
|---|---:|
| Decision Tree model accuracy | 96.55% |
| Real-time classification accuracy | 91.82% |
| Direction detection accuracy | 97.27% |
| Parking capacity calculation accuracy | 89.09% |

The evaluation results show that the system is able to classify passing objects, detect movement direction, and update parking capacity automatically under the tested scenario.

---

## Documentation and Publication

Project documentation, presentation slides, system demo, and the published article can be accessed through the following links.

<p>
  <a href="https://canva.link/vgku0oqrcwyb0u5">
    <img src="https://img.shields.io/badge/Presentation%20Slides-Canva-00C4CC?style=for-the-badge&logo=canva" alt="Presentation Slides">
  </a>
</p>

<p>
  <a href="https://drive.google.com/drive/folders/1W88d7SP1vm2doo_kTv0_wtPjQow8c0Vc?usp=drive_link">
    <img src="https://img.shields.io/badge/System%20Demo-Google%20Drive-blue?style=for-the-badge&logo=googledrive" alt="System Demo">
  </a>
</p>

<p>
  <a href="https://j-ptiik.ub.ac.id/index.php/j-ptiik/article/view/16677">
    <img src="https://img.shields.io/badge/Published%20Article-J--PTIIK%20UB-red?style=for-the-badge" alt="Published Article">
  </a>
</p>

The published article is used as the main publicly accessible academic documentation. The full undergraduate thesis document is not included directly in this repository.

---

## Prototype Preview

![Tampilan Prototipe](media/prototype.jpeg)

This section can be used to show the prototype, including the measurement platform, sensor circuit, ESP32-S3, and P10 LED display.

---

## Repository Structure

```text
firmware/    ESP32-S3 and ESP32 receiver source code
ml/          Machine learning notebook, scripts, and model rules
hardware/    Wiring and schematic documentation
media/       Images, diagrams, and result visuals
data/        Sample dataset or extracted feature examples
```

---

## Planned Folder Contents

### firmware/

Contains microcontroller source code.

```text
esp32-s3-main/
esp32-receiver-led-p10/
```

### ml/

Contains data processing and machine learning files.

```text
notebooks/
scripts/
model/
```

### hardware/

Contains hardware documentation.

```text
wiring.md
schematic.png
```

### media/

Contains images and visual materials used in the README.

```text
prototype.jpg
system-architecture.png
ml-pipeline.png
results-summary.png
```

### data/

Contains sample dataset or extracted feature examples used for classification.

```text
sample/
```

---

## Dataset Note

The full dataset does not necessarily need to be published directly in this repository. To keep the documentation clean and avoid unnecessary raw testing files, this repository may only include sample data or extracted feature examples.

The sample data is used to show the feature format used in the classification process.

---

## Project Status

This project has been completed as an undergraduate thesis project.

Possible future improvements include:

- expanding the dataset,
- testing with more varied motorcycle and non-motor object scenarios,
- improving the mechanical platform design,
- integrating the system with a cloud-based monitoring dashboard,
- comparing the system with other classification methods,
- developing a web-based or application-based parking monitoring system.

---

## Author

**Zidan Fadil Yahya**  
Computer Engineering  
Faculty of Computer Science  
Universitas Brawijaya

---

## License

Source code in this repository is licensed under the MIT License.

The published article, presentation slides, images, and academic materials remain under the author's academic ownership. The full undergraduate thesis document is not published directly in this repository.
