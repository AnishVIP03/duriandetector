"""ML Engine — model training, inference, and feature processing.

Hybrid ML pipeline supporting:
- Random Forest: primary supervised multi-class classifier
- SVM: secondary supervised classifier
- Isolation Forest: unsupervised anomaly detection for zero-day threats

Trained on CICIDS2017 real attack dataset + enhanced synthetic data.
"""
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
    """
    Main IDS ML engine — hybrid supervised + unsupervised detection.

    Uses Random Forest (primary) + SVM (secondary) for known attack classification,
    and Isolation Forest for zero-day anomaly detection.
    """

    def __init__(self, environment_id=None, model_type='random_forest'):
        self.environment_id = environment_id
        self.model_type = model_type
        self.model = None
        self.scaler = None
        self.svm_model = None
        self.iso_model = None
        self._load_or_create()

    def _get_model_path(self):
        return MODEL_DIR / f'model_env_{self.environment_id}.joblib'

    def _get_scaler_path(self):
        return MODEL_DIR / f'scaler_env_{self.environment_id}.joblib'

    def _get_svm_path(self):
        return MODEL_DIR / f'svm_env_{self.environment_id}.joblib'

    def _get_iso_path(self):
        return MODEL_DIR / f'iso_env_{self.environment_id}.joblib'

    def _load_or_create(self):
        """Load existing models or create defaults."""
        model_path = self._get_model_path()
        scaler_path = self._get_scaler_path()
        svm_path = self._get_svm_path()
        iso_path = self._get_iso_path()

        if model_path.exists() and scaler_path.exists():
            try:
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                logger.info(f"Loaded Random Forest model for env {self.environment_id}")
            except Exception as e:
                logger.warning(f"Failed to load RF model: {e}")

        # Load SVM if available
        if svm_path.exists():
            try:
                self.svm_model = joblib.load(svm_path)
                logger.info(f"Loaded SVM model for env {self.environment_id}")
            except Exception as e:
                logger.warning(f"Failed to load SVM: {e}")

        # Load Isolation Forest if available
        if iso_path.exists():
            try:
                self.iso_model = joblib.load(iso_path)
                logger.info(f"Loaded Isolation Forest for env {self.environment_id}")
            except Exception as e:
                logger.warning(f"Failed to load IsoForest: {e}")

        # If no models loaded at all, train defaults
        if self.model is None or self.scaler is None:
            self._train_default()

    def _generate_synthetic_data(self, n_samples=50000):
        """Generate enhanced synthetic training data for bootstrap.

        This is only used as fallback when pre-trained models are not available.
        For production, run train_real_model.py to train on CICIDS2017.
        """
        np.random.seed(42)
        data = []
        labels = []

        # Normal traffic - 50%
        for _ in range(n_samples // 2):
            profile = np.random.choice(['web', 'dns', 'ssh', 'streaming'])
            if profile == 'web':
                data.append([
                    np.random.lognormal(5.5, 1.0), np.random.choice([64, 128, 255]),
                    np.random.randint(1024, 65535), np.random.choice([80, 443, 8080]),
                    6, np.random.choice([16, 24, 18]),
                    np.random.exponential(0.5), np.random.lognormal(8, 2),
                    np.random.randint(1, 15), np.random.uniform(0, 1.5),
                ])
            elif profile == 'dns':
                data.append([
                    np.random.randint(40, 512), np.random.choice([64, 128]),
                    np.random.randint(1024, 65535), 53,
                    17, 0,
                    np.random.exponential(0.3), np.random.lognormal(7, 1),
                    np.random.randint(1, 5), np.random.uniform(0, 0.5),
                ])
            elif profile == 'ssh':
                data.append([
                    np.random.randint(40, 1000), np.random.choice([64, 128]),
                    np.random.randint(1024, 65535), 22,
                    6, np.random.choice([16, 24]),
                    np.random.exponential(1.0), np.random.lognormal(6, 2),
                    np.random.randint(1, 3), np.random.uniform(0, 0.3),
                ])
            else:
                data.append([
                    np.random.randint(500, 1500), np.random.choice([64, 128]),
                    np.random.randint(1024, 65535), np.random.choice([443, 8080]),
                    np.random.choice([6, 17]), np.random.choice([16, 24]),
                    np.random.uniform(0.001, 0.05), np.random.lognormal(10, 1),
                    np.random.randint(1, 5), np.random.uniform(0, 0.5),
                ])
            labels.append(0)

        # Port scan - 10%
        for _ in range(n_samples // 10):
            flags = np.random.choice([2, 1, 41, 0])  # SYN, FIN, XMAS, NULL scan
            data.append([
                np.random.randint(40, 80), np.random.choice([64, 128, 255]),
                np.random.randint(1024, 65535), np.random.randint(1, 65535),
                6, flags,
                np.random.uniform(0.0001, 0.05), np.random.uniform(500, 10000),
                np.random.randint(50, 1000), np.random.uniform(3.5, 8.0),
            ])
            labels.append(1)

        # DoS/DDoS - 10%
        for _ in range(n_samples // 10):
            attack = np.random.choice(['syn_flood', 'udp_flood', 'http_flood'])
            if attack == 'syn_flood':
                data.append([
                    np.random.randint(40, 80), np.random.choice([64, 128, 255]),
                    np.random.randint(1024, 65535), np.random.choice([80, 443]),
                    6, 2,
                    np.random.uniform(0.00001, 0.001), np.random.uniform(50000, 1000000),
                    np.random.randint(200, 5000), np.random.uniform(0, 1),
                ])
            elif attack == 'udp_flood':
                data.append([
                    np.random.randint(40, 1500), np.random.choice([64, 128]),
                    np.random.randint(1024, 65535), np.random.randint(1, 65535),
                    17, 0,
                    np.random.uniform(0.00001, 0.0005), np.random.uniform(100000, 5000000),
                    np.random.randint(500, 10000), np.random.uniform(0, 2),
                ])
            else:
                data.append([
                    np.random.randint(200, 1500), np.random.choice([64, 128]),
                    np.random.randint(1024, 65535), np.random.choice([80, 443]),
                    6, 24,
                    np.random.uniform(0.0001, 0.01), np.random.uniform(50000, 500000),
                    np.random.randint(100, 2000), np.random.uniform(0, 0.5),
                ])
            labels.append(2)

        # Brute force - 10%
        for _ in range(n_samples // 10):
            dst = np.random.choice([22, 21, 3389, 80, 443])
            data.append([
                np.random.randint(100, 800), np.random.choice([64, 128]),
                np.random.randint(1024, 65535), dst,
                6, np.random.choice([16, 24, 18]),
                np.random.uniform(0.05, 2.0), np.random.uniform(5000, 50000),
                np.random.randint(20, 300), np.random.uniform(0, 0.5),
            ])
            labels.append(3)

        # Protocol anomaly - 10%
        for _ in range(n_samples // 10):
            atype = np.random.choice(['oversized', 'low_ttl', 'weird_flags', 'unusual_proto'])
            if atype == 'oversized':
                data.append([
                    np.random.randint(1500, 9000), np.random.randint(32, 128),
                    np.random.randint(1, 65535), np.random.randint(1, 65535),
                    np.random.choice([6, 17]), np.random.randint(0, 255),
                    np.random.uniform(0.001, 5), np.random.uniform(10000, 500000),
                    np.random.randint(1, 50), np.random.uniform(0, 5),
                ])
            elif atype == 'low_ttl':
                data.append([
                    np.random.randint(40, 1500), np.random.randint(1, 10),
                    np.random.randint(1, 65535), np.random.randint(1, 65535),
                    np.random.choice([1, 6, 17]), np.random.randint(0, 255),
                    np.random.uniform(0.001, 5), np.random.uniform(100, 100000),
                    np.random.randint(1, 50), np.random.uniform(0, 5),
                ])
            elif atype == 'weird_flags':
                data.append([
                    np.random.randint(40, 500), np.random.randint(32, 128),
                    np.random.randint(1024, 65535), np.random.randint(1, 65535),
                    6, np.random.choice([41, 37, 63, 255]),
                    np.random.uniform(0.001, 2), np.random.uniform(100, 50000),
                    np.random.randint(1, 100), np.random.uniform(0, 5),
                ])
            else:
                data.append([
                    np.random.randint(40, 1500), np.random.randint(1, 64),
                    0, 0,
                    np.random.choice([1, 2, 47, 50, 51, 89]), 0,
                    np.random.uniform(0.001, 10), np.random.uniform(10, 100000),
                    np.random.randint(1, 30), np.random.uniform(0, 3),
                ])
            labels.append(4)

        # Suspicious IP / C2 - 10%
        for _ in range(n_samples // 10):
            c2 = np.random.choice(['beacon', 'exfil', 'tunnel'])
            if c2 == 'beacon':
                data.append([
                    np.random.randint(40, 300), np.random.choice([64, 128]),
                    np.random.randint(1024, 65535), np.random.choice([443, 8443, 4443]),
                    6, np.random.choice([16, 24]),
                    np.random.normal(60, 5), np.random.uniform(100, 5000),
                    np.random.randint(5, 50), np.random.uniform(0.5, 2),
                ])
            elif c2 == 'exfil':
                data.append([
                    np.random.randint(1000, 1500), np.random.choice([64, 128]),
                    np.random.randint(1024, 65535), np.random.choice([443, 53, 8080]),
                    np.random.choice([6, 17]), np.random.choice([16, 24]),
                    np.random.uniform(0.01, 0.5), np.random.lognormal(11, 1),
                    np.random.randint(10, 100), np.random.uniform(0.5, 2.5),
                ])
            else:
                data.append([
                    np.random.randint(100, 512), np.random.choice([64, 128]),
                    np.random.randint(1024, 65535), 53,
                    17, 0,
                    np.random.uniform(0.01, 1), np.random.uniform(5000, 50000),
                    np.random.randint(20, 200), np.random.uniform(1, 4),
                ])
            labels.append(5)

        return np.array(data, dtype=np.float64), np.array(labels)

    def _train_default(self):
        """Train a default model with enhanced synthetic data."""
        logger.info(f"Training default model for env {self.environment_id}")
        X, y = self._generate_synthetic_data(n_samples=50000)

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.model = RandomForestClassifier(
            n_estimators=200, max_depth=20, min_samples_split=5,
            min_samples_leaf=2, random_state=42, n_jobs=-1,
            class_weight='balanced',
        )
        self.model.fit(X_scaled, y)

        # Save
        joblib.dump(self.model, self._get_model_path())
        joblib.dump(self.scaler, self._get_scaler_path())
        logger.info("Default model trained and saved")

    def predict(self, features):
        """
        Hybrid prediction using multiple models.

        1. Random Forest or SVM for supervised classification
        2. Isolation Forest for anomaly scoring (zero-day detection)
        3. Combine results: if supervised says normal but IsoForest says anomaly,
           flag as protocol_anomaly with adjusted confidence.

        Returns: (label_str, confidence_score, probabilities_dict)
        """
        if self.model is None or self.scaler is None:
            self._load_or_create()

        features_arr = np.array(features).reshape(1, -1)
        features_scaled = self.scaler.transform(features_arr)

        # --- Supervised classification ---
        active_model = self.model
        if self.model_type == 'svm' and self.svm_model is not None:
            active_model = self.svm_model

        prediction = active_model.predict(features_scaled)[0]
        label = LABEL_MAP.get(prediction, 'unknown')

        # Get confidence
        if hasattr(active_model, 'predict_proba'):
            probas = active_model.predict_proba(features_scaled)[0]
            confidence = float(max(probas))
            prob_dict = {
                LABEL_MAP.get(i, 'unknown'): float(p)
                for i, p in enumerate(probas)
            }
        else:
            confidence = 0.85
            prob_dict = {label: confidence}

        # --- Anomaly detection (Isolation Forest) ---
        if self.iso_model is not None:
            try:
                anomaly_score = self.iso_model.decision_function(features_scaled)[0]
                is_anomaly = self.iso_model.predict(features_scaled)[0] == -1

                # If supervised says normal but IsoForest detects anomaly,
                # this could be a zero-day attack
                if label == 'normal' and is_anomaly:
                    # Anomaly score is negative for anomalies, more negative = more anomalous
                    anomaly_confidence = min(0.95, max(0.5, 0.7 - anomaly_score))
                    label = 'protocol_anomaly'
                    confidence = anomaly_confidence
                    prob_dict['protocol_anomaly'] = anomaly_confidence
                    prob_dict['normal'] = 1.0 - anomaly_confidence
                    prob_dict['_anomaly_detected'] = True
                    prob_dict['_anomaly_score'] = float(anomaly_score)

                # If supervised detects attack AND IsoForest agrees, boost confidence
                elif label != 'normal' and is_anomaly:
                    confidence = min(0.99, confidence * 1.15)

                # Add anomaly info to prob_dict for transparency
                prob_dict['_iso_anomaly'] = bool(is_anomaly)
                prob_dict['_iso_score'] = float(anomaly_score)

            except Exception as e:
                logger.debug(f"Isolation Forest error: {e}")

        # --- Cross-model validation (RF vs SVM) ---
        if (self.model_type == 'random_forest' and self.svm_model is not None
                and label != 'normal'):
            try:
                svm_pred = self.svm_model.predict(features_scaled)[0]
                svm_label = LABEL_MAP.get(svm_pred, 'unknown')
                if svm_label == label:
                    # Both models agree — boost confidence
                    confidence = min(0.99, confidence * 1.1)
                    prob_dict['_model_agreement'] = True
                else:
                    prob_dict['_model_agreement'] = False
                    prob_dict['_svm_prediction'] = svm_label
            except Exception:
                pass

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
                n_estimators=200, max_depth=20, min_samples_split=5,
                min_samples_leaf=2, random_state=42, n_jobs=-1,
                class_weight='balanced',
            )
        elif model_type == 'svm':
            self.model = SVC(
                probability=True, kernel='rbf', C=10,
                gamma='scale', random_state=42, class_weight='balanced',
            )
        elif model_type == 'isolation_forest':
            self.model = IsolationForest(
                n_estimators=200, contamination=0.1, random_state=42
            )
        else:
            self.model = RandomForestClassifier(
                n_estimators=200, random_state=42, n_jobs=-1
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
