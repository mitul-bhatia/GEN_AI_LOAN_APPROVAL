import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import os


class LoanDataPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.categorical_cols = ['occupation_status', 'product_type', 'loan_intent']
        self.drop_cols = ['customer_id', 'current_debt']
        self.numerical_cols = None
        self.feature_names = None
        
    def fit_transform(self, df, target_col='loan_status'):
        df = df.copy()
        
        df = df.drop(columns=self.drop_cols, errors='ignore')
        
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        X = pd.get_dummies(X, columns=self.categorical_cols, drop_first=False)
        
        self.numerical_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        bool_cols = X.select_dtypes(include=['bool']).columns
        X[bool_cols] = X[bool_cols].astype(int)
        
        X[self.numerical_cols] = self.scaler.fit_transform(X[self.numerical_cols])
        
        self.feature_names = X.columns.tolist()
        
        return X, y
    
    def transform(self, df):
        df = df.copy()
        
        has_target = 'loan_status' in df.columns
        if has_target:
            y = df['loan_status']
            df = df.drop(columns=['loan_status'])
        
        df = df.drop(columns=self.drop_cols, errors='ignore')
        
        df = pd.get_dummies(df, columns=self.categorical_cols, drop_first=False)
        
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0
        
        df = df[self.feature_names]
        
        bool_cols = df.select_dtypes(include=['bool']).columns
        df[bool_cols] = df[bool_cols].astype(int)
        
        df[self.numerical_cols] = self.scaler.transform(df[self.numerical_cols])
        
        if has_target:
            return df, y
        return df
    
    def save(self, path):
        joblib.dump({
            'scaler': self.scaler,
            'categorical_cols': self.categorical_cols,
            'drop_cols': self.drop_cols,
            'numerical_cols': self.numerical_cols,
            'feature_names': self.feature_names
        }, path)
    
    def load(self, path):
        data = joblib.load(path)
        self.scaler = data['scaler']
        self.categorical_cols = data['categorical_cols']
        self.drop_cols = data['drop_cols']
        self.numerical_cols = data['numerical_cols']
        self.feature_names = data['feature_names']
        return self


def load_raw_data(path):
    return pd.read_csv(path)


def prepare_data(raw_path, processed_dir, test_size=0.2, random_state=42):
    df = load_raw_data(raw_path)
    
    preprocessor = LoanDataPreprocessor()
    X, y = preprocessor.fit_transform(df)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    X_train.to_csv(os.path.join(processed_dir, 'X_train.csv'), index=False)
    X_test.to_csv(os.path.join(processed_dir, 'X_test.csv'), index=False)
    y_train.to_csv(os.path.join(processed_dir, 'y_train.csv'), index=False)
    y_test.to_csv(os.path.join(processed_dir, 'y_test.csv'), index=False)
    
    preprocessor.save(os.path.join(processed_dir, 'preprocessor.pkl'))
    
    return X_train, X_test, y_train, y_test, preprocessor


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RAW_PATH = os.path.join(BASE_DIR, 'data', 'raw', 'loan_approval_data.csv')
    PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
    
    X_train, X_test, y_train, y_test, preprocessor = prepare_data(RAW_PATH, PROCESSED_DIR)
    
    print(f"Training set: {X_train.shape}")
    print(f"Test set: {X_test.shape}")
    print(f"Features: {len(preprocessor.feature_names)}")
    print(f"\nFeature names:\n{preprocessor.feature_names}")
