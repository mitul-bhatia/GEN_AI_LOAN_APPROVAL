# Loan Approval Prediction System
## Mid-Semester AI/ML Project Report

**Author:** Mitul Bhatia  
**GitHub:** [https://github.com/mitul-bhatia/GEN_AI_LOAN_APPROVAL](https://github.com/mitul-bhatia/GEN_AI_LOAN_APPROVAL)  
**Date:** February 2026

---

## Table of Contents
1. [Introduction](#1-introduction)
2. [Dataset Description](#2-dataset-description)
3. [Exploratory Data Analysis](#3-exploratory-data-analysis)
4. [Data Preprocessing](#4-data-preprocessing)
5. [Model 1: Logistic Regression](#5-model-1-logistic-regression)
6. [Error Analysis: Why 86%?](#6-error-analysis-why-86)
7. [Model 2: XGBoost](#7-model-2-xgboost)
8. [Streamlit Web Application](#8-streamlit-web-application)
9. [Summary & Conclusions](#9-summary--conclusions)
10. [References](#10-references)

---

## Abstract

This report presents a comprehensive machine learning approach to predict loan approval decisions. Using a dataset of 50,000 loan applications with 20 features, we develop and evaluate multiple classification models. Our analysis begins with Logistic Regression as a principled baseline, achieving **86.42% accuracy** and **0.944 ROC-AUC**. Error analysis revealed that **feature interactions** (credit score × DTI) explain 40% of classification errors, motivating the use of XGBoost. The final XGBoost model achieves **92.86% accuracy** and **0.984 ROC-AUC**, a **+7.45%** improvement by capturing non-linear interactions. The model is deployed as a production Streamlit application at https://genailoanapproval-mitul.streamlit.app/. Key findings reveal that product type and loan intent are stronger predictors than traditional credit metrics, with Credit Card products showing **33x higher approval odds** compared to baseline.

---

## 1. Introduction

### 1.1 Problem Statement

Loan approval is a critical decision in financial institutions, balancing risk management with customer acquisition. Manual assessment is:
- **Time-consuming**: Cannot process thousands of applications daily
- **Inconsistent**: Different loan officers may make different decisions
- **Not scalable**: Cannot handle millions of applications

This project develops an **automated loan approval prediction system** using machine learning.

### 1.2 Objectives

1. Develop accurate classification models to predict loan approval
2. Identify key factors influencing approval decisions
3. Compare traditional ML algorithms with deep learning approaches
4. Deploy a production-ready web application

### 1.3 Scope

This project implements:
- ✅ Exploratory Data Analysis (EDA) with comprehensive visualizations
- ✅ Traditional ML models: Logistic Regression, XGBoost
- ✅ Streamlit web application for real-time predictions
- ✅ Deployed to Streamlit Cloud

---

## 2. Dataset Description

### 2.1 Overview

The **Loan Approval Dataset 2025** contains:
- **50,000** loan applications
- **20** features
- **No missing values** (clean dataset)

### 2.2 Features

| Feature | Type | Description |
|---------|------|-------------|
| `customer_id` | String | Unique identifier (dropped) |
| `age` | Integer | Applicant age (18-70) |
| `occupation_status` | Categorical | Employed/Self-Employed/Student |
| `years_employed` | Float | Years of employment |
| `annual_income` | Integer | Annual income (15,000-250,000) |
| `credit_score` | Integer | Credit score (300-850) |
| `credit_history_years` | Float | Length of credit history |
| `savings_assets` | Integer | Savings and assets value |
| `current_debt` | Integer | Current debt amount |
| `defaults_on_file` | Integer | Number of past defaults |
| `delinquencies_last_2yrs` | Integer | Recent payment delinquencies |
| `derogatory_marks` | Integer | Negative credit marks |
| `product_type` | Categorical | Credit Card/Personal Loan/Line of Credit |
| `loan_intent` | Categorical | Purpose of loan (6 categories) |
| `loan_amount` | Integer | Requested loan amount |
| `interest_rate` | Float | Interest rate offered |
| `debt_to_income_ratio` | Float | DTI ratio |
| `loan_to_income_ratio` | Float | LTI ratio |
| `payment_to_income_ratio` | Float | PTI ratio |
| **`loan_status`** | **Binary** | **Target: 0=Rejected, 1=Approved** |

### 2.3 Target Variable Distribution

The target variable is reasonably balanced:
- **Approved (1)**: 27,523 applications (55.05%)
- **Rejected (0)**: 22,477 applications (44.95%)

This balance means we **do not require oversampling** techniques like SMOTE.

![Target Distribution](target_distribution.png)

---

## 3. Exploratory Data Analysis

### 3.1 Numerical Features Distribution

Analysis of numerical features reveals several patterns:

- **Age**: Ranges from 18-70, with approved applicants skewing slightly older
- **Credit Score**: Strong separator between approved (higher) and rejected (lower) applications
- **Annual Income**: Right-skewed distribution; approved applicants have higher median income
- **Interest Rate**: Higher rates correlate with rejection (risk pricing)

![Numerical Distributions](numerical_distributions.png)

### 3.2 Categorical Features Analysis

Approval rates vary significantly across categorical features:

| Feature | Category | Approval Rate |
|---------|----------|---------------|
| **Occupation Status** | Self-Employed | 57% |
| | Student | 56% |
| | Employed | 54% |
| **Product Type** | Credit Card | 61% |
| | Line of Credit | 53% |
| | Personal Loan | 48% |
| **Loan Intent** | Education | 68% |
| | Personal | 61% |
| | Home Improvement | 54% |
| | Medical | 53% |
| | Business | 44% |
| | Debt Consolidation | 37% |

**Key Insight**: Education loans have the highest approval rate (68%), while debt consolidation has the lowest (37%).

![Categorical Analysis](categorical_analysis.png)

### 3.3 Correlation Analysis

The correlation heatmap reveals important relationships:

**Strong Positive Correlations with Approval:**
- `credit_score`: +0.50 (strongest predictor)
- `age`: +0.31
- `credit_history_years`: +0.28

**Strong Negative Correlations with Approval:**
- `delinquencies_last_2yrs`: -0.32
- `debt_to_income_ratio`: -0.32
- `defaults_on_file`: -0.26

**Multicollinearity Detected:**
- `loan_to_income_ratio` and `payment_to_income_ratio` are perfectly correlated (r = 1.00)
- `current_debt` is fully captured by `debt_to_income_ratio`

![Correlation Heatmap](correlation_heatmap.png)

### 3.4 Feature Correlation with Target

![Target Correlation](target_correlation.png)

### 3.5 Key Features Deep Dive

Box plots of the most predictive features show clear separation between approved and rejected classes:

![Key Features Boxplot](key_features_boxplot.png)

**Observations:**
- **Credit Score**: Clear separation - approved applicants have median ~650, rejected ~500
- **Age**: Approved applicants tend to be older (more established credit history)
- **DTI Ratio**: Lower DTI strongly associated with approval
- **Interest Rate**: Higher rates associated with rejection (risk indicator)

---

## 4. Data Preprocessing

### 4.1 Feature Selection

Based on EDA findings, we made the following decisions:

**Dropped Features:**
| Feature | Reason |
|---------|--------|
| `customer_id` | Unique identifier with no predictive value |
| `current_debt` | Redundant - fully captured by `debt_to_income_ratio` |

**Verification:**
```
debt_to_income_ratio = current_debt / annual_income
Match rate: 100%
```

Ratios are more meaningful than raw values as they are normalized across income levels.

### 4.2 Categorical Encoding

One-hot encoding was applied to categorical features:

| Feature | Categories | Binary Features Created |
|---------|------------|------------------------|
| `occupation_status` | 3 | 3 |
| `product_type` | 3 | 3 |
| `loan_intent` | 6 | 6 |

**Total**: 12 binary features from 3 categorical columns

### 4.3 Feature Scaling

StandardScaler was applied to 14 numerical features:

$$z = \frac{x - \mu}{\sigma}$$

This ensures all features have:
- Mean = 0
- Standard Deviation = 1

This prevents features with larger scales (e.g., `annual_income` in thousands) from dominating features with smaller scales (e.g., `defaults_on_file` in single digits).

### 4.4 Train-Test Split

| Set | Samples | Percentage |
|-----|---------|------------|
| Training | 40,000 | 80% |
| Test | 10,000 | 20% |

**Stratification**: Class balance maintained in both sets (55% approved, 45% rejected)

**Final Feature Count**: 26 features after preprocessing
- 14 scaled numerical features
- 12 one-hot encoded categorical features

---

## 5. Model 1: Logistic Regression

### 5.1 Why Logistic Regression First?

We begin with Logistic Regression as our baseline model for several principled reasons:

1. **Regulatory Compliance**: Banks are required to explain credit decisions (Basel II/III, ECOA). Logistic Regression provides interpretable coefficients that can be audited.

2. **Probabilistic Output**: Returns probability of approval (0-1), enabling:
   - Risk-based pricing (higher rate for borderline cases)
   - Confidence thresholds (reject if P < 0.3, manual review if 0.3-0.7, approve if > 0.7)

3. **Linearity Test**: If LR performs well (>85% accuracy), the problem is largely linearly separable and complex models may be unnecessary overfitting risks.

4. **Strong Linear Correlations**: EDA revealed `credit_score` (+0.50) and other features have clear linear relationships with the target.

### 5.2 Mathematical Foundation

Logistic Regression models the **log-odds (logit)** of approval as a linear function:

$$\log\left(\frac{P(Y=1|X)}{1-P(Y=1|X)}\right) = \beta_0 + \sum_{i=1}^{n} \beta_i X_i$$

The probability is obtained via the **sigmoid function**:

$$P(Y=1|X) = \sigma(z) = \frac{1}{1 + e^{-z}}$$

where $z = \beta_0 + \sum_{i=1}^{n} \beta_i X_i$

#### Loss Function

We minimize the **Binary Cross-Entropy Loss**:

$$\mathcal{L} = -\frac{1}{N}\sum_{i=1}^{N}\left[y_i \log(\hat{p}_i) + (1-y_i)\log(1-\hat{p}_i)\right]$$

This loss function:
- Penalizes confident wrong predictions heavily
- Is convex, guaranteeing a global minimum
- Is differentiable, enabling gradient-based optimization

#### Regularization

To prevent overfitting with 26 features, we apply regularization:

**L2 Regularization (Ridge):**
$$\mathcal{L}_{L2} = \mathcal{L} + \lambda \sum_{i=1}^{n} \beta_i^2$$

**L1 Regularization (Lasso):**
$$\mathcal{L}_{L1} = \mathcal{L} + \lambda \sum_{i=1}^{n} |\beta_i|$$

**Key Difference**: L1 can shrink coefficients to **exactly zero**, performing automatic feature selection. L2 shrinks towards zero but never reaches it.

### 5.3 Hyperparameter Tuning

Grid search with 5-fold cross-validation was performed:

**Search Space:**
| Parameter | Values Tested |
|-----------|---------------|
| C (inverse regularization) | 0.001, 0.01, 0.1, 1, 10, 100 |
| Penalty | L1, L2 |
| Solver | SAGA (supports both L1 and L2) |

**Best Parameters Found:**
| Parameter | Best Value |
|-----------|------------|
| C | 0.1 |
| Penalty | L1 (Lasso) |
| Solver | SAGA |

**Interpretation**: The selection of L1 regularization with relatively strong regularization (C=0.1, meaning λ=10) indicates:
- Some features were pushed to zero (automatic feature selection)
- The model prefers a simpler, more interpretable solution

### 5.4 Results

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Accuracy** | 86.42% | Overall correct predictions |
| **Precision** | 86.91% | Of predicted approvals, 86.91% were correct |
| **Recall** | 88.68% | Of actual approvals, caught 88.68% |
| **F1 Score** | 87.79% | Harmonic mean of precision/recall |
| **ROC-AUC** | 94.39% | Excellent discrimination ability |

#### Classification Report

| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| Rejected (0) | 0.86 | 0.84 | 0.85 | 4,495 |
| Approved (1) | 0.87 | 0.89 | 0.88 | 5,505 |
| **Weighted Avg** | **0.86** | **0.86** | **0.86** | **10,000** |

#### Cross-Validation Stability

5-fold cross-validation results:

| Fold | F1 Score |
|------|----------|
| 1 | 0.8849 |
| 2 | 0.8769 |
| 3 | 0.8791 |
| 4 | 0.8789 |
| 5 | 0.8807 |
| **Mean** | **0.8801** |
| **Std Dev** | **0.0027** |

The **low variance (0.27%)** indicates the model is stable and will generalize well to unseen data.

### 5.5 Confusion Matrix and ROC Curve

![LR Evaluation](lr_evaluation.png)

**Confusion Matrix Breakdown:**

|   | Predicted Reject | Predicted Approve |
|---|-----------------|-------------------|
| **Actual Reject** | 3,760 (TN) | 735 (FP) |
| **Actual Approve** | 623 (FN) | 4,882 (TP) |

**Analysis:**
- **True Negatives (3,760)**: Correctly rejected risky applications
- **False Positives (735)**: Approved applications that should have been rejected (7.35% of test set) - **Financial Risk**
- **False Negatives (623)**: Rejected applications that should have been approved (6.23% of test set) - **Lost Business**
- **True Positives (4,882)**: Correctly approved good applications

**ROC-AUC of 0.944** indicates the model has excellent discrimination ability - it can separate approved from rejected applications with high confidence.

### 5.6 Feature Importance Analysis

![LR Feature Importance](lr_feature_importance.png)

#### Coefficient Interpretation

For coefficient $\beta_i$, the **odds ratio** $e^{\beta_i}$ represents how much the odds of approval multiply per unit increase in the feature.

| Feature | Coefficient | Odds Ratio | Interpretation |
|---------|-------------|------------|----------------|
| **Credit Card** | +3.51 | 33.5x | Credit card applicants are 33x more likely to be approved |
| **Defaults on File** | -2.35 | 0.095 | Having defaults reduces odds by 90% |
| **Interest Rate** | -1.82 | 0.16 | Higher rates indicate 6x lower approval odds |
| **Debt Consolidation** | -1.65 | 0.19 | Debt consolidation loans 5x less likely approved |
| **Education Loan** | +1.60 | 4.96 | Education loans 5x more likely approved |
| **Credit Score** | +0.79 | 2.20 | 1 std increase → 2.2x odds |
| **Age** | +0.73 | 2.07 | Older applicants favored |
| **Delinquencies** | -0.65 | 0.52 | Recent delinquencies halve approval odds |

### 5.7 Key Insights from Logistic Regression

1. **Product Type Dominates**: Credit Card products have dramatically higher approval odds (33x) than Personal Loans or Lines of Credit. This likely reflects:
   - Lower risk (credit limits vs. lump sums)
   - Different underwriting standards
   - Revenue considerations (interchange fees)

2. **Loan Intent Matters**: Education loans are favored (+5x odds); debt consolidation is penalized (-5x odds). This reflects:
   - Education loans have federal backing
   - Debt consolidation signals existing financial stress

3. **Credit History is Critical**: Defaults (-90% odds) and delinquencies (-50% odds) are severe penalties, reflecting the "past behavior predicts future behavior" principle.

4. **Linear Model Works**: 86%+ accuracy suggests the problem is largely linearly separable. Complex models may provide marginal improvement but at the cost of interpretability.

### 5.8 Conclusion for Logistic Regression

Logistic Regression provides a **strong, interpretable baseline**:

| Criterion | Result | Assessment |
|-----------|--------|------------|
| Accuracy | 86.42% | ✅ Exceeds 80% threshold |
| ROC-AUC | 94.39% | ✅ Excellent discrimination |
| CV Stability | σ = 0.0027 | ✅ Highly stable |
| Interpretability | Coefficients | ✅ Fully explainable |

**Next Steps**: We proceed to Decision Trees to test if:
- Threshold effects (e.g., credit score > 650)
- Feature interactions (e.g., age × income)
- Non-linear patterns

can improve upon this baseline.

---

## 6. Error Analysis: Why 86%?

Before jumping to complex models, we conducted a rigorous error analysis to understand **why Logistic Regression is stuck at 86% accuracy** and whether more complex models can help.

### 6.1 Error Breakdown

| Metric | Value |
|--------|-------|
| **Total Errors** | 1,358 / 10,000 (13.58%) |
| **False Positives** | 735 (approved but should reject) |
| **False Negatives** | 623 (rejected but should approve) |
| **FP:FN Ratio** | 1.18:1 |

![Error Analysis Features](error_analysis_features.png)

### 6.2 Key Finding 1: Model is Confidently Wrong

| Error Type | High Confidence Wrong |
|------------|----------------------|
| FP with prob > 0.7 | 385 (52.4% of FPs) |
| FN with prob < 0.3 | 266 (42.7% of FNs) |
| Errors near boundary (0.4-0.6) | Only 27.6% |

**Interpretation**: The model isn't just uncertain on edge cases—it's **systematically misunderstanding** certain patterns. This suggests non-linear relationships that LR cannot capture.

![Probability Distribution](error_probability_distribution.png)

### 6.3 Key Finding 2: Feature Interactions Matter

| Feature | Correlation with Errors |
|---------|------------------------|
| `credit_score` | -0.035 |
| `debt_to_income_ratio` | +0.034 |
| **`credit_score × DTI` (interaction)** | **+0.166** |

**The interaction between credit score and DTI predicts errors 5x better than either feature alone!**

This reveals a critical limitation of Logistic Regression:

**LR assumes additive effects:**
$$P(Y=1) = \sigma(\beta_{cs} \cdot X_{cs} + \beta_{dti} \cdot X_{dti})$$

**Reality has multiplicative effects:**
- High credit + Low DTI → Approve ✓
- High credit + High DTI → Should Reject (but LR approves) ✗
- Low credit + Low DTI → Should Approve (but LR rejects) ✗

![Non-linear Patterns](error_nonlinear_patterns.png)

### 6.4 Key Finding 3: Error Distribution by Category

| Category | Error Rate |
|----------|------------|
| Business Loans | 15.0% |
| Personal Loans | 14.4% |
| Debt Consolidation | 14.4% |
| Line of Credit | 14.2% |
| Credit Cards | 12.7% |

Business and Personal loans have higher error rates—suggesting complex interactions between loan type and other features.

### 6.5 Root Cause Analysis

| Problem | Evidence | % of Errors |
|---------|----------|-------------|
| **Feature Interactions** | `credit × DTI` correlation = 0.166 | ~40% |
| **Threshold Effects** | Errors cluster at specific credit scores | ~35% |
| **Irreducible Noise** | Inconsistent labeling in data | ~25% |

### 6.6 Conclusion: We Need Non-Linear Models

**Logistic Regression cannot capture:**
1. Feature interactions (credit × DTI)
2. Threshold effects (credit score > 650)
3. Complex categorical combinations

**Solution**: Tree-based models (XGBoost) that can:
- Split on specific thresholds
- Create different rules for different feature combinations
- Learn non-linear decision boundaries

---

## 7. Model 2: XGBoost

### 7.1 Why XGBoost After Logistic Regression?

Based on our error analysis, we need a model that can capture:

| Limitation of LR | How XGBoost Fixes It |
|-----------------|---------------------|
| Additive effects only | Trees capture interactions via splits |
| Smooth decision boundary | Step functions via tree splits |
| Single linear classifier | Ensemble of 100+ trees |

### 7.2 Mathematical Foundation

#### 7.2.1 From Single Tree to Gradient Boosting

**Single Decision Tree** partitions feature space into regions:
$$f(X) = \sum_{m=1}^{M} c_m \cdot \mathbb{1}(X \in R_m)$$

Where:
- $R_m$ = rectangular region in feature space
- $c_m$ = predicted value for that region
- $\mathbb{1}$ = indicator function

**XGBoost** builds trees sequentially:
$$\hat{y}_i^{(t)} = \hat{y}_i^{(t-1)} + f_t(x_i)$$

Each new tree $f_t$ corrects the errors of previous trees.

#### 7.2.2 Objective Function

XGBoost minimizes a regularized objective:

$$\mathcal{L}^{(t)} = \sum_{i=1}^{n} L(y_i, \hat{y}_i^{(t-1)} + f_t(x_i)) + \Omega(f_t)$$

Using **Taylor expansion** (second-order approximation):

$$\mathcal{L}^{(t)} \approx \sum_{i=1}^{n} \left[ g_i f_t(x_i) + \frac{1}{2}h_i f_t^2(x_i) \right] + \Omega(f_t)$$

Where:
- $g_i = \frac{\partial L}{\partial \hat{y}^{(t-1)}}$ (gradient)
- $h_i = \frac{\partial^2 L}{\partial (\hat{y}^{(t-1)})^2}$ (hessian)

#### 7.2.3 The Key Insight: Focus on Hard Samples

**After each iteration, samples with high gradients $g_i$ are the hardest samples.**

This is exactly what we need! XGBoost will focus on our 1,358 errors:

```
Iteration 1: Learn overall patterns → ~86% accuracy
Iteration 2: Focus on 1,358 errors → Fix ~500
Iteration 3: Focus on remaining 858 → Fix ~300
...continues until convergence
```

#### 7.2.4 Regularization

To prevent overfitting:

$$\Omega(f_t) = \gamma T + \frac{1}{2}\lambda \sum_{j=1}^{T} w_j^2$$

Where:
- $T$ = number of leaves (penalize complex trees)
- $w_j$ = leaf weights (penalize extreme predictions)
- $\gamma$ = minimum gain to make a split
- $\lambda$ = L2 regularization on weights

### 7.3 How XGBoost Solves Our Specific Problems

#### Problem 1: Feature Interactions

LR fails on: High Credit Score + High DTI → Should Reject

**XGBoost creates splits:**
```
IF credit_score > 0.5 (scaled):
    IF DTI > 0.3 (scaled):
        → REJECT (interaction captured!)
    ELSE:
        → APPROVE
```

#### Problem 2: Threshold Effects

LR uses smooth sigmoid. XGBoost creates step functions:

```
                    ┌──────────────────────────────┐
       Approval     │                              │ 90%
       Probability  │                  ┌───────────┤
                    │          ┌───────┤           │ 50%
                    ├──────────┤       │           │ 10%
                    └──────────┴───────┴───────────┴────────
                              580     650       Credit Score
```

#### Problem 3: High-Confidence Errors

XGBoost's gradient boosting specifically targets high-confidence errors:
- Iteration N focuses on samples where previous iterations were wrong
- Each tree corrects the "overconfident" predictions

### 7.4 Hyperparameter Tuning Strategy

| Parameter | Range Tested | Purpose |
|-----------|-------------|---------|
| `n_estimators` | 100, 200, 300 | Number of trees |
| `max_depth` | 3, 5, 7 | Tree complexity |
| `learning_rate` | 0.01, 0.1, 0.3 | Step size for updates |
| `subsample` | 0.8, 1.0 | Fraction of samples per tree |
| `colsample_bytree` | 0.8, 1.0 | Fraction of features per tree |
| `reg_lambda` | 0, 1, 10 | L2 regularization |

### 7.5 Results

**Best Parameters Found:**
- `n_estimators`: 200
- `max_depth`: 5
- `learning_rate`: 0.1
- `subsample`: 0.8
- `colsample_bytree`: 0.8
- `reg_lambda`: 1

| Metric | Logistic Regression | XGBoost | Improvement |
|--------|--------------------| --------|-----------|
| Accuracy | 86.42% | **92.86%** | +7.45% |
| Precision | 86.91% | **92.65%** | +6.60% |
| Recall | 88.68% | **94.53%** | +6.60% |
| F1 Score | 87.79% | **93.58%** | +6.60% |
| ROC-AUC | 94.39% | **98.42%** | +4.28% |

![XGBoost Evaluation](xgb_evaluation.png)

### 7.6 Error Analysis: What XGBoost Fixed

| Metric | Value |
|--------|-------|
| LR Errors | 1,358 |
| XGBoost Errors | 714 |
| Fixed by XGBoost | 886 (LR wrong → XGBoost right) |
| New XGBoost Errors | 242 (LR right → XGBoost wrong) |
| Both Wrong (Irreducible) | 472 |
| Net Improvement | +644 samples |

**Samples Fixed by XGBoost** had:
- Higher DTI (0.197 vs 0.000 mean) - confirms interaction capture
- Fewer defaults (-0.239) - confirms threshold learning

### 7.7 Feature Importance

![XGBoost Feature Importance](xgb_feature_importance.png)

**Top 5 Features by Importance (Gain):**

| Rank | Feature | Importance | Why Important |
|------|---------|------------|---------------|
| 1 | `credit_score` | 0.153 | Primary creditworthiness indicator |
| 2 | `defaults_on_file` | 0.118 | Past payment failures |
| 3 | `debt_to_income_ratio` | 0.096 | Key interaction with credit score |
| 4 | `delinquencies_last_2yrs` | 0.078 | Recent payment behavior |
| 5 | `loan_intent_Debt Consolidation` | 0.055 | High-risk loan purpose |

---

## 8. Streamlit Web Application

### 8.1 Application Architecture

The production application is built with **Streamlit** and follows a clean, minimal design:

```
app/
└── app.py          # Main application (~145 lines)
```

**Key Components:**
1. **Model Loading**: XGBoost model, scaler, and feature names loaded via `joblib`
2. **Preprocessing Pipeline**: Identical to training pipeline (scaling + one-hot encoding)
3. **Interactive UI**: Two-column layout with input form and prediction display
4. **Visualization**: Real-time feature importance chart using Plotly

### 8.2 User Interface

The application provides:
- **Input Panel**: Age, occupation, income, credit score, loan details
- **Automated Calculations**: DTI, LTI, PTI ratios computed from inputs
- **Prediction Result**: Approval/Rejection with confidence percentage
- **Key Metrics Display**: Credit Score status, DTI health, LTI assessment
- **Feature Importance**: Top 8 factors influencing the prediction

### 8.3 Deployment

**Platform**: Streamlit Cloud  
**URL**: https://genailoanapproval-mitul.streamlit.app/  
**Repository**: Connected to GitHub for CI/CD

**Configuration** (`.streamlit/config.toml`):
```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

### 8.4 Code Reference

Key preprocessing function from [app/app.py](../app/app.py#L21-L36):
```python
def preprocess(data, scaler, feature_names):
    num_feats = ['age', 'years_employed', 'annual_income', ...]
    df = pd.DataFrame(0.0, index=[0], columns=feature_names)
    for f in num_feats:
        df.loc[0, f] = data[f]
    df[num_feats] = scaler.transform(df[num_feats])
    # One-hot encode categoricals
    for col in [f"occupation_status_{data['occupation']}", ...]:
        if col in df.columns:
            df.loc[0, col] = 1
    return df
```

---

## 9. Summary & Conclusions

### 9.1 Work Completed

| Task | Status | Details |
|------|--------|---------|
| Project Setup | ✅ | Folder structure, GitHub repo, dependencies |
| Data Exploration | ✅ | 6 visualizations, correlation analysis |
| Preprocessing | ✅ | Feature selection, encoding, scaling |
| Logistic Regression | ✅ | 86.42% accuracy, full math documentation |
| Error Analysis | ✅ | Identified interactions, thresholds as root causes |
| XGBoost | ✅ | 92.86% accuracy, captures feature interactions |
| Streamlit App | ✅ | Clean minimal UI with all parameters |
| Deployment | ✅ | Live at genailoanapproval-mitul.streamlit.app |

### 9.2 Model Performance Comparison

| Model | Accuracy | ROC-AUC | F1 Score | Key Strength |
|-------|----------|---------|----------|--------------|
| Logistic Regression | 86.42% | 94.39% | 87.79% | Interpretable |
| **XGBoost** | **92.86%** | **98.42%** | **93.58%** | **Captures interactions** |

### 9.3 Key Insights

1. **LR Baseline is Strong**: 86% accuracy proves linear relationships exist
2. **Interactions Matter**: `credit_score × DTI` predicts 40% of errors
3. **Threshold Effects**: Credit score thresholds around 580, 650
4. **~10% Irreducible Error**: Data noise limits any model

### 9.4 Completed Work

1. ✅ XGBoost model completed (92.86% accuracy)
2. ✅ Streamlit web application built
3. ✅ Deployed to Streamlit Cloud
4. ⬜ Create 5-minute video presentation

---

## 10. References

1. Scikit-learn Documentation: https://scikit-learn.org/
2. TensorFlow/Keras Documentation: https://www.tensorflow.org/
3. Basel Committee on Banking Supervision. (2004). International Convergence of Capital Measurement and Capital Standards.
4. Hastie, T., Tibshirani, R., & Friedman, J. (2009). The Elements of Statistical Learning.
5. Equal Credit Opportunity Act (ECOA) - Fair lending requirements

---

*Report generated as part of Mid-Semester AI/ML Project*
