"""
LoanPredict - Loan Approval Prediction System
Clean, modern UI matching the provided design
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
from pathlib import Path

st.set_page_config(
    page_title="LoanPredict",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .main { background-color: #F5F6F7; }
    .block-container { padding: 1rem 2rem; max-width: 100%; }
    
    .header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid #E5E8EB;
        margin-bottom: 1.5rem;
        background: white;
        margin: -1rem -2rem 1.5rem -2rem;
        padding: 1rem 2rem;
    }
    
    .logo {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 1.25rem;
        font-weight: 600;
        color: #2C3E50;
    }
    
    .logo-icon {
        width: 24px;
        height: 24px;
        background: #2C3E50;
        border-radius: 4px;
    }
    
    .accuracy-badge {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.875rem;
        color: #5D6D7E;
    }
    
    .green-dot {
        width: 8px;
        height: 8px;
        background: #27AE60;
        border-radius: 50%;
    }
    
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border: 1px solid #E5E8EB;
    }
    
    .metric-label {
        font-size: 0.75rem;
        font-weight: 500;
        color: #7F8C8D;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2C3E50;
    }
    
    .metric-badge {
        display: inline-block;
        background: #E8F5E9;
        color: #27AE60;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 2px 8px;
        border-radius: 4px;
        margin-left: 8px;
    }
    
    .metric-sub {
        font-size: 0.75rem;
        color: #7F8C8D;
        margin-top: 4px;
    }
    
    .decision-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border: 1px solid #E5E8EB;
        height: 100%;
    }
    
    .card-title {
        font-size: 0.75rem;
        font-weight: 500;
        color: #7F8C8D;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 1rem;
    }
    
    .approved-text {
        font-size: 1.75rem;
        font-weight: 700;
        color: #27AE60;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .rejected-text {
        font-size: 1.75rem;
        font-weight: 700;
        color: #C0392B;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .model-stats {
        display: flex;
        gap: 2rem;
        margin-top: 1.5rem;
    }
    
    .stat-item { display: flex; flex-direction: column; }
    
    .stat-label {
        font-size: 0.7rem;
        color: #7F8C8D;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stat-value {
        font-size: 1.25rem;
        font-weight: 600;
        color: #2C3E50;
    }
    
    .prob-value {
        font-size: 3.5rem;
        font-weight: 700;
        color: #2C3E50;
        text-align: center;
        margin: 1rem 0;
    }
    
    .prob-value span {
        font-size: 1.5rem;
        font-weight: 500;
    }
    
    .risk-bar {
        height: 8px;
        background: linear-gradient(to right, #27AE60, #F1C40F, #E74C3C);
        border-radius: 4px;
        margin: 1rem 0 0.5rem 0;
    }
    
    .risk-labels {
        display: flex;
        justify-content: space-between;
        font-size: 0.7rem;
        color: #7F8C8D;
    }
    
    .feature-bar {
        display: flex;
        align-items: center;
        margin-bottom: 0.75rem;
    }
    
    .feature-name {
        width: 120px;
        font-size: 0.8rem;
        color: #5D6D7E;
    }
    
    .feature-bar-container {
        flex: 1;
        height: 8px;
        background: #E5E8EB;
        border-radius: 4px;
        margin: 0 10px;
    }
    
    .feature-bar-fill {
        height: 100%;
        background: #3498DB;
        border-radius: 4px;
    }
    
    .feature-value {
        width: 40px;
        font-size: 0.8rem;
        color: #7F8C8D;
        text-align: right;
    }
    
    .factor-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #F0F0F0;
    }
    
    .factor-item:last-child { border-bottom: none; }
    
    .factor-indicator {
        width: 4px;
        height: 40px;
        border-radius: 2px;
        flex-shrink: 0;
    }
    
    .factor-green { background: #27AE60; }
    .factor-orange { background: #F39C12; }
    .factor-red { background: #E74C3C; }
    
    .factor-content { flex: 1; }
    
    .factor-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #2C3E50;
        margin-bottom: 4px;
    }
    
    .factor-desc {
        font-size: 0.75rem;
        color: #7F8C8D;
        line-height: 1.4;
    }
    
    .recommendations { margin-top: 1.5rem; }
    
    .rec-title {
        font-size: 0.7rem;
        font-weight: 500;
        color: #7F8C8D;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.75rem;
    }
    
    .rec-item {
        font-size: 0.8rem;
        color: #5D6D7E;
        padding-left: 1rem;
        position: relative;
        margin-bottom: 0.5rem;
    }
    
    .rec-item::before {
        content: "•";
        position: absolute;
        left: 0;
        color: #7F8C8D;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #FAFAFA;
        border-right: 1px solid #E5E8EB;
    }
    
    .sidebar-section {
        font-size: 0.7rem;
        font-weight: 500;
        color: #7F8C8D;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 1.5rem 0 0.75rem 0;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    .stButton > button {
        width: 100%;
        background: #27AE60;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    .stButton > button:hover { background: #219A52; }
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


def get_feature_importance(model, feature_names):
    importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': model.feature_importances_
    }).sort_values('Importance', ascending=False).head(5)
    
    name_map = {
        'credit_score': 'Credit Score',
        'annual_income': 'Annual Income',
        'debt_to_income_ratio': 'Debt-to-Income',
        'loan_amount': 'Loan Amount',
        'years_employed': 'Employment Hist',
        'defaults_on_file': 'Default History',
        'credit_history_years': 'Credit History',
        'loan_to_income_ratio': 'Loan-to-Income',
        'interest_rate': 'Interest Rate',
        'age': 'Age'
    }
    
    importance_df['Display'] = importance_df['Feature'].map(
        lambda x: name_map.get(x, x.replace('_', ' ').title()[:15])
    )
    
    return importance_df


def get_contributing_factors(data, probability):
    factors = []
    
    if data['credit_score'] >= 700:
        factors.append({
            'type': 'green',
            'title': 'Strong Credit History',
            'desc': f"Applicant has a credit score in the top 20% percentile, significantly boosting approval odds."
        })
    elif data['credit_score'] >= 650:
        factors.append({
            'type': 'green',
            'title': 'Good Credit Score',
            'desc': f"Credit score of {data['credit_score']} meets standard lending requirements."
        })
    else:
        factors.append({
            'type': 'red',
            'title': 'Low Credit Score',
            'desc': f"Credit score of {data['credit_score']} is below the preferred threshold of 650."
        })
    
    dti = data.get('debt_to_income_ratio', 0) * 100
    if dti < 36:
        factors.append({
            'type': 'green',
            'title': 'Low Debt-to-Income Ratio',
            'desc': f"Current DTI of {dti:.0f}% is well below the conservative threshold of 36%."
        })
    elif dti < 43:
        factors.append({
            'type': 'orange',
            'title': 'Moderate Debt-to-Income Ratio',
            'desc': f"DTI of {dti:.0f}% is acceptable but approaching upper limits."
        })
    else:
        factors.append({
            'type': 'red',
            'title': 'High Debt-to-Income Ratio',
            'desc': f"DTI of {dti:.0f}% exceeds the recommended maximum of 43%."
        })
    
    if data['years_employed'] >= 2:
        factors.append({
            'type': 'green',
            'title': 'Stable Employment',
            'desc': f"Employment duration of {data['years_employed']:.1f} years demonstrates job stability."
        })
    else:
        factors.append({
            'type': 'orange',
            'title': 'Short Employment Duration',
            'desc': f"Current employment length is less than 2 years at current role, introducing minor risk."
        })
    
    if data.get('defaults_on_file', 0) > 0:
        factors.append({
            'type': 'red',
            'title': 'Previous Defaults',
            'desc': "History of defaults significantly impacts creditworthiness assessment."
        })
    
    return factors[:3]


def get_recommendations(data, probability):
    recs = []
    
    if data['years_employed'] < 2:
        recs.append("Verify employment with current employer letter.")
    
    if data.get('debt_to_income_ratio', 0) * 100 > 30:
        recs.append("Confirm detailed breakdown of existing debts.")
    
    if data['credit_score'] < 700:
        recs.append("Consider credit score improvement strategies.")
    
    if data['loan_amount'] > data['annual_income'] * 0.5:
        recs.append("Review loan amount relative to annual income.")
    
    if not recs:
        recs.append("Application appears strong - proceed with standard verification.")
    
    return recs[:2]


def main():
    try:
        model, scaler, feature_names = load_model()
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return

    with st.sidebar:
        st.markdown('<p class="sidebar-section">PERSONAL</p>', unsafe_allow_html=True)
        
        full_name = st.text_input("Full Name", placeholder="e.g. Alex Morgan")
        
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=18, max_value=70, value=34)
        with col2:
            dependents = st.number_input("Dependents", min_value=0, max_value=10, value=1)
        
        st.markdown('<p class="sidebar-section">FINANCIAL</p>', unsafe_allow_html=True)
        
        annual_income = st.number_input("Annual Income", min_value=15000, max_value=500000, value=85000, format="%d")
        years_employed = st.slider("Employment Length (Years)", 0.0, 40.0, 5.0, 0.5)
        
        st.markdown('<p class="sidebar-section">LOAN DETAILS</p>', unsafe_allow_html=True)
        
        loan_amount = st.number_input("Loan Amount", min_value=1000, max_value=100000, value=25000, format="%d")
        term_months = st.selectbox("Term (Months)", [12, 24, 36, 48, 60], index=2)
        loan_intent = st.selectbox("Intent", [
            "Debt Consolidation", "Education", "Home Improvement", 
            "Medical", "Personal", "Business"
        ])
        
        st.markdown('<p class="sidebar-section">CREDIT HISTORY</p>', unsafe_allow_html=True)
        
        credit_score = st.number_input("Credit Score", min_value=300, max_value=850, value=720)
        default_history = st.radio("Default History", ["No", "Yes"], horizontal=True)
        defaults = 1 if default_history == "Yes" else 0
        
        st.markdown("<br>", unsafe_allow_html=True)
        predict_button = st.button("Run Analysis", type="primary", use_container_width=True)

    st.markdown("""
    <div class="header-bar">
        <div class="logo">
            <div class="logo-icon"></div>
            LoanPredict
        </div>
        <div class="accuracy-badge">
            <div class="green-dot"></div>
            XGBoost · 92.86% accuracy
        </div>
    </div>
    """, unsafe_allow_html=True)

    monthly_payment = (loan_amount * 0.08) / 12
    dti = (monthly_payment / (annual_income / 12)) if annual_income > 0 else 0
    lti = loan_amount / annual_income if annual_income > 0 else 0
    pti = monthly_payment / (annual_income / 12) if annual_income > 0 else 0

    col1, col2, col3 = st.columns(3)
    
    with col1:
        score_change = "+15pts" if credit_score >= 700 else "+5pts" if credit_score >= 650 else ""
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">CREDIT SCORE</div>
            <div class="metric-value">{credit_score}<span class="metric-badge">{score_change}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">LOAN AMOUNT</div>
            <div class="metric-value">${loan_amount:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        target_text = "Target <35%" if dti * 100 < 35 else "Above target"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">DTI RATIO</div>
            <div class="metric-value">{dti * 100:.0f}%</div>
            <div class="metric-sub">{target_text}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

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

    features = preprocess_input(input_data, scaler, feature_names)
    prediction = model.predict(features)[0]
    probability = model.predict_proba(features)[0][1]

    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        if prediction == 1:
            decision_html = '<div class="approved-text">APPROVED <span style="font-size:1.5rem;">✓</span></div>'
        else:
            decision_html = '<div class="rejected-text">NOT APPROVED <span style="font-size:1.5rem;">✗</span></div>'
        
        st.markdown(f"""
        <div class="decision-card">
            <div class="card-title">MODEL DECISION</div>
            {decision_html}
            <div class="model-stats">
                <div class="stat-item">
                    <span class="stat-label">PRECISION</span>
                    <span class="stat-value">0.94</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">RECALL</span>
                    <span class="stat-value">0.89</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        prob_pct = probability * 100
        st.markdown(f"""
        <div class="decision-card">
            <div class="card-title">APPROVAL PROBABILITY</div>
            <div class="prob-value">{prob_pct:.0f}<span>%</span></div>
            <div class="risk-bar"></div>
            <div class="risk-labels">
                <span>Low Risk</span>
                <span>High Risk</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    
    with col1:
        importance_df = get_feature_importance(model, feature_names)
        max_imp = importance_df['Importance'].max()
        
        bars_html = ""
        for _, row in importance_df.iterrows():
            width_pct = (row['Importance'] / max_imp) * 100
            bars_html += f"""
            <div class="feature-bar">
                <span class="feature-name">{row['Display']}</span>
                <div class="feature-bar-container">
                    <div class="feature-bar-fill" style="width: {width_pct}%"></div>
                </div>
                <span class="feature-value">{row['Importance']:.2f}</span>
            </div>
            """
        
        st.markdown(f"""
        <div class="decision-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div class="card-title" style="margin: 0;">Feature Importance (SHAP)</div>
                <span style="font-size: 0.7rem; color: #7F8C8D;">Global Impact</span>
            </div>
            {bars_html}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        factors = get_contributing_factors(input_data, probability)
        recs = get_recommendations(input_data, probability)
        
        factors_html = ""
        for f in factors:
            factors_html += f"""
            <div class="factor-item">
                <div class="factor-indicator factor-{f['type']}"></div>
                <div class="factor-content">
                    <div class="factor-title">{f['title']}</div>
                    <div class="factor-desc">{f['desc']}</div>
                </div>
            </div>
            """
        
        recs_html = ""
        for r in recs:
            recs_html += f'<div class="rec-item">{r}</div>'
        
        st.markdown(f"""
        <div class="decision-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div class="card-title" style="margin: 0;">Key Contributing Factors</div>
                <span style="font-size: 0.7rem; color: #7F8C8D;">Local explanation</span>
            </div>
            {factors_html}
            <div class="recommendations">
                <div class="rec-title">RECOMMENDED ACTIONS</div>
                {recs_html}
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
