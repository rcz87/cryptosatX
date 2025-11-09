"""
Machine Learning Service for CryptoSatX
Advanced ML models untuk signal optimization dan prediction
"""
import asyncio
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import warnings
warnings.filterwarnings('ignore')

from app.utils.logger import default_logger


@dataclass
class MLModelConfig:
    """Configuration untuk ML models"""
    model_type: str
    features: List[str]
    target: str
    hyperparameters: Dict[str, Any]
    retrain_interval_hours: int = 24
    min_samples: int = 1000
    validation_split: float = 0.2


class PredictionResult(BaseModel):
    """Model untuk prediction results"""
    prediction: float
    confidence: float
    feature_importance: Dict[str, float]
    model_version: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelPerformance(BaseModel):
    """Model untuk performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    cross_val_score: float
    sample_size: int
    last_updated: datetime = Field(default_factory=datetime.now)


class MLService:
    """
    Comprehensive ML service dengan:
    - Multiple model types (Classification, Regression)
    - Feature engineering dan selection
    - Model training dan validation
    - Real-time predictions
    - Model performance tracking
    - Automated retraining
    """
    
    def __init__(self):
        self.logger = default_logger
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.encoders: Dict[str, LabelEncoder] = {}
        self.model_performance: Dict[str, ModelPerformance] = {}
        self.feature_importance: Dict[str, Dict[str, float]] = {}
        self.prediction_history: List[Dict[str, Any]] = []
        
        # Model configurations
        self.model_configs = {
            "signal_classifier": MLModelConfig(
                model_type="classification",
                features=[
                    "liquidations", "funding_rate", "price_momentum", "long_short_ratio",
                    "smart_money", "oi_trend", "social_sentiment", "fear_greed",
                    "volume_change", "volatility", "rsi", "macd_signal"
                ],
                target="signal_success",
                hyperparameters={
                    "n_estimators": 100,
                    "max_depth": 10,
                    "min_samples_split": 5,
                    "min_samples_leaf": 2,
                    "random_state": 42
                }
            ),
            "price_predictor": MLModelConfig(
                model_type="regression",
                features=[
                    "liquidations", "funding_rate", "price_momentum", "long_short_ratio",
                    "smart_money", "oi_trend", "social_sentiment", "fear_greed",
                    "volume_change", "volatility", "rsi", "macd_signal",
                    "price_change_1h", "price_change_4h", "price_change_24h"
                ],
                target="price_change_future",
                hyperparameters={
                    "n_estimators": 100,
                    "max_depth": 8,
                    "learning_rate": 0.1,
                    "loss": "squared_error",
                    "random_state": 42
                }
            ),
            "volatility_predictor": MLModelConfig(
                model_type="regression",
                features=[
                    "liquidations", "funding_rate", "price_momentum", "long_short_ratio",
                    "smart_money", "oi_trend", "social_sentiment", "fear_greed",
                    "volume_change", "current_volatility", "rsi", "macd_signal"
                ],
                target="volatility_future",
                hyperparameters={
                    "n_estimators": 50,
                    "max_depth": 6,
                    "learning_rate": 0.1,
                    "loss": "squared_error",
                    "random_state": 42
                }
            )
        }
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models"""
        try:
            for model_name, config in self.model_configs.items():
                if config.model_type == "classification":
                    self.models[model_name] = RandomForestClassifier(**config.hyperparameters)
                elif config.model_type == "regression":
                    self.models[model_name] = GradientBoostingRegressor(**config.hyperparameters)
                
                self.scalers[model_name] = StandardScaler()
                
                self.logger.info(f"Initialized ML model: {model_name}")
                
        except Exception as e:
            self.logger.error(f"Error initializing ML models: {e}")
    
    async def train_model(
        self,
        model_name: str,
        training_data: List[Dict[str, Any]],
        force_retrain: bool = False
    ) -> ModelPerformance:
        """Train ML model dengan new data"""
        try:
            if model_name not in self.model_configs:
                raise ValueError(f"Model {model_name} not found")
            
            config = self.model_configs[model_name]
            
            # Check if we have enough data
            if len(training_data) < config.min_samples:
                raise ValueError(f"Insufficient training data: {len(training_data)} < {config.min_samples}")
            
            # Convert to DataFrame
            df = pd.DataFrame(training_data)
            
            # Check if all features exist
            missing_features = [f for f in config.features if f not in df.columns]
            if missing_features:
                raise ValueError(f"Missing features: {missing_features}")
            
            # Prepare features and target
            X = df[config.features]
            y = df[config.target]
            
            # Handle categorical variables
            for column in X.select_dtypes(include=['object']).columns:
                if column not in self.encoders:
                    self.encoders[column] = LabelEncoder()
                X[column] = self.encoders[column].fit_transform(X[column].astype(str))
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=config.validation_split, random_state=42, stratify=y if config.model_type == "classification" else None
            )
            
            # Scale features
            X_train_scaled = self.scalers[model_name].fit_transform(X_train)
            X_test_scaled = self.scalers[model_name].transform(X_test)
            
            # Train model
            model = self.models[model_name]
            model.fit(X_train_scaled, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test_scaled)
            
            # Calculate metrics
            if config.model_type == "classification":
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            else:  # regression
                accuracy = model.score(X_test_scaled, y_test)
                precision = 0.0  # Not applicable for regression
                recall = 0.0
                f1 = 0.0
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
            cv_score = cv_scores.mean()
            
            # Feature importance
            if hasattr(model, 'feature_importances_'):
                importance_dict = dict(zip(config.features, model.feature_importances_))
                self.feature_importance[model_name] = importance_dict
            
            # Store performance
            performance = ModelPerformance(
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                cross_val_score=cv_score,
                sample_size=len(training_data)
            )
            
            self.model_performance[model_name] = performance
            
            # Log training
            self.logger.info(f"Model {model_name} trained successfully:")
            self.logger.info(f"  Accuracy: {accuracy:.4f}")
            self.logger.info(f"  Cross-val: {cv_score:.4f}")
            self.logger.info(f"  Sample size: {len(training_data)}")
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Error training model {model_name}: {e}")
            raise
    
    async def predict(
        self,
        model_name: str,
        features: Dict[str, Any]
    ) -> PredictionResult:
        """Make prediction using trained model"""
        try:
            if model_name not in self.models:
                raise ValueError(f"Model {model_name} not found")
            
            if model_name not in self.model_performance:
                raise ValueError(f"Model {model_name} not trained yet")
            
            config = self.model_configs[model_name]
            model = self.models[model_name]
            
            # Prepare features
            feature_vector = []
            for feature in config.features:
                if feature not in features:
                    raise ValueError(f"Missing feature: {feature}")
                feature_vector.append(features[feature])
            
            # Handle categorical variables
            for i, feature in enumerate(config.features):
                if isinstance(feature_vector[i], str):
                    if feature in self.encoders:
                        try:
                            feature_vector[i] = self.encoders[feature].transform([feature_vector[i]])[0]
                        except ValueError:
                            # Handle unseen categories
                            feature_vector[i] = 0
                    else:
                        feature_vector[i] = 0
            
            # Scale features
            X_scaled = self.scalers[model_name].transform([feature_vector])
            
            # Make prediction
            prediction = model.predict(X_scaled)[0]
            
            # Get confidence (probability for classification, std for regression)
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(X_scaled)[0]
                confidence = max(probabilities)
            else:
                # For regression, use distance from mean as confidence proxy
                predictions = model.predict(X_scaled)
                confidence = 1.0 / (1.0 + np.std(predictions))
            
            # Get feature importance
            feature_importance = self.feature_importance.get(model_name, {})
            
            # Create result
            result = PredictionResult(
                prediction=float(prediction),
                confidence=float(confidence),
                feature_importance=feature_importance,
                model_version=f"{model_name}_v1",
                metadata={
                    "features_used": config.features,
                    "model_type": config.model_type
                }
            )
            
            # Store prediction history
            self.prediction_history.append({
                "model_name": model_name,
                "prediction": result.dict(),
                "input_features": features,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only last 10000 predictions
            if len(self.prediction_history) > 10000:
                self.prediction_history = self.prediction_history[-10000:]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error making prediction with {model_name}: {e}")
            raise
    
    async def batch_predict(
        self,
        model_name: str,
        features_list: List[Dict[str, Any]]
    ) -> List[PredictionResult]:
        """Make batch predictions"""
        try:
            results = []
            
            for features in features_list:
                result = await self.predict(model_name, features)
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in batch prediction: {e}")
            raise
    
    async def get_model_recommendations(
        self,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get recommendations from all models"""
        try:
            recommendations = {}
            
            for model_name in self.model_configs.keys():
                if model_name in self.model_performance:
                    try:
                        result = await self.predict(model_name, features)
                        recommendations[model_name] = result.dict()
                    except Exception as e:
                        self.logger.warning(f"Error getting recommendation from {model_name}: {e}")
            
            # Aggregate recommendations
            if recommendations:
                # For signal classification
                if "signal_classifier" in recommendations:
                    signal_pred = recommendations["signal_classifier"]["prediction"]
                    signal_conf = recommendations["signal_classifier"]["confidence"]
                    
                    # For price prediction
                    price_change = 0.0
                    price_conf = 0.0
                    if "price_predictor" in recommendations:
                        price_change = recommendations["price_predictor"]["prediction"]
                        price_conf = recommendations["price_predictor"]["confidence"]
                    
                    # Generate final recommendation
                    if signal_pred > 0.5 and price_change > 0:
                        action = "LONG"
                        strength = min(signal_conf, price_conf)
                    elif signal_pred > 0.5 and price_change < 0:
                        action = "SHORT"
                        strength = min(signal_conf, price_conf)
                    else:
                        action = "HOLD"
                        strength = 0.5
                    
                    recommendations["final_recommendation"] = {
                        "action": action,
                        "strength": strength,
                        "expected_price_change": price_change,
                        "confidence": (signal_conf + price_conf) / 2
                    }
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting model recommendations: {e}")
            raise
    
    def get_model_statistics(self) -> Dict[str, Any]:
        """Get statistics for all models"""
        try:
            stats = {
                "models": {},
                "total_predictions": len(self.prediction_history),
                "last_updated": datetime.now().isoformat()
            }
            
            for model_name, config in self.model_configs.items():
                model_stats = {
                    "config": {
                        "type": config.model_type,
                        "features": config.features,
                        "target": config.target
                    },
                    "trained": model_name in self.model_performance,
                    "performance": None,
                    "feature_importance": self.feature_importance.get(model_name, {})
                }
                
                if model_name in self.model_performance:
                    perf = self.model_performance[model_name]
                    model_stats["performance"] = perf.dict()
                
                stats["models"][model_name] = model_stats
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting model statistics: {e}")
            return {}
    
    def get_prediction_history(
        self,
        model_name: Optional[str] = None,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """Get prediction history"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours_back)
            
            filtered_history = []
            for pred in self.prediction_history:
                pred_time = datetime.fromisoformat(pred["timestamp"])
                
                if pred_time < cutoff:
                    continue
                
                if model_name and pred["model_name"] != model_name:
                    continue
                
                filtered_history.append(pred)
            
            return sorted(filtered_history, key=lambda x: x["timestamp"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error getting prediction history: {e}")
            return []
    
    async def retrain_all_models(self, training_data: Dict[str, List[Dict[str, Any]]]):
        """Retrain all models dengan new data"""
        try:
            results = {}
            
            for model_name, data in training_data.items():
                if model_name in self.model_configs:
                    try:
                        performance = await self.train_model(model_name, data)
                        results[model_name] = performance.dict()
                        self.logger.info(f"Retrained model: {model_name}")
                    except Exception as e:
                        self.logger.error(f"Error retraining {model_name}: {e}")
                        results[model_name] = {"error": str(e)}
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error retraining models: {e}")
            raise
    
    def save_models(self, path: str = "models/"):
        """Save trained models to disk"""
        try:
            import os
            os.makedirs(path, exist_ok=True)
            
            for model_name, model in self.models.items():
                if model_name in self.model_performance:
                    # Save model
                    model_path = f"{path}/{model_name}.joblib"
                    joblib.dump(model, model_path)
                    
                    # Save scaler
                    scaler_path = f"{path}/{model_name}_scaler.joblib"
                    joblib.dump(self.scalers[model_name], scaler_path)
                    
                    # Save performance
                    perf_path = f"{path}/{model_name}_performance.json"
                    with open(perf_path, 'w') as f:
                        json.dump(self.model_performance[model_name].dict(), f, indent=2, default=str)
            
            self.logger.info(f"Models saved to {path}")
            
        except Exception as e:
            self.logger.error(f"Error saving models: {e}")
    
    def load_models(self, path: str = "models/"):
        """Load trained models from disk"""
        try:
            import os
            
            for model_name in self.model_configs.keys():
                model_path = f"{path}/{model_name}.joblib"
                scaler_path = f"{path}/{model_name}_scaler.joblib"
                perf_path = f"{path}/{model_name}_performance.json"
                
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)
                    self.logger.info(f"Loaded model: {model_name}")
                
                if os.path.exists(scaler_path):
                    self.scalers[model_name] = joblib.load(scaler_path)
                
                if os.path.exists(perf_path):
                    with open(perf_path, 'r') as f:
                        perf_data = json.load(f)
                    self.model_performance[model_name] = ModelPerformance(**perf_data)
            
            self.logger.info(f"Models loaded from {path}")
            
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")


# Global instance
ml_service = MLService()
