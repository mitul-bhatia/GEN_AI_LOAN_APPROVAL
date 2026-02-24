"""
Loan Approval Prediction System
A professional Streamlit application for predicting loan approvals using XGBoost.
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Loan Approval Predictor",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 2rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1e3a5f;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #666;
    }
    
    /* Result cards */
    .approved-card {
        background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    
    .rejected-card {
        background: linear-gradient(135deg, #c0392b 0%, #e74c3c 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e3a5f;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #3498db;
    }
    
    /* Info boxes */
    .info-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3498db;
        margin: 1rem 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    /* Input styling */
    .stSelectbox, .stSlider, .stNumberInput {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_model():
    """Load the trained XGBoost model and preprocessing objects."""
    # Try multiple path resolutions for different run contexts
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
    
    raise FileNotFoundError("Could not find model files. Please check the directory structure.")


def preprocess_input(data, scaler, feature_names):
    """Preprocess user input to match training data format."""
    
    # Numerical features that need scaling
    numerical_features = [
        'age', 'years_employed', 'annual_income', 'credit_score',
        'credit_history_years', 'savings_assets', 'defaults_on_file',
        'delinquencies_last_2yrs', 'derogatory_marks', 'loan_amount',
        'interest_rate', 'debt_to_income_ratio', 'loan_to_income_ratio',
        'payment_to_income_ratio'
    ]
    
    # Create feature vector with float64 dtype to avoid warnings
    features = pd.DataFrame(0.0, index=[0], columns=feature_names, dtype=np.float64)
    
    # Set numerical features
    for feat in numerical_features:
        if feat in data:
            features.loc[0, feat] = data[feat]
    
    # Scale numerical features
    numerical_cols = [f for f in numerical_features if f in features.columns]
    features[numerical_cols] = scaler.transform(features[numerical_cols])
    
    # Set categorical features (one-hot encoded)
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


def create_gauge_chart(probability, title="Approval Probability"):
    """Create a gauge chart for probability visualization."""
    
    # Determine color based on probability
    if probability >= 0.7:
        bar_color = "#27ae60"
    elif probability >= 0.4:
        bar_color = "#f39c12"
    else:
        bar_color = "#e74c3c"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20, 'color': '#1e3a5f'}},
        number={'suffix': "%", 'font': {'size': 40, 'color': '#1e3a5f'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#1e3a5f"},
            'bar': {'color': bar_color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#1e3a5f",
            'steps': [
                {'range': [0, 40], 'color': '#fadbd8'},
                {'range': [40, 70], 'color': '#fef9e7'},
                {'range': [70, 100], 'color': '#d5f5e3'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "#1e3a5f", 'family': "Arial"}
    )
    
    return fig


def create_feature_importance_chart(model, feature_names, user_features):
    """Create a feature importance chart highlighting user's values."""
    
    importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': model.feature_importances_
    }).sort_values('Importance', ascending=True).tail(10)
    
    fig = px.bar(
        importance_df,
        x='Importance',
        y='Feature',
        orientation='h',
        title='Top 10 Features Influencing Decision',
        color='Importance',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="Feature Importance",
        yaxis_title="",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#1e3a5f"}
    )
    
    return fig


def get_decision_factors(model, feature_names, user_features, prediction_proba):
    """Analyze which factors most influenced the decision."""
    
    # Get feature importances
    importances = dict(zip(feature_names, model.feature_importances_))
    user_values = user_features.iloc[0].to_dict()
    
    # Identify top positive and negative factors
    factors = []
    
    # Map features to interpretable names
    feature_labels = {
        'credit_score': 'Credit Score',
        'defaults_on_file': 'Past Defaults',
        'debt_to_income_ratio': 'Debt-to-Income Ratio',
        'delinquencies_last_2yrs': 'Recent Delinquencies',
        'loan_intent_Debt Consolidation': 'Debt Consolidation Loan',
        'loan_intent_Education': 'Education Loan',
        'product_type_Credit Card': 'Credit Card Product',
        'age': 'Age',
        'annual_income': 'Annual Income',
        'credit_history_years': 'Credit History Length'
    }
    
    for feat, imp in sorted(importances.items(), key=lambda x: -x[1])[:5]:
        label = feature_labels.get(feat, feat.replace('_', ' ').title())
        value = user_values.get(feat, 0)
        
        if value != 0:
            if value > 0:
                impact = "positive" if prediction_proba > 0.5 else "negative"
            else:
                impact = "negative" if prediction_proba > 0.5 else "positive"
            
            factors.append({
                'feature': label,
                'importance': imp,
                'impact': impact
            })
    
    return factors[:4]


def main():
    # Load model
    try:
        model, scaler, feature_names = load_model()
    except Exception as e:
        st.error(f"Error loading model: {e}")
        st.info("Please ensure the model files are in the correct location.")
        return
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏦 Loan Approval Prediction System</h1>
        <p>AI-Powered Credit Decision Engine | XGBoost Model | 92.86% Accuracy</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - Input Form
    with st.sidebar:
        st.markdown("### 📝 Application Details")
        st.markdown("---")
        
        # Personal Information
        st.markdown("#### Personal Information")
        age = st.slider("Age", 18, 70, 35, help="Applicant's age")
        occupation = st.selectbox(
            "Occupation Status",
            ["Employed", "Self-Employed", "Student"],
            help="Current employment status"
        )
        years_employed = st.slider("Years Employed", 0.0, 40.0, 5.0, 0.5)
        
        st.markdown("---")
        
        # Financial Information
        st.markdown("#### Financial Information")
        annual_income = st.number_input(
            "Annual Income ($)",
            min_value=15000,
            max_value=500000,
            value=75000,
            step=5000
        )
        savings = st.number_input(
            "Savings & Assets ($)",
            min_value=0,
            max_value=1000000,
            value=25000,
            step=5000
        )
        
        st.markdown("---")
        
        # Credit Information
        st.markdown("#### Credit History")
        credit_score = st.slider(
            "Credit Score",
            300, 850, 680,
            help="FICO score range: 300-850"
        )
        credit_history = st.slider("Credit History (Years)", 0.0, 30.0, 8.0, 0.5)
        defaults = st.selectbox("Defaults on File", [0, 1, 2, 3], index=0)
        delinquencies = st.selectbox("Delinquencies (Last 2 Years)", [0, 1, 2, 3, 4, 5], index=0)
        derogatory_marks = st.selectbox("Derogatory Marks", [0, 1, 2, 3], index=0)
        
        st.markdown("---")
        
        # Loan Details
        st.markdown("#### Loan Details")
        product_type = st.selectbox(
            "Product Type",
            ["Credit Card", "Personal Loan", "Line of Credit"]
        )
        loan_intent = st.selectbox(
            "Loan Purpose",
            ["Education", "Personal", "Home Improvement", "Medical", "Business", "Debt Consolidation"]
        )
        loan_amount = st.number_input(
            "Loan Amount ($)",
            min_value=1000,
            max_value=100000,
            value=15000,
            step=1000
        )
        interest_rate = st.slider("Interest Rate (%)", 5.0, 25.0, 12.0, 0.5)
        
        # Calculate ratios
        dti = (loan_amount * (interest_rate / 100) / 12) / (annual_income / 12) * 100
        lti = loan_amount / annual_income
        pti = (loan_amount * (interest_rate / 100) / 12) / (annual_income / 12)
        
        st.markdown("---")
        predict_button = st.button("🔮 Predict Approval", use_container_width=True, type="primary")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="section-header">Application Summary</div>', unsafe_allow_html=True)
        
        # Display application summary in a nice format
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        
        with summary_col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Credit Score</div>
            </div>
            """.format(credit_score), unsafe_allow_html=True)
        
        with summary_col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">${:,}</div>
                <div class="metric-label">Loan Amount</div>
            </div>
            """.format(loan_amount), unsafe_allow_html=True)
        
        with summary_col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{:.1f}%</div>
                <div class="metric-label">DTI Ratio</div>
            </div>
            """.format(dti), unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-header">Risk Indicators</div>', unsafe_allow_html=True)
        
        # Risk indicator
        risk_level = "Low" if credit_score >= 700 and defaults == 0 else "Medium" if credit_score >= 600 else "High"
        risk_color = "#27ae60" if risk_level == "Low" else "#f39c12" if risk_level == "Medium" else "#e74c3c"
        
        st.markdown(f"""
        <div class="info-box" style="border-left-color: {risk_color};">
            <strong>Risk Assessment:</strong> {risk_level}<br>
            <small>Based on credit score and payment history</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Prediction Section
    if predict_button:
        st.markdown("---")
        st.markdown('<div class="section-header">🎯 Prediction Results</div>', unsafe_allow_html=True)
        
        # Prepare input data
        input_data = {
            'age': age,
            'years_employed': years_employed,
            'annual_income': annual_income,
            'credit_score': credit_score,
            'credit_history_years': credit_history,
            'savings_assets': savings,
            'defaults_on_file': defaults,
            'delinquencies_last_2yrs': delinquencies,
            'derogatory_marks': derogatory_marks,
            'loan_amount': loan_amount,
            'interest_rate': interest_rate,
            'debt_to_income_ratio': dti / 100,
            'loan_to_income_ratio': lti,
            'payment_to_income_ratio': pti,
            'occupation_status': occupation,
            'product_type': product_type,
            'loan_intent': loan_intent
        }
        
        # Preprocess and predict
        try:
            features = preprocess_input(input_data, scaler, feature_names)
            prediction = model.predict(features)[0]
            probability = model.predict_proba(features)[0][1]
            
            # Display results
            result_col1, result_col2 = st.columns([1, 1])
            
            with result_col1:
                if prediction == 1:
                    st.markdown("""
                    <div class="approved-card">
                        <h2>✅ APPROVED</h2>
                        <p>Your loan application has been approved!</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="rejected-card">
                        <h2>❌ REJECTED</h2>
                        <p>Unfortunately, your application was not approved.</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with result_col2:
                gauge_fig = create_gauge_chart(probability)
                st.plotly_chart(gauge_fig, use_container_width=True)
            
            # Decision Factors
            st.markdown('<div class="section-header">📊 Decision Analysis</div>', unsafe_allow_html=True)
            
            analysis_col1, analysis_col2 = st.columns([1, 1])
            
            with analysis_col1:
                # Feature importance chart
                importance_fig = create_feature_importance_chart(model, feature_names, features)
                st.plotly_chart(importance_fig, use_container_width=True)
            
            with analysis_col2:
                st.markdown("#### Key Factors in This Decision")
                
                # Show what influenced the decision
                if probability >= 0.5:
                    st.success("**Positive Factors:**")
                    if credit_score >= 700:
                        st.write("✅ Excellent credit score")
                    if defaults == 0:
                        st.write("✅ No defaults on file")
                    if dti < 30:
                        st.write("✅ Low debt-to-income ratio")
                    if loan_intent == "Education":
                        st.write("✅ Education loans have higher approval rates")
                    if product_type == "Credit Card":
                        st.write("✅ Credit card products have favorable terms")
                else:
                    st.error("**Areas of Concern:**")
                    if credit_score < 650:
                        st.write("⚠️ Credit score below 650")
                    if defaults > 0:
                        st.write("⚠️ Defaults on file reduce approval chances")
                    if dti > 40:
                        st.write("⚠️ High debt-to-income ratio")
                    if loan_intent == "Debt Consolidation":
                        st.write("⚠️ Debt consolidation loans have stricter requirements")
                    if delinquencies > 0:
                        st.write("⚠️ Recent delinquencies affect score")
                
                # Recommendations
                st.markdown("#### 💡 Recommendations")
                if probability < 0.5:
                    if credit_score < 700:
                        st.info("📈 Improve credit score by paying bills on time")
                    if dti > 30:
                        st.info("💰 Consider reducing existing debt before applying")
                    if loan_amount > annual_income * 0.3:
                        st.info("📉 Request a smaller loan amount")
        
        except Exception as e:
            st.error(f"Error making prediction: {e}")
            st.info("Please check your input values and try again.")
    
    # Footer with model info
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p><strong>Model Information</strong></p>
        <p>XGBoost Classifier | Accuracy: 92.86% | ROC-AUC: 98.42%</p>
        <p>Trained on 50,000 loan applications | 26 features</p>
        <p><small>Built for educational purposes | Mid-Semester AI/ML Project</small></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
