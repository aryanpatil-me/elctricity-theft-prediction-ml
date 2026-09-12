# Energy Theft & Abnormal Consumption Detection

An AI-powered system for detecting **electricity theft and abnormal energy consumption** using smart-meter data, machine learning, and transformer-level energy analysis.

## Overview

The system analyzes electricity consumption patterns to identify suspicious or abnormal behavior. Instead of simply classifying a consumer as *"theft"* or *"no theft"*, it attempts to identify the likely cause of an anomaly, such as:

* Electricity theft
* Meter tampering
* Faulty/failing meter
* Communication failure
* Unusual consumption
* Other unexplained anomalies

The system also uses **transformer-level energy accounting** to cross-check whether detected anomalies correspond to actual unaccounted energy.

## Key Features

* AI-based anomaly detection
* Transformer-level energy cross-check
* Detection of known and unknown abnormal patterns
* Explainable AI using SHAP
* Cause-based classification
* Prioritized inspection cases
* Evidence generation for field officers
* Feedback loop from inspection results

## How It Works

```text
Smart Meter Data
       ↓
Data Collection & Processing
       ↓
ML-based Anomaly Detection
       ↓
Transformer-level Physics Cross-check
       ↓
Cause Identification
       ↓
Case Prioritization
       ↓
Field Verification
       ↓
Inspection Result → Model Feedback
```

The system combines multiple approaches including **LightGBM, Isolation Forest, LSTM Autoencoder, and PU Learning** rather than relying on a single model. 

## Tech Stack

* **Python**
* **Pandas**
* **LightGBM**
* **PyTorch**
* **Isolation Forest**
* **LSTM Autoencoder**
* **PU Learning**
* **SHAP**
* **FastAPI**
* **PostgreSQL / TimescaleDB**
* **React**
* **Tailwind CSS**
* **Recharts**
* **ESP32**
* **ReportLab**

## Dataset

The project uses the **SGCC Electricity Theft Detection Dataset** as a primary benchmark, along with simulated theft patterns and testbed data for validation. The referenced SGCC dataset contains **42,372 consumers over 1,036 days**. 

## Important Principle

An AI anomaly score is **not treated as proof of electricity theft**.

The system is designed to provide an explainable, prioritized lead for field investigation. Physical verification is required before taking action. 

## Project

Developed as part of **Smart India Hackathon 2026**.

* **Problem Statement:** PS 53
* **Problem:** Energy Theft and Abnormal Consumption Detection
* **Theme:** Renewable / Sustainable Energy
* **Team:** Turing Sparks
* **Team ID:** SIH26-S073 

## Status

**Developed**

More details, implementation, experiments, and documentation will not be added as the project is concluded.
