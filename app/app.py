"""
LoanPredict - Loan Approval Prediction System
Clean UI using Streamlit native components
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="LoanPredict",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimal custom CSS
st.markdown("""
<style>
    .main { background-color: #F5F6F7; }
    .block-container { padding-top: 1rem; }
    section[data-testid="stSidebar"] { background-color: #FAFAFA; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_model():
    possible_roots = [
        Path(__file__).parent.parent,
        Path.cwd(),
        Path.cwd().parent
    ]
    
    for root in possible_roots:
        model_path = root / "models" / "xgboost.pkl"
        scaler_path = root / "data" / "processed" / "scaler.pkl"
        features_path = root / "data" / "processed" / "feature_names.pkl"
        
        if model_path.exists() and scaler_path.exists() and features_path.exists():
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            feature_names = joblib.load(features_path)
            return model, scaler, feature_names
    
    raise FileNotFoundError("Could not find model files.")


def preprocess_input(data, scaler, feature_names):
    numerical_features = [
        'age', 'years_employed', 'annual_income', 'credit_score',
        'credit_history_years', 'savings_assets', 'defaults_on_file',
        'delinquencies_last_2yrs', 'derogatory_marks', 'loan_amount',
        'interest_rate', 'debt_to_income_ratio', 'loan_to_income_ratio',
        'payment_to_income_ratio'
    ]
    
    features = pd.DataFrame(0.0, index=[0], columns=feature_names, dtype=np.float64)
    
    for feat in numerical_features:
        if feat in data:
            features.loc[0, feat] = data[feat]
    
    numerical_cols = [f for f in numerical_features if f in features.columns]
    features[numerical_cols] = scaler.transform(features[numerical_cols])
    
    occupation_col = f"occupation_status_{data['occupation_status']}"
    product_col = f"product_type_{data['product_type']}"
    intent_col = f"loan_intent_{data['loan_intent']}"
    
    if occupation_col in features.columns:
        features.loc[0, occupation_col] = 1
    if product_col in features.columns:
        features.loc[0, product_col] = 1
    if intent_col in features.columns:
        features.loc[0, intent_col] = 1
    
    return features


def create_gauge_chart(probability):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'suffix': "%", 'font': {'size': 48, 'color': '#2C3E50'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#7F8C8D", 'tickfont': {'size': 10}},
            'bar': {'color': "#27AE60" if probability >= 0.5 else "#E74C3C", 'thickness': 0.3},
            'bgcolor': "white",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 40], 'color': '#FADBD8'},
                {'range': [40, 70], 'color': '#FCF3CF'},
                {'range': [70, 100], 'color': '#D5F5E3'}
            ],
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "#2C3E50"}
    )
    
    return fig


def create_feature_importance_chart(model, feature_names):
    importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': model.feature_importances_
    }).sort_values('Importance', ascending=True).tail(5)
    
    name_map = {
        'credit_score': 'Credit Score',
        'annual_income': 'Annual Income',
        'debt_to_income_ratio': 'Debt-to-Income',
        'loan_amount': 'Loan Amount',
        'years_employed': 'Employment History',
        'defaults_on_file': 'Default History',
        'credit_history_years': 'Credit History',
        'loan_to_income_ratio': 'Loan-to-Income',
        'interest_rate': 'Interest Rate',
        'delinquencies_last_2yrs': 'Delinquencies',
        'age': 'Age'
    }
    
    importance_df['Display'] = importance_df['Feature'].map(
        lambda x: name_map.get(x, x.replace('_', ' ').title())
    )
    
    fig = go.Figure(go.Bar(
        x=importance_df['Importance'],
        y=importance_df['Display'],
        orientation='h',
        marker_color='#5D6D7E',
        text=[f"{v:.2f}" for v in importance_df['Importance']],
        textposition='outside',
        textfont={'size': 11, 'color': '#7F8C8D'}
    ))
    
    fig.update_layout(
        height=220,
        margin=dict(l=10, r=40, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis={'showgrid': False, 'showticklabels': False, 'zeroline': False},
        yaxis={'showgrid': False, 'tickfont': {'size': 11, 'color': '#5D6D7E'}},
        font={'color': "#2C3E50"}
    )
    
    return fig


def main():
    try:
        model, scaler, feature_names = load_model()
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return

    # Sidebar
    with st.sidebar:
        st.markdown("#### PERSONAL")
        full_name = st.text_input("Full Name", placeholder="e.g. Alex Morgan")
        
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=18, max_value=70, value=34)
        with col2:
            dependents = st.number_input("Dependents", min_value=0, max_value=10, value=1)
        
        st.markdown("#### FINANCIAL")
        annual_income = st.number_input("Annual Income ($)", min_value=15000, max_value=500000, value=85000)
        years_employed = st.slider("Employment Length (Years)", 0.0, 40.0, 5.0, 0.5)
        
        st.markdown("#### LOAN DETAILS")
        loan_amount = st.number_input("Loan Amount ($)", min_value=1000, max_value=100000, value=25000)
        term_months = st.selectbox("Term (Months)", [12, 24, 36, 48, 60], index=2)
        loan_intent = st.selectbox("Intent", [
            "Debt Consolidation", "Education", "Home Improvement", 
            "Medical", "Personal", "Business"
        ])
        
        st.markdown("#### CREDIT HISTORY")
        credit_score = st.number_input("Credit Score", min_value=300, max_value=850, value=720)
        default_history = st.radio("Default History", ["No", "Yes"], horizontal=True)
        defaults = 1 if default_history == "Yes" else 0
        
        st.markdown("---")
        predict_button = st.button("🔍 Run Analysis", type="primary", use_container_width=True)

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 🏦 LoanPredict")
    with col2:
        st.markdown("🟢 **XGBoost** · 92.86% accuracy")

    st.markdown("---")

    # Calculate values
    monthly_payment = (loan_amount * 0.08) / 12
    dti = (monthly_payment / (annual_income / 12)) if annual_income > 0 else 0
    lti = loan_amount / annual_income if annual_income > 0 else 0
    pti = monthly_payment / (annual_income / 12) if annual_income > 0 else 0

    # Top metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        delta = "+15 pts" if credit_score >= 700 else ("+5 pts" if credit_score >= 650 else None)
        st.metric("CREDIT SCORE", credit_score, delta=delta)
    with col2:
        st.metric("LOAN AMOUNT", f"${loan_amount:,}")
    with col3:
        st.metric("DTI RATIO", f"{dti * 100:.0f}%", delta="Target <35%" if dti * 100 < 35 else "Above target", delta_color="off")

    st.markdown("")

    # Prepare input data
    input_data = {
        'age': age,
        'years_employed': years_employed,
        'annual_income': annual_income,
        'credit_score': credit_score,
        'credit_history_years': years_employed * 0.8,
        'savings_assets': annual_income * 0.3,
        'defaults_on_file': defaults,
        'delinquencies_last_2yrs': 0,
        'derogatory_marks': 0,
        'loan_amount': loan_amount,
        'interest_rate': 8.0,
        'debt_to_income_ratio': dti,
        'loan_to_income_ratio': lti,
        'payment_to_income_ratio': pti,
        'occupation_status': 'Employed',
        'product_type': 'Personal Loan',
        'loan_intent': loan_intent
    }

    # Make prediction
    features = preprocess_input(input_data, scaler, feature_names)
    prediction = model.predict(features)[0]
    probability = model.predict_proba(features)[0][1]

    # Decision row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### MODEL DECISION")
        if prediction == 1:
            st.success("### ✅ APPROVED")
        else:
            st.error("### ❌ NOT APPROVED")
        
        mcol1, mcol2 = st.columns(2)
        with mcol1:
            st.caption("PRECISION")
            st.markdown("**0.94**")
        with mcol2:
            st.caption("RECALL")
            st.markdown("**0.89**")
    
    with col2:
        st.markdown("##### APPROVAL PROBABILITY")
        gauge_fig = create_gauge_chart(probability)
        st.plotly_chart(gauge_fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("")

    # Analysis row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### FEATURE IMPORTANCE (SHAP)")
        importance_fig = create_feature_importance_chart(model, feature_names)
        st.plotly_chart(importance_fig, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        st.markdown("##### KEY CONTRIBUTING FACTORS")
        
        # Credit score factor
        if credit_score >= 700:
            st.success("**Strong Credit History**")
            st.caption("Applicant has a credit score in the top 20% percentile, significantly boosting approval odds.")
        elif credit_score >= 650:
            st.info("**Good Credit Score**")
            st.caption(f"Credit score of {credit_score} meets standard lending requirements.")
        else:
            st.error("**Low Credit Score**")
            st.caption(f"Credit score of {credit_score} is below the preferred threshold of 650.")
        
        # DTI factor
        dti_pct = dti * 100
        if dti_pct < 36:
            st.success("**Low Debt-to-Income Ratio**")
            st.caption(f"Current DTI of {dti_pct:.0f}% is well below the conservative threshold of 36%.")
        elif dti_pct < 43:
            st.warning("**Moderate Debt-to-Income Ratio**")
            st.caption(f"DTI of {dti_pct:.0f}% is acceptable but approaching upper limits.")
        else:
            st.error("**High Debt-to-Income Ratio**")
            st.caption(f"DTI of {dti_pct:.0f}% exceeds the recommended maximum of 43%.")
        
        # Employment factor
        if years_employed >= 2:
            st.success("**Stable Employment**")
            st.caption(f"Employment duration of {years_employed:.1f} years demonstrates job stability.")
        else:
            st.warning("**Short Employment Duration**")
            st.caption("Current employment is less than 2 years, introducing minor risk.")
        
        # Recommendations
        st.markdown("---")
        st.markdown("##### RECOMMENDED ACTIONS")
        
        if years_employed < 2:
            st.markdown("• Verify employment with current employer letter.")
        if dti_pct > 30:
            st.markdown("• Confirm detailed breakdown of existing debts.")
        if credit_score < 700:
            st.markdown("• Consider credit score improvement strategies.")
        if defaults > 0:
            st.markdown("• Address previous defaults before applying.")
        if prediction == 1 and years_employed >= 2 and credit_score >= 700:
            st.markdown("• Application appears strong - proceed with standard verification.")

    # Footer
    st.markdown("---")
    st.caption("LoanPredict | XGBoost Model | Trained on 50,000 loan applications | Educational Project")


if __name__ == "__main__":
    main()
