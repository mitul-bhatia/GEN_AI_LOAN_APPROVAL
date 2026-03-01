import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Loan Approval Predictor", page_icon="🏦", layout="wide")


@st.cache_resource
def load_model():
    roots = [Path(__file__).parent.parent, Path.cwd(), Path.cwd().parent]
    for root in roots:
        m = root / "models" / "xgboost.pkl"
        s = root / "data" / "processed" / "scaler.pkl"
        f = root / "data" / "processed" / "feature_names.pkl"
        if m.exists() and s.exists() and f.exists():
            return joblib.load(m), joblib.load(s), joblib.load(f)
    raise FileNotFoundError("Model files not found")


def preprocess(data, scaler, feature_names):
    num_feats = [
        "age",
        "years_employed",
        "annual_income",
        "credit_score",
        "credit_history_years",
        "savings_assets",
        "defaults_on_file",
        "delinquencies_last_2yrs",
        "derogatory_marks",
        "loan_amount",
        "interest_rate",
        "debt_to_income_ratio",
        "loan_to_income_ratio",
        "payment_to_income_ratio",
    ]

    df = pd.DataFrame(0.0, index=[0], columns=feature_names, dtype=np.float64)
    for f in num_feats:
        if f in data:
            df.loc[0, f] = data[f]

    df[num_feats] = scaler.transform(df[num_feats])

    for col in [
        f"occupation_status_{data['occupation']}",
        f"product_type_{data['product']}",
        f"loan_intent_{data['intent']}",
    ]:
        if col in df.columns:
            df.loc[0, col] = 1
    return df


def main():
    try:
        model, scaler, feature_names = load_model()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    st.title("🏦 Loan Approval Prediction")
    st.caption("XGBoost Model · 92.86% Accuracy · 50,000 training samples")
    st.divider()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Applicant Details")

        age = st.number_input("Age", 18, 70, 35)
        occupation = st.selectbox(
            "Occupation", ["Employed", "Self-Employed", "Student"]
        )
        years_employed = st.number_input("Years Employed", 0.0, 40.0, 5.0, 0.5)
        annual_income = st.number_input("Annual Income ($)", 15000, 500000, 75000, 5000)
        savings = st.number_input("Savings & Assets ($)", 0, 500000, 20000, 5000)

        st.subheader("Credit History")
        credit_score = st.slider("Credit Score", 300, 850, 700)
        credit_history = st.number_input("Credit History (Years)", 0.0, 30.0, 5.0, 0.5)
        defaults = st.number_input("Defaults on File", 0, 10, 0)
        delinquencies = st.number_input("Delinquencies (Last 2 Yrs)", 0, 10, 0)
        derogatory = st.number_input("Derogatory Marks", 0, 10, 0)

        st.subheader("Loan Details")
        product = st.selectbox(
            "Product Type", ["Personal Loan", "Credit Card", "Line of Credit"]
        )
        intent = st.selectbox(
            "Loan Purpose",
            [
                "Personal",
                "Education",
                "Home Improvement",
                "Medical",
                "Business",
                "Debt Consolidation",
            ],
        )
        loan_amount = st.number_input("Loan Amount ($)", 1000, 100000, 15000, 1000)
        interest_rate = st.slider("Interest Rate (%)", 5.0, 25.0, 10.0, 0.5)

        # Calculate ratios
        monthly_payment = (loan_amount * (interest_rate / 100)) / 12
        monthly_income = annual_income / 12
        dti = monthly_payment / monthly_income if monthly_income > 0 else 0
        lti = loan_amount / annual_income if annual_income > 0 else 0
        pti = monthly_payment / monthly_income if monthly_income > 0 else 0

        predict = st.button(
            "Predict Approval", type="primary", use_container_width=True
        )

    with col2:
        if predict:
            data = {
                "age": age,
                "years_employed": years_employed,
                "annual_income": annual_income,
                "credit_score": credit_score,
                "credit_history_years": credit_history,
                "savings_assets": savings,
                "defaults_on_file": defaults,
                "delinquencies_last_2yrs": delinquencies,
                "derogatory_marks": derogatory,
                "loan_amount": loan_amount,
                "interest_rate": interest_rate,
                "debt_to_income_ratio": dti,
                "loan_to_income_ratio": lti,
                "payment_to_income_ratio": pti,
                "occupation": occupation,
                "product": product,
                "intent": intent,
            }

            features = preprocess(data, scaler, feature_names)
            pred = model.predict(features)[0]
            prob = model.predict_proba(features)[0][1]

            st.subheader("Prediction Result")

            if pred == 1:
                st.success(f"### ✅ APPROVED ({prob*100:.1f}% confidence)")
            else:
                st.error(f"### ❌ REJECTED ({(1-prob)*100:.1f}% confidence)")

            # Key metrics
            c1, c2, c3 = st.columns(3)
            c1.metric(
                "Credit Score",
                credit_score,
                (
                    "Good"
                    if credit_score >= 700
                    else "Fair" if credit_score >= 650 else "Low"
                ),
            )
            c2.metric("DTI Ratio", f"{dti*100:.1f}%", "OK" if dti < 0.36 else "High")
            c3.metric("Loan-to-Income", f"{lti:.2f}", "OK" if lti < 0.5 else "High")

            st.divider()

            # Feature importance
            st.subheader("Top Factors")
            imp = pd.DataFrame(
                {"Feature": feature_names, "Importance": model.feature_importances_}
            )
            imp = imp.nlargest(8, "Importance")
            imp["Feature"] = imp["Feature"].str.replace("_", " ").str.title()

            fig = px.bar(
                imp,
                x="Importance",
                y="Feature",
                orientation="h",
                color="Importance",
                color_continuous_scale="Blues",
            )
            fig.update_layout(
                height=300,
                showlegend=False,
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("👈 Fill in the applicant details and click **Predict Approval**")

            st.subheader("Model Performance")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Accuracy", "92.86%")
            c2.metric("Precision", "94%")
            c3.metric("Recall", "89%")
            c4.metric("ROC-AUC", "98.42%")

            st.divider()
            st.subheader("About")
            st.write("""
            This model predicts loan approval based on applicant information including credit history, 
            financial status, and loan details. Built with XGBoost trained on 50,000 loan applications.
            """)


if __name__ == "__main__":
    main()
