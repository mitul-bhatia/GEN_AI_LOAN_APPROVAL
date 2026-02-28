# Loan Approval Prediction System

A Machine Learning system to predict loan approval status using Logistic Regression and XGBoost, with a production Streamlit web application.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![XGBoost](https://img.shields.io/badge/XGBoost-3.2-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-1.54-red)
![Accuracy](https://img.shields.io/badge/Accuracy-92.86%25-brightgreen)

## 🌐 Live Demo

**[Try the App →](https://genailoanapproval-mitul.streamlit.app/)**

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Dataset](#dataset)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Models & Results](#models--results)
- [Methodology](#methodology)
- [Tech Stack](#tech-stack)
- [Author](#author)

## Overview

This project predicts whether a loan application will be approved or rejected based on applicant features such as credit score, annual income, employment status, and loan details.

**Key Achievement:** Improved accuracy from **86.42%** (Logistic Regression) to **92.86%** (XGBoost) by discovering that `credit_score × DTI` interaction explains 40% of classification errors.

### Key Features

1. **Exploratory Data Analysis** - 6 comprehensive visualizations
2. **Error Analysis Pipeline** - Diagnosed why LR was stuck at 86%
3. **Feature Interaction Discovery** - Found `credit_score × DTI` correlation = 0.166
4. **Production Deployment** - Real-time predictions on Streamlit Cloud

## Dataset

The dataset contains **50,000 loan applications** with **20 features**:

| Feature | Description |
|---------|-------------|
| `customer_id` | Unique identifier for each customer |
| `age` | Age of the applicant |
| `occupation_status` | Employment type (Employed/Self-Employed/Student) |
| `years_employed` | Years of employment |
| `annual_income` | Annual income in currency units |
| `credit_score` | Credit score (300-850) |
| `credit_history_years` | Length of credit history |
| `savings_assets` | Savings and assets value |
| `current_debt` | Current debt amount |
| `defaults_on_file` | Number of defaults |
| `delinquencies_last_2yrs` | Recent payment delinquencies |
| `derogatory_marks` | Negative credit marks |
| `product_type` | Type of loan product |
| `loan_intent` | Purpose of the loan |
| `loan_amount` | Requested loan amount |
| `interest_rate` | Interest rate offered |
| `debt_to_income_ratio` | Debt to income ratio |
| `loan_to_income_ratio` | Loan amount to income ratio |
| `payment_to_income_ratio` | Monthly payment to income ratio |
| `loan_status` | **Target variable** (0: Rejected, 1: Approved) |

## Project Structure

```
loan-approval-prediction/
├── data/
│   ├── raw/                        # Original dataset
│   └── processed/                  # Preprocessed train/test splits
├── notebooks/
│   ├── 01_EDA.ipynb                # Exploratory Data Analysis
│   ├── 02_ML_Models.ipynb          # Logistic Regression
│   ├── 03_Error_Analysis.ipynb     # Why LR stuck at 86%?
│   └── 04_XGBoost.ipynb            # XGBoost (92.86%)
├── models/
│   ├── logistic_regression.pkl     # Baseline model
│   └── xgboost.pkl                 # Production model
├── app/
│   └── app.py                      # Streamlit application
├── report/
│   ├── PROJECT_REPORT.md           # Markdown report
│   ├── main.tex                    # LaTeX report
│   └── *.png                       # Visualizations
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites
- Python 3.11+
- pip or conda

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/loan-approval-prediction.git
cd loan-approval-prediction
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Verify installation**
```bash
python -c "import pandas, sklearn, tensorflow; print('Setup successful!')"
```

## Usage

### Running Notebooks

```bash
jupyter notebook
# Navigate to notebooks/ folder and run notebooks in order
```

### Training Models

```bash
# Train ML models
python src/train_ml.py

# Train Deep Learning model
python src/train_dl.py
```

### Running the Web App

```bash
streamlit run app/streamlit_app.py
```

The app will open at `http://localhost:8501`

## Models & Results

### Model Comparison

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|-------|----------|-----------|--------|----------|---------|
| Logistic Regression | 86.42% | 86.91% | 88.68% | 87.79% | 94.39% |
| **XGBoost** | **92.86%** | **92.65%** | **94.53%** | **93.58%** | **98.42%** |

### Why XGBoost Won

| LR Limitation | XGBoost Solution |
|---------------|------------------|
| Additive effects only | Trees capture interactions |
| Smooth decision boundary | Step functions via splits |
| Single classifier | Ensemble of 200 trees |

**Key Discovery:** The interaction `credit_score × DTI` predicts errors 5x better than either feature alone (r=0.166 vs r≈0.03).

## Methodology

1. **EDA**: Analyzed 50,000 samples, 20 features, identified credit_score (+0.50) as strongest predictor
2. **Preprocessing**: StandardScaler + One-Hot Encoding → 26 features
3. **Baseline (LR)**: 86.42% accuracy, identified 1,358 errors
4. **Error Analysis**: Found 52% of errors are "confidently wrong" (prob > 0.7)
5. **XGBoost**: Captured interactions, achieved 92.86% accuracy
6. **Deployment**: Streamlit Cloud with real-time predictions

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.13 |
| ML | scikit-learn 1.8, XGBoost 3.2 |
| Visualization | Plotly, Seaborn, Matplotlib |
| Web App | Streamlit 1.54 |
| Deployment | Streamlit Cloud |
| Version Control | Git + GitHub |

## Author

**Mitul Bhatia**
- GitHub: [@mitul-bhatia](https://github.com/mitul-bhatia)
- Repository: [GEN_AI_LOAN_APPROVAL](https://github.com/mitul-bhatia/GEN_AI_LOAN_APPROVAL)

---

*Mid-Semester AI/ML Capstone Project | Newton School of Technology | February 2026*
