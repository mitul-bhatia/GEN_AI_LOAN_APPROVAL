# Loan Approval Prediction System

A Machine Learning and Deep Learning-based system to predict loan approval status using traditional ML algorithms and neural networks.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.13+-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![License](https://img.shields.io/badge/License-MIT-green)

## Table of Contents
- [Overview](#overview)
- [Dataset](#dataset)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Models](#models)
- [Results](#results)
- [Live Demo](#live-demo)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project aims to predict whether a loan application will be approved or rejected based on various applicant features such as credit score, annual income, employment status, and more. The system implements multiple ML algorithms and a deep learning model to achieve optimal prediction accuracy.

### Key Features
- Exploratory Data Analysis (EDA) with comprehensive visualizations
- Multiple ML models: Logistic Regression, Random Forest, XGBoost, SVM, KNN
- Deep Learning model using TensorFlow/Keras
- Interactive Streamlit web application for predictions
- Deployed on Streamlit Cloud for easy access

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
│   └── loan_approval_data.csv      # Dataset
├── notebooks/
│   ├── 01_EDA.ipynb                # Exploratory Data Analysis
│   ├── 02_Preprocessing.ipynb      # Data Preprocessing
│   ├── 03_ML_Models.ipynb          # Traditional ML Models
│   └── 04_Deep_Learning.ipynb      # Neural Network Model
├── src/
│   ├── __init__.py
│   ├── data_preprocessing.py       # Preprocessing utilities
│   ├── feature_engineering.py      # Feature engineering
│   ├── train_ml.py                 # ML training script
│   ├── train_dl.py                 # DL training script
│   └── utils.py                    # Utility functions
├── models/
│   ├── best_model.pkl              # Saved best model
│   └── scaler.pkl                  # Saved preprocessor
├── app/
│   └── streamlit_app.py            # Streamlit application
├── report/
│   └── main.tex                    # LaTeX project report
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── .gitignore                      # Git ignore file
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

## Models

### Traditional Machine Learning
| Model | Description |
|-------|-------------|
| Logistic Regression | Baseline linear classifier |
| Random Forest | Ensemble of decision trees |
| XGBoost | Gradient boosting algorithm |
| SVM | Support Vector Machine with RBF kernel |
| KNN | K-Nearest Neighbors |

### Deep Learning
- **Architecture**: Fully Connected Neural Network
- **Layers**: Input → Dense(128) → Dense(64) → Dense(32) → Output(1)
- **Activation**: ReLU (hidden), Sigmoid (output)
- **Optimizer**: Adam
- **Loss**: Binary Cross-Entropy

## Results

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|-------|----------|-----------|--------|----------|---------|
| Logistic Regression | - | - | - | - | - |
| Random Forest | - | - | - | - | - |
| XGBoost | - | - | - | - | - |
| Neural Network | - | - | - | - | - |

*Results will be updated after training*

## Live Demo

🌐 **[Try the Live App](https://your-app.streamlit.app)**

## Tech Stack

- **Data Processing**: Pandas, NumPy
- **Visualization**: Matplotlib, Seaborn, Plotly
- **ML**: Scikit-learn, XGBoost, LightGBM
- **Deep Learning**: TensorFlow/Keras
- **Web App**: Streamlit
- **Deployment**: Streamlit Cloud

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

## Acknowledgments

- Dataset source
- Course instructors and TAs
- Open-source community

---
*This project is part of the Mid-Semester AI/ML Project evaluation.*
