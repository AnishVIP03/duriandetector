"""ML Engine — model training, inference, and feature processing."""
import os
import joblib
import logging
import numpy as np
from pathlib import Path
from django.conf import settings
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)
MODEL_DIR = Path(settings.BASE_DIR) / 'ml_models'
MODEL_DIR.mkdir(exist_ok=True)

# Feature names for the model (extracted from packets)
FEATURE_NAMES = [
    'packet_length', 'ttl', 'src_port', 'dst_port',
    'protocol_num', 'tcp_flags_num', 'inter_arrival_time',
    'byte_rate', 'connection_count', 'port_entropy',
]

# Attack type labels
LABEL_MAP = {
    0: 'normal',
    1: 'port_scan',
    2: 'dos',
    3: 'brute_force',
    4: 'protocol_anomaly',
    5: 'suspicious_ip',
}
REVERSE_LABEL_MAP = {v: k for k, v in LABEL_MAP.items()}


class IDSEngine:
    """Main IDS ML engine — handles training, prediction, and model management."""

    def __init__(self, environment_id=None):
        self.environment_id = environment_id
        self.model = None
        self.scaler = None
        self._load_or_create()

    def _get_model_path(self):
        return MODEL_DIR / f'model_env_{self.environment_id}.joblib'

    def _get_scaler_path(self):
        return MODEL_DIR / f'scaler_env_{self.environment_id}.joblib'

    def _load_or_create(self):
        """Load existing model or create default."""
        model_path = self._get_model_path()
        scaler_path = self._get_scaler_path()

        if model_path.exists() and scaler_path.exists():
            try:
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                logger.info(f"Loaded model for env {self.environment_id}")
                return
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")

        # Create default model with synthetic training data
        self._train_default()

    def _generate_synthetic_data(self, n_samples=5000):
        """Generate synthetic training data for bootstrap."""
        np.random.seed(42)
        data = []
        labels = []

        # Normal traffic
        for _ in range(n_samples // 2):
            data.append([
                np.random.randint(40, 1500),   # packet_length
                np.random.randint(32, 128),     # ttl
                np.random.randint(1024, 65535), # src_port
                np.random.choice([80, 443, 8080, 3306, 22, 53]),  # dst_port
                np.random.choice([6, 17]),      # protocol (TCP=6, UDP=17)
                np.random.randint(0, 32),       # tcp_flags
                np.random.uniform(0.001, 2.0),  # inter_arrival_time
                np.random.uniform(100, 50000),  # byte_rate
                np.random.randint(1, 10),       # connection_count
                np.random.uniform(0, 2),        # port_entropy
            ])
            labels.append(0)  # normal

        # Port scan
        for _ in range(n_samples // 10):
            data.append([
                np.random.randint(40, 100), np.random.randint(64, 128),
                np.random.randint(1024, 65535),
                np.random.randint(1, 65535),    # random dst ports
                6, 2,                           # TCP SYN
                np.random.uniform(0.0001, 0.01),
                np.random.uniform(100, 5000),
                np.random.randint(50, 500),     # high connection count
                np.random.uniform(4, 8),        # high port entropy
            ])
            labels.append(1)

        # DoS
        for _ in range(n_samples // 10):
            data.append([
                np.random.randint(40, 200), np.random.randint(64, 128),
                np.random.randint(1024, 65535), np.random.choice([80, 443]),
                6, np.random.choice([2, 18]),
                np.random.uniform(0.00001, 0.001),  # very fast
                np.random.uniform(50000, 500000),    # high byte rate
                np.random.randint(100, 1000),
                np.random.uniform(0, 1),
            ])
            labels.append(2)

        # Brute force
        for _ in range(n_samples // 10):
            data.append([
                np.random.randint(40, 500), np.random.randint(64, 128),
                np.random.randint(1024, 65535), np.random.choice([22, 3389, 21]),
                6, np.random.randint(0, 32),
                np.random.uniform(0.1, 1.0),
                np.random.uniform(1000, 20000),
                np.random.randint(20, 200),
                np.random.uniform(0, 0.5),
            ])
            labels.append(3)

        # Protocol anomaly
        for _ in range(n_samples // 10):
            data.append([
                np.random.randint(1400, 9000),  # oversized
                np.random.randint(1, 20),       # low TTL
                np.random.randint(1, 1023),     # privileged port
                np.random.randint(1, 65535),
                np.random.choice([1, 47, 50]),  # unusual protocols (ICMP, GRE, ESP)
                np.random.randint(0, 255),
                np.random.uniform(0.0001, 5),
                np.random.uniform(10, 100000),
                np.random.randint(1, 50),
                np.random.uniform(0, 5),
            ])
            labels.append(4)

        # Suspicious IP (similar to normal but from known bad patterns)
        for _ in range(n_samples // 10):
            data.append([
                np.random.randint(40, 1500), np.random.randint(32, 64),
                np.random.randint(1024, 65535), np.random.choice([80, 443, 8443, 4443]),
                6, np.random.randint(0, 32),
                np.random.uniform(0.01, 0.5),
                np.random.uniform(5000, 80000),
                np.random.randint(5, 30),
                np.random.uniform(1, 4),
            ])
            labels.append(5)

        return np.array(data), np.array(labels)

    def _train_default(self):
        """Train a default model with synthetic data."""
        logger.info(f"Training default model for env {self.environment_id}")
        X, y = self._generate_synthetic_data()

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.model = RandomForestClassifier(
            n_estimators=100, max_depth=15, random_state=42, n_jobs=-1
        )
        self.model.fit(X_scaled, y)

        # Save
        joblib.dump(self.model, self._get_model_path())
        joblib.dump(self.scaler, self._get_scaler_path())
        logger.info("Default model trained and saved")

    def predict(self, features):
        """
        Predict attack type for a single feature vector.
        Returns: (label_str, confidence_score, probabilities_dict)
        """
        if self.model is None or self.scaler is None:
            self._load_or_create()

        features_arr = np.array(features).reshape(1, -1)
        features_scaled = self.scaler.transform(features_arr)

        prediction = self.model.predict(features_scaled)[0]
        label = LABEL_MAP.get(prediction, 'unknown')

        # Get confidence (probability for the predicted class)
        if hasattr(self.model, 'predict_proba'):
            probas = self.model.predict_proba(features_scaled)[0]
            confidence = float(max(probas))
            prob_dict = {
                LABEL_MAP.get(i, 'unknown'): float(p)
                for i, p in enumerate(probas)
            }
        else:
            confidence = 0.85  # default for SVM
            prob_dict = {label: confidence}

        return label, confidence, prob_dict

    def train(self, X, y, model_type='random_forest'):
        """Train a new model with provided data."""
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )

        if model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100, max_depth=15, random_state=42, n_jobs=-1
            )
        elif model_type == 'svm':
            self.model = SVC(probability=True, kernel='rbf', random_state=42)
        elif model_type == 'isolation_forest':
            self.model = IsolationForest(
                n_estimators=100, contamination=0.1, random_state=42
            )
        else:
            self.model = RandomForestClassifier(
                n_estimators=100, random_state=42, n_jobs=-1
            )

        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(
                y_test, y_pred, average='weighted', zero_division=0
            )),
            'recall': float(recall_score(
                y_test, y_pred, average='weighted', zero_division=0
            )),
            'f1_score': float(f1_score(
                y_test, y_pred, average='weighted', zero_division=0
            )),
            'training_samples': len(X_train),
        }

        # Save
        joblib.dump(self.model, self._get_model_path())
        joblib.dump(self.scaler, self._get_scaler_path())

        return metrics

    def get_feature_importance(self):
        """Get feature importance (for Random Forest)."""
        if hasattr(self.model, 'feature_importances_'):
            return dict(zip(
                FEATURE_NAMES, self.model.feature_importances_.tolist()
            ))
        return {}
