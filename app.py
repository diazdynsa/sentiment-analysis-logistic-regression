"""
ReviewScope - Customer Sentiment Analysis
Flask backend untuk klasifikasi sentimen ulasan pelanggan
menggunakan Logistic Regression dan TF-IDF yang sudah dilatih.
"""

import os
import re
import logging
from flask import Flask, render_template, request, jsonify
import joblib
import numpy as np

# ---------------------------------------------------------------------------
# Konfigurasi logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Inisialisasi Flask
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB max request

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "logistic_regression_model.joblib")
VECTORIZER_PATH = os.path.join(BASE_DIR, "tfidf_vectorizer.joblib")

MAX_REVIEW_LENGTH = 2000  # karakter
MIN_REVIEW_LENGTH = 3     # karakter

# ---------------------------------------------------------------------------
# Muat model dan vectorizer satu kali saat aplikasi dimulai
# ---------------------------------------------------------------------------
model = None
vectorizer = None
model_load_error = None

try:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"File model tidak ditemukan: {MODEL_PATH}\n"
            "Salin 'logistic_regression_model.joblib' dari Google Colab ke folder project."
        )
    if not os.path.exists(VECTORIZER_PATH):
        raise FileNotFoundError(
            f"File vectorizer tidak ditemukan: {VECTORIZER_PATH}\n"
            "Salin 'tfidf_vectorizer.joblib' dari Google Colab ke folder project."
        )

    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    logger.info("Model dan vectorizer berhasil dimuat.")
    logger.info(f"Kelas model: {model.classes_}")

except FileNotFoundError as e:
    model_load_error = str(e)
    logger.error(f"[MODEL LOAD ERROR] {model_load_error}")
except Exception as e:
    model_load_error = f"Gagal memuat model: {str(e)}"
    logger.error(f"[MODEL LOAD ERROR] {model_load_error}")


# ---------------------------------------------------------------------------
# Helper: bersihkan teks input secara minimal
# ---------------------------------------------------------------------------
def sanitize_text(text: str) -> str:
    """
    Bersihkan teks input secara minimal — hanya normalisasi whitespace.
    Tidak mengubah makna kalimat.
    """
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


# ---------------------------------------------------------------------------
# Helper: lakukan inferensi
# ---------------------------------------------------------------------------
def predict_sentiment(review_text: str) -> dict:
    """
    Lakukan prediksi sentimen menggunakan model dan vectorizer yang sudah dimuat.
    Mengembalikan dict berisi prediksi, probabilitas, dan metadata.
    """
    if model is None or vectorizer is None:
        raise RuntimeError("Model belum dimuat. Periksa file .joblib.")

    # Transform teks menggunakan vectorizer yang sudah dilatih
    features = vectorizer.transform([review_text])

    # Prediksi kelas
    prediction = model.predict(features)[0]

    # Probabilitas — gunakan model.classes_ untuk pemetaan yang benar
    proba = model.predict_proba(features)[0]
    classes = model.classes_

    # Buat mapping kelas → probabilitas
    proba_map = {int(cls): float(prob) for cls, prob in zip(classes, proba)}

    prob_negative = proba_map.get(0, 0.0)
    prob_positive = proba_map.get(1, 0.0)

    sentiment_label = "Positif" if int(prediction) == 1 else "Negatif"
    sentiment_class = "positive" if int(prediction) == 1 else "negative"

    return {
        "sentiment_label": sentiment_label,
        "sentiment_class": sentiment_class,
        "predicted_class": int(prediction),
        "prob_positive": round(prob_positive * 100, 2),
        "prob_negative": round(prob_negative * 100, 2),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    """Halaman utama — tampilkan form analisis sentimen."""
    return render_template(
        "index.html",
        model_ready=(model is not None and vectorizer is not None),
        model_error=model_load_error,
        result=None,
        review_text="",
        error_message=None,
    )


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Endpoint POST — terima ulasan, jalankan inferensi, kembalikan hasil.
    """
    review_text = request.form.get("review", "").strip()
    error_message = None
    result = None

    # --- Validasi input ---
    if not review_text:
        error_message = "Teks ulasan tidak boleh kosong."
    elif len(review_text) < MIN_REVIEW_LENGTH:
        error_message = f"Teks ulasan terlalu singkat (minimal {MIN_REVIEW_LENGTH} karakter)."
    elif len(review_text) > MAX_REVIEW_LENGTH:
        error_message = (
            f"Teks ulasan terlalu panjang. Maksimum {MAX_REVIEW_LENGTH} karakter "
            f"(saat ini {len(review_text)} karakter)."
        )

    # --- Periksa model ---
    if not error_message and (model is None or vectorizer is None):
        error_message = (
            "Model belum tersedia. "
            "Pastikan file 'logistic_regression_model.joblib' dan "
            "'tfidf_vectorizer.joblib' ada di folder project."
        )

    # --- Inferensi ---
    if not error_message:
        try:
            clean_text = sanitize_text(review_text)
            result = predict_sentiment(clean_text)
            result["review_text"] = clean_text
            logger.info(
                f"Prediksi: {result['sentiment_label']} "
                f"(+{result['prob_positive']}% / -{result['prob_negative']}%)"
            )
        except Exception as e:
            logger.error(f"[INFERENCE ERROR] {str(e)}")
            error_message = "Terjadi kesalahan saat memproses ulasan. Silakan coba lagi."

    return render_template(
        "index.html",
        model_ready=(model is not None and vectorizer is not None),
        model_error=model_load_error,
        result=result,
        review_text=review_text,
        error_message=error_message,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
