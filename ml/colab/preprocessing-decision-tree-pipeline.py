# -*- coding: utf-8 -*-

from google.colab import files
import pandas as pd
import numpy as np
import os
import io

uploaded = files.upload()

print("Jumlah file terupload:", len(uploaded))
for filename in uploaded.keys():
    print("-", filename)

def clean_numeric(series):

    return (
        series.astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .replace(["nan", "None", "", "NaN"], np.nan)
        .pipe(pd.to_numeric, errors="coerce")
    )

def read_uploaded_file(file_content, filename):

    if filename.lower().endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(file_content))
        df.columns = [str(col).strip().replace("\ufeff", "") for col in df.columns]
        return df

    text = None

    for enc in ["utf-8-sig", "utf-8", "latin1"]:
        try:
            text = file_content.decode(enc)
            break
        except Exception:
            pass

    if text is None:
        raise ValueError(f"File {filename} gagal dibaca encoding-nya.")

    lines = [line for line in text.splitlines() if line.strip() != ""]

    if len(lines) == 0:
        raise ValueError(f"File {filename} kosong.")

    header_index = None

    for i, line in enumerate(lines):
        clean_line = line.replace("\ufeff", "").strip()

        if "TIME" in clean_line and "CH1" in clean_line and "CH2" in clean_line:
            header_index = i
            break

    if header_index is None:
        raise ValueError(
            f"Header TIME, CH1, CH2 tidak ditemukan pada file {filename}"
        )

    cleaned_text = "\n".join(lines[header_index:])
    header = lines[header_index]

    if "\t" in header:
        sep = "\t"
    elif ";" in header:
        sep = ";"
    elif "," in header and header.count(",") >= 4:
        sep = ","
    else:
        sep = r"\s+"

    df = pd.read_csv(
        io.StringIO(cleaned_text),
        sep=sep,
        engine="python",
        on_bad_lines="skip"
    )

    df.columns = [str(col).strip().replace("\ufeff", "") for col in df.columns]

    return df

read_check_results = []

for filename, file_content in uploaded.items():
    if not (filename.lower().endswith(".csv") or filename.lower().endswith(".xlsx")):
        continue

    try:
        df_test = read_uploaded_file(file_content, filename)

        read_check_results.append({
            "filename": filename,
            "status": "ok",
            "columns": df_test.columns.tolist(),
            "row_count": len(df_test)
        })

    except Exception as e:
        read_check_results.append({
            "filename": filename,
            "status": "error",
            "error": str(e)
        })

read_check_df = pd.DataFrame(read_check_results)

print(read_check_df["status"].value_counts())
read_check_df[read_check_df["status"] == "error"]

def normalize_label(label):
    label = str(label).strip().lower()

    if label in ["motor", "mtr"]:
        return "motor"

    if label in [
        "non_motor",
        "nonmotor",
        "non motor",
        "non-motor",
        "manusia",
        "orang",
        "human"
    ]:
        return "non_motor"

    return label

def get_label_from_file(file_content, filename):
    try:
        df = read_uploaded_file(file_content, filename)
        df.columns = [str(col).strip().replace("\ufeff", "") for col in df.columns]

        if "CH5" in df.columns:
            label_series = df["CH5"].dropna().astype(str).str.strip()

            if len(label_series) > 0:
                label = label_series.iloc[0]
            else:
                label = "unknown"
        else:
            lower_name = filename.lower()

            if "non" in lower_name or "manusia" in lower_name or "orang" in lower_name:
                label = "non_motor"
            else:
                label = "motor"

        return normalize_label(label)

    except Exception as e:
        return "error"

file_records = []

for filename, file_content in uploaded.items():
    if not (filename.lower().endswith(".csv") or filename.lower().endswith(".xlsx")):
        continue

    label = get_label_from_file(file_content, filename)

    file_records.append({
        "filename": filename,
        "label": label
    })

file_df = pd.DataFrame(file_records)

print("Jumlah file terbaca:", len(file_df))
print(file_df["label"].value_counts())

file_df.head()

from sklearn.model_selection import train_test_split

print("Distribusi label sebelum split:")
print(file_df["label"].value_counts())

train_df, test_df = train_test_split(
    file_df,
    train_size=120,
    test_size=29,
    random_state=42,
    stratify=file_df["label"]
)

print("\nJumlah data training:", len(train_df))
print(train_df["label"].value_counts())

print("\nJumlah data testing:", len(test_df))
print(test_df["label"].value_counts())

output_file = "split_train_test_120_29.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    train_df.to_excel(writer, sheet_name="Train Files 120", index=False)
    test_df.to_excel(writer, sheet_name="Test Files 29", index=False)

    workbook = writer.book

    for sheet_name in ["Train Files 120", "Test Files 29"]:
        worksheet = writer.sheets[sheet_name]

        worksheet.freeze_panes = "A2"

        worksheet.auto_filter.ref = worksheet.dimensions

        worksheet.column_dimensions["A"].width = 35
        worksheet.column_dimensions["B"].width = 15

        for cell in worksheet[1]:
            cell.font = cell.font.copy(bold=True)
            cell.alignment = cell.alignment.copy(horizontal="center")

        for row in worksheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = cell.alignment.copy(vertical="center")

files.download(output_file)

def check_baseline_quality(
    file_content,
    filename,
    label,
    baseline_samples=10,
    zero_as_invalid=True,
    min_reasonable_raw=100000,
    max_baseline_std=5000
):

    df = read_uploaded_file(file_content, filename)
    df.columns = [str(col).strip().replace("\ufeff", "") for col in df.columns]

    if "CH2" not in df.columns:
        return {
            "filename": filename,
            "label": label,
            "status": "invalid",
            "reason": "CH2 tidak ditemukan"
        }

    df["CH2"] = clean_numeric(df["CH2"])
    df = df.dropna(subset=["CH2"]).reset_index(drop=True)

    if len(df) < baseline_samples:
        return {
            "filename": filename,
            "label": label,
            "status": "invalid",
            "reason": "data terlalu sedikit"
        }

    baseline_data = df["CH2"].tail(baseline_samples)

    baseline_mean = baseline_data.mean()
    baseline_std = baseline_data.std(ddof=0)
    baseline_min = baseline_data.min()
    baseline_max = baseline_data.max()

    reasons = []

    if zero_as_invalid and (baseline_data == 0).any():
        reasons.append("baseline mengandung nilai 0")

    if baseline_mean < min_reasonable_raw:
        reasons.append(f"baseline_mean terlalu kecil ({baseline_mean:.2f})")

    if baseline_std > max_baseline_std:
        reasons.append(f"baseline_std terlalu besar ({baseline_std:.2f})")

    status = "valid" if len(reasons) == 0 else "outlier"

    return {
        "filename": filename,
        "label": label,
        "status": status,
        "reason": "ok" if status == "valid" else " | ".join(reasons),
        "baseline_mean": baseline_mean,
        "baseline_std": baseline_std,
        "baseline_min": baseline_min,
        "baseline_max": baseline_max,
        "baseline_values": baseline_data.tolist()
    }

baseline_quality_results = []

for _, row in train_df.iterrows():
    filename = row["filename"]
    label = row["label"]

    try:
        result = check_baseline_quality(
            uploaded[filename],
            filename,
            label,
            baseline_samples=10,
            zero_as_invalid=True,
            min_reasonable_raw=100000,
            max_baseline_std=5000
        )

        baseline_quality_results.append(result)

    except Exception as e:
        baseline_quality_results.append({
            "filename": filename,
            "label": label,
            "status": "invalid",
            "reason": str(e)
        })

baseline_quality_df = pd.DataFrame(baseline_quality_results)

print("Ringkasan status baseline training:")
print(baseline_quality_df["status"].value_counts())

baseline_quality_df.head()

outlier_baseline_df = baseline_quality_df[
    baseline_quality_df["status"] != "valid"
].copy()

outlier_baseline_df[
    [
        "filename",
        "label",
        "status",
        "reason",
        "baseline_mean",
        "baseline_std",
        "baseline_min",
        "baseline_max"
    ]
]

valid_train_files = baseline_quality_df[
    baseline_quality_df["status"] == "valid"
]["filename"].tolist()

outlier_train_files = baseline_quality_df[
    baseline_quality_df["status"] != "valid"
]["filename"].tolist()

print("Jumlah training awal:", len(train_df))
print("Jumlah training valid:", len(valid_train_files))
print("Jumlah training outlier:", len(outlier_train_files))

print("\nDaftar training outlier:")
for f in outlier_train_files:
    print("-", f)

all_training_noise_clean = []
baseline_results_clean = []

for filename in valid_train_files:
    label = train_df.loc[train_df["filename"] == filename, "label"].iloc[0]

    df = read_uploaded_file(uploaded[filename], filename)
    df.columns = [str(col).strip().replace("\ufeff", "") for col in df.columns]

    df["CH2"] = clean_numeric(df["CH2"])
    df = df.dropna(subset=["CH2"]).reset_index(drop=True)

    baseline_data = df["CH2"].tail(10)

    baseline_mean = baseline_data.mean()
    baseline_std = baseline_data.std(ddof=0)
    baseline_min = baseline_data.min()
    baseline_max = baseline_data.max()

    noise_values = (baseline_data - baseline_mean).abs().tolist()
    all_training_noise_clean.extend(noise_values)

    baseline_results_clean.append({
        "filename": filename,
        "label": label,
        "baseline_mean": baseline_mean,
        "baseline_std": baseline_std,
        "baseline_min": baseline_min,
        "baseline_max": baseline_max
    })

baseline_train_clean_df = pd.DataFrame(baseline_results_clean)

print("Jumlah training valid:", len(valid_train_files))
print("Jumlah noise baseline valid:", len(all_training_noise_clean))

baseline_train_clean_df.head()

global_noise_p95_clean = np.percentile(all_training_noise_clean, 95)
global_noise_p99_clean = np.percentile(all_training_noise_clean, 99)

GLOBAL_NOISE_THRESHOLD = global_noise_p99_clean

print("Global Noise Threshold P95 clean:", global_noise_p95_clean)
print("Global Noise Threshold P99 clean:", global_noise_p99_clean)
print("GLOBAL_NOISE_THRESHOLD final:", GLOBAL_NOISE_THRESHOLD)

baseline_quality_df.to_csv("baseline_quality_check_training.csv", index=False)
baseline_train_clean_df.to_csv("baseline_training_clean.csv", index=False)

threshold_info_clean = pd.DataFrame([{
    "global_noise_p95_clean": global_noise_p95_clean,
    "global_noise_p99_clean": global_noise_p99_clean,
    "global_noise_threshold_used": GLOBAL_NOISE_THRESHOLD,
    "baseline_samples": 10,
    "training_total": len(train_df),
    "training_baseline_valid": len(valid_train_files),
    "training_baseline_outlier": len(outlier_train_files),
    "testing_total": len(test_df),
    "source": "valid training baseline only"
}])

threshold_info_clean.to_csv("global_threshold_clean.csv", index=False)

files.download("baseline_quality_check_training.csv")
files.download("baseline_training_clean.csv")
files.download("global_threshold_clean.csv")

threshold_info_clean

baseline_train_clean_df.sort_values("baseline_std", ascending=False).head(10)

baseline_quality_df.to_csv(
    "baseline_quality_check_training_excel.csv",
    index=False,
    sep=";",
    decimal=",",
    encoding="utf-8-sig"
)

baseline_train_clean_df.to_csv(
    "baseline_training_clean_excel.csv",
    index=False,
    sep=";",
    decimal=",",
    encoding="utf-8-sig"
)

threshold_info_clean.to_csv(
    "global_threshold_clean_excel.csv",
    index=False,
    sep=";",
    decimal=",",
    encoding="utf-8-sig"
)

files.download("baseline_quality_check_training_excel.csv")
files.download("baseline_training_clean_excel.csv")
files.download("global_threshold_clean_excel.csv")

with pd.ExcelWriter("laporan_preprocessing_baseline.xlsx", engine="openpyxl") as writer:
    baseline_quality_df.to_excel(
        writer,
        sheet_name="Baseline Quality",
        index=False
    )

    baseline_train_clean_df.to_excel(
        writer,
        sheet_name="Baseline Clean",
        index=False
    )

    threshold_info_clean.to_excel(
        writer,
        sheet_name="Global Threshold",
        index=False
    )

files.download("laporan_preprocessing_baseline.xlsx")

print("Jumlah training:", len(train_df))
print("Jumlah testing:", len(test_df))
print("Global threshold:", GLOBAL_NOISE_THRESHOLD)

print("\nTraining label:")
print(train_df["label"].value_counts())

print("\nTesting label:")
print(test_df["label"].value_counts())

def extract_event_features(
    file_content,
    filename,
    label,
    global_noise_threshold,
    baseline_samples=10,
    sigma_multiplier=3,
    padding_samples=0
):
    df = read_uploaded_file(file_content, filename)
    df.columns = [str(col).strip().replace("\ufeff", "") for col in df.columns]

    if "CH1" not in df.columns or "CH2" not in df.columns:
        raise ValueError(f"CH1 atau CH2 tidak ditemukan pada file {filename}")

    df["CH1"] = clean_numeric(df["CH1"])
    df["CH2"] = clean_numeric(df["CH2"])

    df = df.dropna(subset=["CH1", "CH2"]).reset_index(drop=True)

    if len(df) < baseline_samples + 3:
        raise ValueError(f"Data terlalu sedikit pada file {filename}")

    baseline_data = df["CH2"].tail(baseline_samples)

    baseline_mean = baseline_data.mean()
    baseline_std = baseline_data.std(ddof=0)

    threshold_event = max(
        sigma_multiplier * baseline_std,
        global_noise_threshold
    )

    df["raw_delta"] = df["CH2"] - baseline_mean
    df["raw_abs_delta"] = df["raw_delta"].abs()

    event_mask = df["raw_abs_delta"] > threshold_event

    if event_mask.sum() == 0:
        raise ValueError(
            f"Tidak ada event terdeteksi pada {filename}. "
            f"threshold_event={threshold_event:.2f}"
        )

    event_indices = df.index[event_mask].to_list()

    start_idx = max(min(event_indices) - padding_samples, 0)
    end_idx = min(max(event_indices) + padding_samples, len(df) - 1)

    event_df = df.loc[start_idx:end_idx].copy()

    signal = event_df["raw_abs_delta"]

    mean_delta_raw = signal.mean()
    max_delta_raw = signal.max()
    min_delta_raw = signal.min()
    variance_delta_raw = signal.var(ddof=0)
    std_delta_raw = signal.std(ddof=0)
    range_delta_raw = max_delta_raw - min_delta_raw

    duration_ms = event_df["CH1"].max() - event_df["CH1"].min()

    raw_original = event_df["CH2"]

    return {
        "filename": filename,
        "label": label,

        "baseline_mean": baseline_mean,
        "baseline_std": baseline_std,
        "global_noise_threshold": global_noise_threshold,
        "threshold_event": threshold_event,

        "event_start_index": start_idx,
        "event_end_index": end_idx,
        "event_sample_count": len(event_df),

        "mean_delta_raw": mean_delta_raw,
        "max_delta_raw": max_delta_raw,
        "min_delta_raw": min_delta_raw,
        "variance_delta_raw": variance_delta_raw,
        "std_delta_raw": std_delta_raw,
        "range_delta_raw": range_delta_raw,
        "duration_ms": duration_ms,

        "mean_raw_original_event": raw_original.mean(),
        "max_raw_original_event": raw_original.max(),
        "min_raw_original_event": raw_original.min(),
        "range_raw_original_event": raw_original.max() - raw_original.min()
    }

train_features = []
train_feature_errors = []

for filename in valid_train_files:
    try:
        label = train_df.loc[train_df["filename"] == filename, "label"].iloc[0]

        feature = extract_event_features(
            uploaded[filename],
            filename,
            label,
            global_noise_threshold=GLOBAL_NOISE_THRESHOLD,
            baseline_samples=10,
            sigma_multiplier=3,
            padding_samples=0
        )

        train_features.append(feature)
        print("Training berhasil:", filename)

    except Exception as e:
        train_feature_errors.append({
            "filename": filename,
            "error": str(e)
        })
        print("Training gagal:", filename, "|", e)

train_features_df = pd.DataFrame(train_features)
train_feature_errors_df = pd.DataFrame(train_feature_errors)

print("\nJumlah fitur training berhasil:", len(train_features_df))
print("Jumlah fitur training gagal:", len(train_feature_errors_df))

train_features_df.head()

test_features = []
test_feature_errors = []

for _, row in test_df.iterrows():
    filename = row["filename"]
    label = row["label"]

    try:
        feature = extract_event_features(
            uploaded[filename],
            filename,
            label,
            global_noise_threshold=GLOBAL_NOISE_THRESHOLD,
            baseline_samples=10,
            sigma_multiplier=3,
            padding_samples=0
        )

        test_features.append(feature)
        print("Testing berhasil:", filename)

    except Exception as e:
        test_feature_errors.append({
            "filename": filename,
            "label": label,
            "error": str(e)
        })
        print("Testing gagal:", filename, "|", e)

test_features_df = pd.DataFrame(test_features)
test_feature_errors_df = pd.DataFrame(test_feature_errors)

print("\nJumlah fitur testing berhasil:", len(test_features_df))
print("Jumlah fitur testing gagal:", len(test_feature_errors_df))

test_features_df.head()

train_features_df.to_csv("dataset_fitur_train.csv", index=False)
test_features_df.to_csv("dataset_fitur_test.csv", index=False)

files.download("dataset_fitur_train.csv")
files.download("dataset_fitur_test.csv")

train_export = train_features_df.copy()
test_export = test_features_df.copy()

for df in [train_export, test_export]:
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
    df[numeric_cols] = df[numeric_cols].round(2)

with pd.ExcelWriter("dataset_fitur_train_test_rapi.xlsx", engine="openpyxl") as writer:
    train_export.to_excel(writer, sheet_name="Train Features", index=False)
    test_export.to_excel(writer, sheet_name="Test Features", index=False)

    for sheet_name in ["Train Features", "Test Features"]:
        ws = writer.sheets[sheet_name]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                if cell.value is not None:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = min(max_length + 2, 25)

        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if isinstance(cell.value, (int, float)):
                    cell.number_format = '#,##0.00'

files.download("dataset_fitur_train_test_rapi.xlsx")

train_export = train_features_df.copy()
test_export = test_features_df.copy()

for df in [train_export, test_export]:
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
    df[numeric_cols] = df[numeric_cols].round(2)

with pd.ExcelWriter("dataset_fitur_train_test.xlsx", engine="openpyxl") as writer:
    train_export.to_excel(writer, sheet_name="Train Features", index=False)
    test_export.to_excel(writer, sheet_name="Test Features", index=False)

files.download("dataset_fitur_train_test.xlsx")

print("Distribusi fitur training:")
print(train_features_df["label"].value_counts())

print("\nDistribusi fitur testing:")
print(test_features_df["label"].value_counts())

feature_cols = [
    "mean_delta_raw",
    "max_delta_raw",
    "variance_delta_raw",
    "std_delta_raw",
    "range_delta_raw",
    "duration_ms"
]

train_features_df[feature_cols].describe()
test_features_df[feature_cols].describe()

from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

feature_cols = [
    "mean_delta_raw",
    "max_delta_raw",
    "variance_delta_raw",
    "std_delta_raw",
    "range_delta_raw",
    "duration_ms"
]

X_train = train_features_df[feature_cols]
y_train = train_features_df["label"]

X_test = test_features_df[feature_cols]
y_test = test_features_df["label"]

print("Jumlah data training:", len(X_train))
print("Jumlah data testing:", len(X_test))

print("\nDistribusi label training:")
print(y_train.value_counts())

print("\nDistribusi label testing:")
print(y_test.value_counts())

model_dt = DecisionTreeClassifier(
    criterion="entropy",
    max_depth=3,
    random_state=42
)

model_dt.fit(X_train, y_train)

print("Training Decision Tree selesai.")

y_pred = model_dt.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("Accuracy:", accuracy)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

hasil_prediksi_df = test_features_df[["filename", "label"]].copy()
hasil_prediksi_df["predicted_label"] = y_pred
hasil_prediksi_df["correct"] = hasil_prediksi_df["label"] == hasil_prediksi_df["predicted_label"]

hasil_prediksi_df

hasil_prediksi_df.to_csv("hasil_prediksi_decision_tree.csv", index=False)
files.download("hasil_prediksi_decision_tree.csv")

with pd.ExcelWriter("hasil_prediksi_decision_tree.xlsx", engine="openpyxl") as writer:
    hasil_prediksi_df.to_excel(writer, sheet_name="Hasil Prediksi", index=False)

files.download("hasil_prediksi_decision_tree.xlsx")

plt.figure(figsize=(22, 10))

plot_tree(
    model_dt,
    feature_names=feature_cols,
    class_names=model_dt.classes_,
    filled=True,
    rounded=True,
    fontsize=10
)

plt.show()

rules = export_text(model_dt, feature_names=feature_cols)
print(rules)

with open("aturan_decision_tree.txt", "w") as f:
    f.write(rules)

files.download("aturan_decision_tree.txt")

model_info = pd.DataFrame([{
    "model": "Decision Tree",
    "criterion": "entropy",
    "max_depth": 3,
    "features": ", ".join(feature_cols),
    "accuracy": accuracy,
    "training_data_count": len(X_train),
    "testing_data_count": len(X_test)
}])

model_info.to_csv("decision_tree_model_info.csv", index=False)
files.download("decision_tree_model_info.csv")

feature_importance_df = pd.DataFrame({
    "feature": feature_cols,
    "importance": model_dt.feature_importances_
}).sort_values(by="importance", ascending=False)

feature_importance_df

feature_importance_df.to_csv("feature_importance_decision_tree.csv", index=False)
files.download("feature_importance_decision_tree.csv")

classification_report_dict = classification_report(y_test, y_pred, output_dict=True)
classification_report_df = pd.DataFrame(classification_report_dict).transpose()

conf_matrix = confusion_matrix(y_test, y_pred, labels=model_dt.classes_)
confusion_matrix_df = pd.DataFrame(
    conf_matrix,
    index=[f"actual_{label}" for label in model_dt.classes_],
    columns=[f"predicted_{label}" for label in model_dt.classes_]
)

with pd.ExcelWriter("hasil_decision_tree_lengkap.xlsx", engine="openpyxl") as writer:
    model_info.to_excel(writer, sheet_name="Model Info", index=False)
    hasil_prediksi_df.to_excel(writer, sheet_name="Prediksi Testing", index=False)
    classification_report_df.to_excel(writer, sheet_name="Classification Report")
    confusion_matrix_df.to_excel(writer, sheet_name="Confusion Matrix")
    feature_importance_df.to_excel(writer, sheet_name="Feature Importance", index=False)

files.download("hasil_decision_tree_lengkap.xlsx")

from sklearn.metrics import classification_report, confusion_matrix
import pandas as pd
from google.colab import files

classification_report_dict = classification_report(
    y_test,
    y_pred,
    output_dict=True
)

classification_report_df = pd.DataFrame(classification_report_dict).transpose()

classification_report_df.to_csv(
    "classification_report_decision_tree.csv",
    index=True
)

files.download("classification_report_decision_tree.csv")

labels = model_dt.classes_

conf_matrix = confusion_matrix(
    y_test,
    y_pred,
    labels=labels
)

confusion_matrix_df = pd.DataFrame(
    conf_matrix,
    index=[f"actual_{label}" for label in labels],
    columns=[f"predicted_{label}" for label in labels]
)

confusion_matrix_df.to_csv(
    "confusion_matrix_decision_tree.csv",
    index=True
)

files.download("confusion_matrix_decision_tree.csv")

with pd.ExcelWriter("evaluasi_decision_tree.xlsx", engine="openpyxl") as writer:
    classification_report_df.to_excel(writer, sheet_name="Classification Report")
    confusion_matrix_df.to_excel(writer, sheet_name="Confusion Matrix")

files.download("evaluasi_decision_tree.xlsx")

from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pandas as pd

depth_results = []

for depth in [2, 3, 4, 5, None]:
    model_check = DecisionTreeClassifier(
        criterion="entropy",
        max_depth=depth,
        random_state=42
    )

    model_check.fit(X_train, y_train)
    y_pred_check = model_check.predict(X_test)

    used_features = [
        feature_cols[i]
        for i in model_check.tree_.feature
        if i != -2
    ]

    used_features_unique = sorted(set(used_features))

    depth_results.append({
        "max_depth": "None" if depth is None else depth,
        "accuracy": accuracy_score(y_test, y_pred_check),
        "precision_macro": precision_score(y_test, y_pred_check, average="macro"),
        "recall_macro": recall_score(y_test, y_pred_check, average="macro"),
        "f1_macro": f1_score(y_test, y_pred_check, average="macro"),
        "jumlah_fitur_dipakai": len(used_features_unique),
        "fitur_dipakai": ", ".join(used_features_unique),
        "jumlah_node": model_check.tree_.node_count,
        "kedalaman_pohon": model_check.tree_.max_depth
    })

depth_results_df = pd.DataFrame(depth_results)
depth_results_df

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    ConfusionMatrixDisplay,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

from sklearn.tree import plot_tree, export_text

labels = model_dt.classes_

cm = confusion_matrix(y_test, y_pred, labels=labels)

disp = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=labels
)

plt.figure(figsize=(6, 5))
disp.plot(values_format="d")
plt.title("Confusion Matrix Decision Tree")
plt.grid(False)
plt.show()

report_dict = classification_report(
    y_test,
    y_pred,
    output_dict=True
)

classification_report_df = pd.DataFrame(report_dict).transpose()
classification_report_df

report_plot_df = classification_report_df.copy()

report_plot_df = report_plot_df.loc[
    [idx for idx in report_plot_df.index if idx in labels],
    ["precision", "recall", "f1-score"]
]

ax = report_plot_df.plot(kind="bar", figsize=(8, 5))

plt.title("Classification Report Decision Tree")
plt.xlabel("Class")
plt.ylabel("Score")
plt.ylim(0, 1.1)
plt.xticks(rotation=0)
plt.grid(axis="y")
plt.legend(loc="lower right")
plt.tight_layout()
plt.show()

feature_importance_df = pd.DataFrame({
    "feature": feature_cols,
    "importance": model_dt.feature_importances_
}).sort_values(by="importance", ascending=False)

feature_importance_df

plt.figure(figsize=(9, 5))
plt.bar(feature_importance_df["feature"], feature_importance_df["importance"])
plt.title("Feature Importance Decision Tree")
plt.xlabel("Feature")
plt.ylabel("Importance")
plt.xticks(rotation=45, ha="right")
plt.ylim(0, 1.1)
plt.grid(axis="y")
plt.tight_layout()
plt.show()

plt.figure(figsize=(9, 5))
plt.bar(feature_importance_df["feature"], feature_importance_df["importance"])
plt.title("Feature Importance Decision Tree")
plt.xlabel("Feature")
plt.ylabel("Importance")
plt.xticks(rotation=45, ha="right")
plt.ylim(0, 1.1)
plt.grid(axis="y")
plt.tight_layout()
plt.show()

from google.colab import files

uploaded = files.upload()

!pip -q install openpyxl

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

RAW_EXCEL_PATH = "Dataset Raw.xlsx"

MOTOR_SEG_PATH = "Percobaan 1 Motor.csv"
NON_MOTOR_SEG_PATH = "Percobaan 1 Non Motor.csv"

MOTOR_SHEET = "Pengujian 1"
NON_MOTOR_SHEET = "Orang 1"

OUTPUT_DIR = "gambar_bab_6_1"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def time_to_ms_in_day(time_series):
    dt = pd.to_datetime(time_series, errors="coerce")

    ms = (
        dt.dt.hour * 3600 * 1000
        + dt.dt.minute * 60 * 1000
        + dt.dt.second * 1000
        + (dt.dt.microsecond // 1000)
    )

    return ms

def load_raw_excel_sheet(file_path, sheet_name):

    raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

    header_row = None

    for i in range(len(raw)):
        row_values = (
            raw.iloc[i]
            .astype(str)
            .str.strip()
            .str.upper()
            .str.replace("\ufeff", "", regex=False)
            .tolist()
        )

        if "TIME" in row_values and "CH2" in row_values:
            header_row = i
            break

    if header_row is None:
        raise ValueError(f"Header TIME dan CH2 tidak ditemukan pada sheet {sheet_name}")

    columns = (
        raw.iloc[header_row]
        .astype(str)
        .str.strip()
        .str.upper()
        .str.replace("\ufeff", "", regex=False)
        .tolist()
    )

    df = raw.iloc[header_row + 1:].copy()
    df.columns = columns

    df = df.loc[:, ~pd.Index(df.columns).astype(str).str.contains("^UNNAMED", case=False, na=False)]

    keep_cols = [c for c in ["TIME", "CH1", "CH2", "CH3", "CH4", "CH5"] if c in df.columns]
    df = df[keep_cols].copy()

    df["TIME_dt"] = pd.to_datetime(df["TIME"], errors="coerce")

    df["CH2"] = pd.to_numeric(df["CH2"], errors="coerce")

    df = df.dropna(subset=["TIME_dt", "CH2"]).reset_index(drop=True)

    df["raw_index_top_order"] = np.arange(len(df))

    df["time_ms_day"] = time_to_ms_in_day(df["TIME_dt"])

    return df

def load_segment_csv(file_path, label_name):

    df = pd.read_csv(file_path, sep=";", engine="python")

    df.columns = [
        str(c).strip().replace("\ufeff", "").upper()
        for c in df.columns
    ]

    df = df.loc[:, ~pd.Index(df.columns).astype(str).str.contains("^UNNAMED", case=False, na=False)]

    keep_cols = [c for c in ["TIME", "CH1", "CH2", "CH3", "CH4", "CH5"] if c in df.columns]
    df = df[keep_cols].copy()

    df["TIME_str"] = df["TIME"].astype(str).str.strip()
    df["TIME_dt"] = pd.to_datetime(df["TIME_str"], format="%H:%M:%S,%f", errors="coerce")

    df["CH2"] = pd.to_numeric(df["CH2"], errors="coerce")

    df = df.dropna(subset=["TIME_dt", "CH2"]).reset_index(drop=True)

    df["seg_index_top_order"] = np.arange(len(df))

    df["time_ms_day"] = time_to_ms_in_day(df["TIME_dt"])

    df["label_file"] = label_name

    return df

raw_motor = load_raw_excel_sheet(RAW_EXCEL_PATH, MOTOR_SHEET)
raw_non_motor = load_raw_excel_sheet(RAW_EXCEL_PATH, NON_MOTOR_SHEET)

seg_motor = load_segment_csv(MOTOR_SEG_PATH, "motor")
seg_non_motor = load_segment_csv(NON_MOTOR_SEG_PATH, "non_motor")

print("Raw Motor:", raw_motor.shape)
print("Segment Motor:", seg_motor.shape)

print("Raw Non Motor:", raw_non_motor.shape)
print("Segment Non Motor:", seg_non_motor.shape)

display(raw_motor.head())
display(seg_motor.head())
display(raw_non_motor.head())
display(seg_non_motor.head())

def match_segment_to_raw_by_time_and_ch2(segment_df, raw_df, tolerance_ms=10):
    matched_rows = []

    for _, seg_row in segment_df.iterrows():
        seg_time = seg_row["time_ms_day"]
        seg_ch2 = seg_row["CH2"]

        candidates = raw_df[
            (raw_df["CH2"] == seg_ch2)
            & ((raw_df["time_ms_day"] - seg_time).abs() <= tolerance_ms)
        ].copy()

        if len(candidates) == 0:
            matched_rows.append({
                "seg_index_top_order": seg_row["seg_index_top_order"],
                "seg_time": seg_row["TIME"],
                "seg_ch2": seg_ch2,
                "matched": False,
                "raw_index_top_order": np.nan,
                "raw_time": np.nan,
                "time_diff_ms": np.nan
            })
        else:
            candidates["time_diff_abs"] = (candidates["time_ms_day"] - seg_time).abs()
            best = candidates.sort_values("time_diff_abs").iloc[0]

            matched_rows.append({
                "seg_index_top_order": seg_row["seg_index_top_order"],
                "seg_time": seg_row["TIME"],
                "seg_ch2": seg_ch2,
                "matched": True,
                "raw_index_top_order": int(best["raw_index_top_order"]),
                "raw_time": best["TIME_dt"],
                "time_diff_ms": int(best["time_ms_day"] - seg_time)
            })

    match_df = pd.DataFrame(matched_rows)

    total = len(match_df)
    matched = match_df["matched"].sum()

    print("Total data segment:", total)
    print("Data yang cocok di raw:", matched)
    print("Persentase cocok:", round(matched / total * 100, 2), "%")

    if matched > 0:
        raw_start_top = int(match_df.loc[match_df["matched"], "raw_index_top_order"].min())
        raw_end_top = int(match_df.loc[match_df["matched"], "raw_index_top_order"].max())

        print("Index raw posisi atas-terbaru awal range:", raw_start_top)
        print("Index raw posisi atas-terbaru akhir range:", raw_end_top)

    return match_df

print("Pencocokan Motor 1")
match_motor = match_segment_to_raw_by_time_and_ch2(
    seg_motor,
    raw_motor,
    tolerance_ms=10
)

display(match_motor.head())
display(match_motor.tail())

print("Pencocokan Non Motor 1")
match_non_motor = match_segment_to_raw_by_time_and_ch2(
    seg_non_motor,
    raw_non_motor,
    tolerance_ms=10
)

display(match_non_motor.head())
display(match_non_motor.tail())

def make_chronological_for_plot(df, time_col="TIME_dt"):
    plot_df = df.iloc[::-1].reset_index(drop=True).copy()

    plot_df["plot_time_sec"] = (
        plot_df[time_col] - plot_df[time_col].iloc[0]
    ).dt.total_seconds()

    return plot_df

def plot_raw_with_matched_event(raw_df, match_df, title, save_path):
    matched = match_df[match_df["matched"]].copy()

    if len(matched) == 0:
        raise ValueError("Tidak ada data segment yang cocok dengan raw.")

    event_start_time = matched["raw_time"].min()
    event_end_time = matched["raw_time"].max()

    plot_df = make_chronological_for_plot(raw_df, time_col="TIME_dt")

    event_start_sec = (event_start_time - plot_df["TIME_dt"].iloc[0]).total_seconds()
    event_end_sec = (event_end_time - plot_df["TIME_dt"].iloc[0]).total_seconds()

    plt.figure(figsize=(10, 4))

    plt.plot(
        plot_df["plot_time_sec"],
        plot_df["CH2"],
        linewidth=1,
        label="Sinyal Raw"
    )

    plt.axvspan(
        event_start_sec,
        event_end_sec,
        alpha=0.25,
        label="Area Event dari File Potong"
    )

    plt.title(title)
    plt.xlabel("Waktu berdasarkan TIME (detik)")
    plt.ylabel("Nilai Raw Load Cell (CH2)")
    plt.ticklabel_format(style="plain", axis="y")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    plt.savefig(save_path, dpi=300)
    plt.show()

    print("Gambar disimpan:", save_path)
    print("Event mulai:", event_start_time)
    print("Event selesai:", event_end_time)
    print("Event mulai detik:", event_start_sec)
    print("Event selesai detik:", event_end_sec)

def plot_segment_event(segment_df, title, save_path):

    plot_df = segment_df.iloc[::-1].reset_index(drop=True).copy()

    plot_df["event_time_sec"] = (
        plot_df["TIME_dt"] - plot_df["TIME_dt"].iloc[0]
    ).dt.total_seconds()

    plt.figure(figsize=(10, 4))

    plt.plot(
        plot_df["event_time_sec"],
        plot_df["CH2"],
        linewidth=1.5
    )

    plt.title(title)
    plt.xlabel("Waktu Event berdasarkan TIME (detik)")
    plt.ylabel("Nilai Raw Load Cell (CH2)")
    plt.ticklabel_format(style="plain", axis="y")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(save_path, dpi=300)
    plt.show()

    print("Gambar disimpan:", save_path)

path_motor_raw_area = os.path.join(
    OUTPUT_DIR,
    "gambar_area_event_motor_1_dari_dataset_raw.png"
)

plot_raw_with_matched_event(
    raw_df=raw_motor,
    match_df=match_motor,
    title="Area Event Motor 1 pada Dataset Raw",
    save_path=path_motor_raw_area
)

path_motor_segment = os.path.join(
    OUTPUT_DIR,
    "gambar_hasil_event_motor_1_yang_sudah_dipotong.png"
)

plot_segment_event(
    segment_df=seg_motor,
    title="Hasil Pemotongan Event Motor 1",
    save_path=path_motor_segment
)

path_non_motor_raw_area = os.path.join(
    OUTPUT_DIR,
    "gambar_area_event_non_motor_1_dari_dataset_raw.png"
)

plot_raw_with_matched_event(
    raw_df=raw_non_motor,
    match_df=match_non_motor,
    title="Area Event Non Motor 1 pada Dataset Raw",
    save_path=path_non_motor_raw_area
)

path_non_motor_segment = os.path.join(
    OUTPUT_DIR,
    "gambar_hasil_event_non_motor_1_yang_sudah_dipotong.png"
)

plot_segment_event(
    segment_df=seg_non_motor,
    title="Hasil Pemotongan Event Non Motor 1",
    save_path=path_non_motor_segment
)

from google.colab import files

download_files = [
    path_motor_raw_area,
    path_motor_segment,
    path_non_motor_raw_area,
    path_non_motor_segment
]

for path in download_files:
    files.download(path)

from google.colab import files

uploaded = files.upload()

!pip -q install openpyxl graphviz

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from graphviz import Digraph
from google.colab import files

excel_path = "hasil_decision_tree_lengkap.xlsx"
rule_path = "aturan_decision_tree.txt"

output_dir = "gambar_bab_6_3"
os.makedirs(output_dir, exist_ok=True)

xls = pd.ExcelFile(excel_path)

print("Daftar sheet:")
for sheet in xls.sheet_names:
    print("-", sheet)

cm_df = pd.read_excel(excel_path, sheet_name="Confusion Matrix")

display(cm_df)

cm_values = cm_df[["predicted_motor", "predicted_non_motor"]].to_numpy()

actual_labels = ["Aktual Motor", "Aktual Non Motor"]
predicted_labels = ["Prediksi Motor", "Prediksi Non Motor"]

print(cm_values)

plt.figure(figsize=(6, 5))

plt.imshow(cm_values)

for i in range(cm_values.shape[0]):
    for j in range(cm_values.shape[1]):
        plt.text(
            j,
            i,
            cm_values[i, j],
            ha="center",
            va="center",
            fontsize=14
        )

plt.xticks(np.arange(len(predicted_labels)), predicted_labels)
plt.yticks(np.arange(len(actual_labels)), actual_labels)

plt.title("Confusion Matrix Model Decision Tree")
plt.xlabel("Kelas Prediksi")
plt.ylabel("Kelas Aktual")

plt.colorbar(label="Jumlah Data")
plt.tight_layout()

path_cm = os.path.join(output_dir, "gambar_6_5_confusion_matrix_decision_tree.png")
plt.savefig(path_cm, dpi=300, bbox_inches="tight")
plt.show()

print("Gambar confusion matrix disimpan di:", path_cm)

fi_df = pd.read_excel(excel_path, sheet_name="Feature Importance")

display(fi_df)

fi_plot = fi_df.sort_values("importance", ascending=True)

plt.figure(figsize=(8, 5))

plt.barh(
    fi_plot["feature"],
    fi_plot["importance"]
)

plt.title("Feature Importance Model Decision Tree")
plt.xlabel("Nilai Importance")
plt.ylabel("Fitur")
plt.grid(axis="x", alpha=0.3)
plt.tight_layout()

path_fi = os.path.join(output_dir, "gambar_6_6_feature_importance_decision_tree.png")
plt.savefig(path_fi, dpi=300, bbox_inches="tight")
plt.show()

print("Gambar feature importance disimpan di:", path_fi)

with open(rule_path, "r", encoding="utf-8") as f:
    rule_text = f.read()

print(rule_text)

dot = Digraph(comment="Decision Tree Rule")

dot.attr(rankdir="TB")
dot.attr("node", shape="box", style="rounded")

dot.node("A", "mean_delta_raw ≤ 265535.88?")
dot.node("B", "duration_ms ≤ 2375.50?")
dot.node("C", "duration_ms ≤ 2675.00?")
dot.node("D", "duration_ms ≤ 849.00?")

dot.node("M1", "motor", shape="ellipse")
dot.node("NM1", "non_motor", shape="ellipse")
dot.node("M2", "motor", shape="ellipse")
dot.node("M3", "motor", shape="ellipse")
dot.node("NM2", "non_motor", shape="ellipse")

dot.edge("A", "B", label="Iya")
dot.edge("B", "M1", label="Iya")
dot.edge("B", "C", label="Tidak")
dot.edge("C", "NM1", label="Iya")
dot.edge("C", "M2", label="Tidak")

dot.edge("A", "D", label="Tidak")
dot.edge("D", "M3", label="Iya")
dot.edge("D", "NM2", label="Tidak")

path_tree = os.path.join(output_dir, "gambar_6_7_visualisasi_rule_decision_tree")

dot.render(path_tree, format="png", cleanup=True)

print("Gambar rule decision tree disimpan di:", path_tree + ".png")

from IPython.display import Image, display

display(Image(filename=path_tree + ".png"))

files.download(path_cm)
files.download(path_fi)
files.download(path_tree + ".png")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

output_dir = "gambar_bab_6_4"
os.makedirs(output_dir, exist_ok=True)

cm_realtime = np.array([
    [73, 7],
    [2, 28]
])

actual_labels = ["Aktual Motor", "Aktual Non Motor"]
predicted_labels = ["Prediksi Motor", "Prediksi Non Motor"]

total_data = cm_realtime.sum()
correct_data = np.trace(cm_realtime)
accuracy = correct_data / total_data

print("Total data:", total_data)
print("Benar:", correct_data)
print("Salah:", total_data - correct_data)
print("Accuracy:", accuracy)
print("Accuracy (%):", accuracy * 100)

plt.figure(figsize=(6, 5))

plt.imshow(cm_realtime)

for i in range(cm_realtime.shape[0]):
    for j in range(cm_realtime.shape[1]):
        plt.text(
            j,
            i,
            cm_realtime[i, j],
            ha="center",
            va="center",
            fontsize=16
        )

plt.xticks(np.arange(len(predicted_labels)), predicted_labels)
plt.yticks(np.arange(len(actual_labels)), actual_labels)

plt.title("Confusion Matrix Klasifikasi Real-time ESP32-S3")
plt.xlabel("Kelas Prediksi")
plt.ylabel("Kelas Aktual")

plt.colorbar(label="Jumlah Data")
plt.tight_layout()

path_cm_realtime = os.path.join(
    output_dir,
    "gambar_6_8_confusion_matrix_realtime_esp32s3.png"
)

plt.savefig(path_cm_realtime, dpi=300, bbox_inches="tight")
plt.show()

print("Gambar disimpan di:", path_cm_realtime)

precision_motor = 73 / (73 + 2)
recall_motor = 73 / (73 + 7)
f1_motor = 2 * precision_motor * recall_motor / (precision_motor + recall_motor)
support_motor = 80

precision_non_motor = 28 / (28 + 7)
recall_non_motor = 28 / (28 + 2)
f1_non_motor = 2 * precision_non_motor * recall_non_motor / (precision_non_motor + recall_non_motor)
support_non_motor = 30

accuracy = (73 + 28) / 110

macro_precision = (precision_motor + precision_non_motor) / 2
macro_recall = (recall_motor + recall_non_motor) / 2
macro_f1 = (f1_motor + f1_non_motor) / 2

weighted_precision = ((precision_motor * support_motor) + (precision_non_motor * support_non_motor)) / 110
weighted_recall = ((recall_motor * support_motor) + (recall_non_motor * support_non_motor)) / 110
weighted_f1 = ((f1_motor * support_motor) + (f1_non_motor * support_non_motor)) / 110

report_df = pd.DataFrame([
    ["Motor", precision_motor, recall_motor, f1_motor, support_motor],
    ["Non_motor", precision_non_motor, recall_non_motor, f1_non_motor, support_non_motor],
    ["Accuracy", None, None, accuracy, 110],
    ["Macro Average", macro_precision, macro_recall, macro_f1, 110],
    ["Weighted Average", weighted_precision, weighted_recall, weighted_f1, 110],
], columns=["Kelas", "Precision", "Recall", "F1-score", "Support"])

display(report_df)

report_df.to_excel(
    os.path.join(output_dir, "classification_report_realtime_esp32s3.xlsx"),
    index=False
)

metrics_plot_df = pd.DataFrame({
    "Kelas": ["Motor", "Non_motor"],
    "Precision": [precision_motor, precision_non_motor],
    "Recall": [recall_motor, recall_non_motor],
    "F1-score": [f1_motor, f1_non_motor]
})

display(metrics_plot_df)

x = np.arange(len(metrics_plot_df["Kelas"]))
width = 0.25

plt.figure(figsize=(8, 5))

plt.bar(x - width, metrics_plot_df["Precision"], width, label="Precision")
plt.bar(x, metrics_plot_df["Recall"], width, label="Recall")
plt.bar(x + width, metrics_plot_df["F1-score"], width, label="F1-score")

plt.xticks(x, metrics_plot_df["Kelas"])
plt.ylim(0, 1.1)

plt.title("Precision, Recall, dan F1-score Klasifikasi Real-time")
plt.xlabel("Kelas")
plt.ylabel("Nilai")
plt.grid(axis="y", alpha=0.3)
plt.legend()
plt.tight_layout()

path_metrics = os.path.join(
    output_dir,
    "gambar_precision_recall_f1_realtime_esp32s3.png"
)

plt.savefig(path_metrics, dpi=300, bbox_inches="tight")
plt.show()

print("Gambar disimpan di:", path_metrics)

beam_df = pd.DataFrame({
    "Hasil Klasifikasi": ["Motor", "Non_motor"],
    "Jumlah": [8, 2]
})

display(beam_df)

plt.figure(figsize=(6, 4))

plt.bar(
    beam_df["Hasil Klasifikasi"],
    beam_df["Jumlah"]
)

for i, value in enumerate(beam_df["Jumlah"]):
    plt.text(
        i,
        value,
        str(value),
        ha="center",
        va="bottom",
        fontsize=12
    )

plt.title("Distribusi Hasil Klasifikasi Sepeda Listrik BEAM")
plt.xlabel("Hasil Klasifikasi")
plt.ylabel("Jumlah Pengujian")
plt.ylim(0, 10)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

path_beam = os.path.join(
    output_dir,
    "gambar_distribusi_klasifikasi_beam.png"
)

plt.savefig(path_beam, dpi=300, bbox_inches="tight")
plt.show()

print("Gambar disimpan di:", path_beam)

from google.colab import files

files.download(path_cm_realtime)
files.download(path_metrics)
files.download(path_beam)
