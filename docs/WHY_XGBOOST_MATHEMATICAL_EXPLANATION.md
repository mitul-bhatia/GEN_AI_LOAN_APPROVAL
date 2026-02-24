# The Complete Mathematical Journey: From Logistic Regression to XGBoost

## The Story: Why We Needed XGBoost

This document explains the full reasoning behind our model selection, the mathematical limitations we discovered, and how XGBoost overcame them.

---

## Chapter 1: Starting with Logistic Regression

### 1.1 Why We Chose Logistic Regression First

We didn't randomly pick Logistic Regression. It was a **deliberate, principled choice**:

1. **Industry Standard**: Banks use LR for credit scoring (Basel II/III compliance)
2. **Interpretability**: Coefficients have direct meaning (odds ratios)
3. **Linearity Test**: If LR works well, the problem is linearly separable

### 1.2 The Mathematical Model

Logistic Regression assumes the **log-odds** of approval is a **linear function** of features:

$$\log\left(\frac{P(Y=1)}{1-P(Y=1)}\right) = \beta_0 + \beta_1 X_1 + \beta_2 X_2 + ... + \beta_{26} X_{26}$$

Solving for probability:

$$P(Y=1|X) = \frac{1}{1 + e^{-(\beta_0 + \sum_{i=1}^{26} \beta_i X_i)}}$$

### 1.3 The Critical Assumption: ADDITIVITY

**This is the key limitation we discovered.**

LR assumes each feature contributes **independently and additively**:

$$\text{Total Effect} = \beta_1 X_1 + \beta_2 X_2 + \beta_3 X_3 + ...$$

**What this means:**
- The effect of `credit_score` is always $\beta_{cs}$, regardless of other features
- The effect of `DTI` is always $\beta_{dti}$, regardless of other features
- Features don't "interact" — they just add up

### 1.4 Our LR Results

| Metric | Value |
|--------|-------|
| Accuracy | 86.42% |
| ROC-AUC | 94.39% |
| Errors | 1,358 / 10,000 |

**Question**: Is 86% good enough, or can we do better?

---

## Chapter 2: Error Analysis — Finding the Problem

### 2.1 The Investigation

We analyzed the 1,358 errors to understand **what patterns LR was missing**.

**Key Statistics:**
- False Positives (approved but should reject): 735
- False Negatives (rejected but should approve): 623

### 2.2 Discovery #1: Confident Wrong Predictions

| Category | Count | Percentage |
|----------|-------|------------|
| FP with probability > 0.7 | 385 | 52.4% of FPs |
| FN with probability < 0.3 | 266 | 42.7% of FNs |
| Errors near boundary (0.4-0.6) | 375 | 27.6% of errors |

**Interpretation**: The model isn't just uncertain on edge cases — it's **confidently wrong** on many predictions. This suggests it's **systematically misunderstanding** something.

### 2.3 Discovery #2: Feature Interactions

We computed the correlation between features and errors:

| Feature | Correlation with Error |
|---------|----------------------|
| `credit_score` | -0.035 |
| `debt_to_income_ratio` | +0.034 |
| **`credit_score × DTI`** | **+0.166** |

**The interaction term predicts errors 5× better than individual features!**

---

## Chapter 3: Why Feature Interactions Break Logistic Regression

### 3.1 The Real-World Reality

In loan approval, features don't act independently. Consider these scenarios:

| Scenario | Credit Score | DTI | Reality | LR Prediction |
|----------|-------------|-----|---------|---------------|
| A | 750 (High) | 20% (Low) | ✅ Approve | ✅ Approve |
| B | 750 (High) | 60% (High) | ❌ Reject | ✅ **WRONG** |
| C | 550 (Low) | 20% (Low) | ✅ Approve | ❌ **WRONG** |
| D | 550 (Low) | 60% (High) | ❌ Reject | ❌ Reject |

### 3.2 Mathematical Explanation of LR's Failure

**For Scenario B (High Credit + High DTI):**

LR computes:
$$\text{Score} = \beta_0 + \beta_{cs} \cdot (\text{high}) + \beta_{dti} \cdot (\text{high})$$

Since $\beta_{cs} > 0$ (good credit helps) and $\beta_{dti} < 0$ (high debt hurts):
$$\text{Score} = \beta_0 + (\text{positive}) + (\text{negative})$$

If the positive credit effect is larger, the net score is positive → **Approve**

**But reality says:** "Even with excellent credit, if your debt is 60% of income, you can't afford more loans."

This is a **multiplicative relationship**, not additive:
$$\text{Reality} \approx f(\text{credit\_score} \times \text{DTI threshold check})$$

### 3.3 The Visualization

Imagine the feature space with Credit Score on X-axis and DTI on Y-axis:

```
DTI
 ↑
 │ ┌─────────────────┬─────────────────┐
 │ │                 │                 │
High│    REJECT       │    REJECT       │  ← Reality
 │ │  (LR correct)   │  (LR wrong:     │
 │ │                 │   approves)     │
 │ ├─────────────────┼─────────────────┤
 │ │                 │                 │
Low│    APPROVE      │    APPROVE      │
 │ │  (LR wrong:     │  (LR correct)   │
 │ │   rejects)      │                 │
 │ └─────────────────┴─────────────────┘
 └────────────────────────────────────→ Credit Score
        Low              High
```

**LR can only draw a diagonal line** (linear boundary):
- It cannot create the "rectangular" regions that reality requires
- It cannot say "High credit is good, UNLESS DTI is also high"

### 3.4 Mathematical Proof: LR Cannot Capture Interactions

The LR decision boundary is defined by:
$$\beta_0 + \beta_1 X_1 + \beta_2 X_2 = 0$$

Rearranging:
$$X_2 = -\frac{\beta_0}{\beta_2} - \frac{\beta_1}{\beta_2} X_1$$

This is a **straight line** in 2D (hyperplane in higher dimensions).

**To capture interactions**, we would need:
$$X_2 = f(X_1) \cdot g(X_1)$$

Or decision rules like:
$$\text{IF } X_1 > t_1 \text{ AND } X_2 > t_2 \text{ THEN Reject}$$

LR **cannot express this** without manual feature engineering.

---

## Chapter 4: Why Decision Trees Solve This

### 4.1 How Trees Work Differently

A Decision Tree doesn't assume linearity. It creates **rectangular regions** in feature space:

```python
IF credit_score > 650:
    IF dti < 0.4:
        APPROVE (Region 1)
    ELSE:
        REJECT (Region 2)  # <-- This captures the interaction!
ELSE:
    IF dti < 0.25:
        APPROVE (Region 3)
    ELSE:
        REJECT (Region 4)
```

### 4.2 Mathematical Representation

A tree partitions the feature space into $M$ regions $R_1, R_2, ..., R_M$:

$$f(X) = \sum_{m=1}^{M} c_m \cdot \mathbb{1}(X \in R_m)$$

Where:
- $R_m$ = a rectangular region (defined by axis-aligned splits)
- $c_m$ = the prediction for that region
- $\mathbb{1}(\cdot)$ = indicator function (1 if true, 0 if false)

### 4.3 Why Trees Capture Interactions Automatically

When a tree splits on `credit_score > 650`, then splits again on `dti < 0.4` within that branch:

**It has learned:**
$$\text{Decision} = f(\text{credit\_score}, \text{dti}) = \begin{cases} 
\text{Approve} & \text{if } cs > 650 \text{ AND } dti < 0.4 \\
\text{Reject} & \text{if } cs > 650 \text{ AND } dti \geq 0.4 \\
... & ...
\end{cases}$$

**The interaction is implicit in the tree structure!**

### 4.4 The Problem with Single Trees: High Variance

Single decision trees have a critical flaw: **overfitting**.

- Small changes in training data → completely different tree
- Memorizes noise → poor generalization

**Mathematically:**
$$\text{Prediction Error} = \text{Bias}^2 + \text{Variance} + \text{Irreducible Noise}$$

| Model | Bias | Variance |
|-------|------|----------|
| Logistic Regression | High (can't capture interactions) | Low |
| Single Decision Tree | Low (flexible) | **High** (overfits) |

---

## Chapter 5: XGBoost — The Solution

### 5.1 Two Key Ideas

XGBoost combines two powerful techniques:

1. **Ensemble**: Use many trees instead of one
2. **Boosting**: Build trees sequentially, focusing on previous errors

### 5.2 The Boosting Process

**Step 1**: Start with a simple prediction (e.g., average)
$$\hat{y}_i^{(0)} = \text{average}(y)$$

**Step 2**: Build Tree 1 to predict the **residual errors**
$$\hat{y}_i^{(1)} = \hat{y}_i^{(0)} + \eta \cdot f_1(x_i)$$

Where $\eta$ is the learning rate (step size).

**Step 3**: Build Tree 2 to predict the **remaining errors**
$$\hat{y}_i^{(2)} = \hat{y}_i^{(1)} + \eta \cdot f_2(x_i)$$

**Continue until:**
$$\hat{y}_i^{(T)} = \hat{y}_i^{(0)} + \eta \sum_{t=1}^{T} f_t(x_i)$$

### 5.3 Why Boosting Fixes LR's Errors

**After Iteration 0** (baseline):
- The model makes 1,358 errors (just like LR)

**After Iteration 1**:
- Tree 1 is built to specifically fix high-residual samples
- These are exactly the samples LR got confidently wrong!
- Fixes ~500 errors

**After Iteration 2**:
- Tree 2 focuses on remaining hard cases
- Learns finer threshold effects
- Fixes ~300 more

**By Iteration 200**:
- Total errors reduced to 714

### 5.4 The Gradient Descent Connection

XGBoost treats tree building as **gradient descent in function space**.

**Objective Function:**
$$\mathcal{L}^{(t)} = \sum_{i=1}^{n} L(y_i, \hat{y}_i^{(t-1)} + f_t(x_i)) + \Omega(f_t)$$

**Using Taylor expansion:**
$$\mathcal{L}^{(t)} \approx \sum_{i=1}^{n} \left[ g_i f_t(x_i) + \frac{1}{2} h_i f_t^2(x_i) \right] + \Omega(f_t)$$

Where:
- $g_i = \frac{\partial L}{\partial \hat{y}^{(t-1)}}$ — **Gradient** (first derivative)
- $h_i = \frac{\partial^2 L}{\partial (\hat{y}^{(t-1)})^2}$ — **Hessian** (second derivative)

**The gradient $g_i$ is largest for samples where the model is most wrong!**

This is why XGBoost focuses on hard cases — it's mathematically guaranteed by gradient descent.

### 5.5 Regularization: Preventing Overfitting

XGBoost adds regularization to prevent trees from overfitting:

$$\Omega(f_t) = \gamma T + \frac{1}{2}\lambda \sum_{j=1}^{T} w_j^2$$

| Term | Meaning | Effect |
|------|---------|--------|
| $\gamma T$ | Penalty on number of leaves | Prefer simpler trees |
| $\lambda \sum w_j^2$ | L2 penalty on leaf weights | Prevent extreme predictions |

**Our best parameters:**
- `max_depth = 5` (not too deep)
- `reg_lambda = 1` (moderate L2 penalty)
- `subsample = 0.8` (use 80% of data per tree)
- `colsample_bytree = 0.8` (use 80% of features per tree)

---

## Chapter 6: The Final Results

### 6.1 Performance Comparison

| Metric | Logistic Regression | XGBoost | Improvement |
|--------|--------------------| --------|-------------|
| Accuracy | 86.42% | **92.86%** | **+7.45%** |
| Precision | 86.91% | 92.65% | +6.60% |
| Recall | 88.68% | 94.53% | +6.60% |
| F1 Score | 87.79% | 93.58% | +6.60% |
| ROC-AUC | 94.39% | **98.42%** | +4.28% |

### 6.2 Error Analysis

| Category | Count |
|----------|-------|
| LR Errors | 1,358 |
| XGBoost Errors | 714 |
| **Fixed by XGBoost** | **886** |
| New XGBoost Errors | 242 |
| Both Wrong (Irreducible) | 472 |

### 6.3 What XGBoost Fixed

The 886 samples fixed by XGBoost had:
- **Higher DTI** (mean = 0.197 vs 0.000 overall) — confirms interaction capture
- **Fewer defaults** (mean = -0.239) — confirms threshold learning

These are exactly the scenarios we identified in Chapter 3!

---

## Chapter 7: Summary — The Complete Story

### 7.1 The Journey

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: EDA                                                         │
│   → Found strong linear correlations (credit_score: +0.50)         │
│   → Hypothesis: Linear model should work                            │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Logistic Regression                                         │
│   → Achieved 86.42% accuracy, 94.39% AUC                           │
│   → Good, but 1,358 errors — can we do better?                     │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: Error Analysis                                              │
│   → Discovery: 52% of errors are high-confidence wrong             │
│   → Discovery: credit_score × DTI interaction (r=0.166)            │
│   → Conclusion: LR's additive assumption is violated               │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: Mathematical Analysis                                       │
│   → LR: linear boundary (can't capture interactions)                │
│   → Trees: rectangular regions (capture interactions naturally)     │
│   → Boosting: focuses on hard cases via gradient descent           │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: XGBoost Implementation                                      │
│   → 92.86% accuracy (+7.45% improvement)                           │
│   → Fixed 886 of LR's 1,358 errors                                 │
│   → 472 errors remain (irreducible noise in data)                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Key Takeaways

1. **Always Start Simple**: LR gave us a baseline and revealed the problem
2. **Analyze Errors**: Don't just accept accuracy — understand failures
3. **Mathematical Reasoning**: The interaction correlation told us LR's assumption was violated
4. **Right Tool for the Job**: XGBoost's tree structure naturally captures what LR couldn't

### 7.3 Why NOT Deep Learning?

| Factor | XGBoost | Deep Learning |
|--------|---------|---------------|
| Tabular data performance | ✅ Excellent | ❌ Often worse than trees |
| Training data needed | 40,000 sufficient | Needs millions |
| Feature interactions | Automatic via splits | Needs more layers |
| Interpretability | Feature importance | Black box |
| Training time | ~20 seconds | Minutes to hours |

**Research shows**: For tabular data, gradient boosting (XGBoost, LightGBM) consistently outperforms neural networks.

---

## Appendix: Mathematical Symbols Reference

| Symbol | Meaning |
|--------|---------|
| $P(Y=1\|X)$ | Probability of approval given features X |
| $\beta_i$ | Logistic regression coefficient for feature i |
| $\sigma(z)$ | Sigmoid function: $\frac{1}{1+e^{-z}}$ |
| $\mathcal{L}$ | Loss function |
| $g_i$ | Gradient (first derivative of loss) |
| $h_i$ | Hessian (second derivative of loss) |
| $f_t(x)$ | Tree t's prediction |
| $\eta$ | Learning rate |
| $\gamma$ | Leaf count penalty |
| $\lambda$ | L2 regularization strength |
| $\Omega(f)$ | Regularization term |
| $R_m$ | Region m in feature space |
| $\mathbb{1}(\cdot)$ | Indicator function |

---

*This document is part of the Loan Approval Prediction project for educational purposes.*
