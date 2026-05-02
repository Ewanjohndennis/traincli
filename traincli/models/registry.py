from sklearn.linear_model import LinearRegression, Ridge, LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.svm import SVC, SVR
from xgboost import XGBClassifier, XGBRegressor

# Each entry:
#   key         — CLI flag value (--model random_forest)
#   label       — display name
#   description — plain English, shown in --model ? picker
#   class       — actual sklearn/xgb class
#   recommended_max_rows — above this, model may be slow (None = no limit)

REGISTRY = {
    "regression": [
        {
            "key": "linear_regression",
            "label": "Linear Regression",
            "description": "fast, interpretable, best when relationships are roughly linear",
            "class": LinearRegression,
            "params": {},
            "recommended_max_rows": None,
        },
        {
            "key": "ridge",
            "label": "Ridge Regression",
            "description": "like linear regression but handles correlated features better",
            "class": Ridge,
            "params": {"alpha": 1.0},
            "recommended_max_rows": None,
        },
        {
            "key": "random_forest",
            "label": "Random Forest",
            "description": "robust, handles non-linear patterns, good all-round default",
            "class": RandomForestRegressor,
            "params": {"n_estimators": 100, "max_depth": 8, "random_state": 42},
            "recommended_max_rows": None,
        },
        {
            "key": "gradient_boosting",
            "label": "Gradient Boosting",
            "description": "often highest accuracy, slower to train",
            "class": GradientBoostingRegressor,
            "params": {"n_estimators": 100, "max_depth": 4, "random_state": 42},
            "recommended_max_rows": 50000,
        },
        {
            "key": "xgboost",
            "label": "XGBoost",
            "description": "like gradient boosting but faster, great for larger datasets",
            "class": XGBRegressor,
            "params": {"n_estimators": 100, "max_depth": 6, "random_state": 42, "verbosity": 0},
            "recommended_max_rows": None,
        },
        {
            "key": "svr",
            "label": "SVR",
            "description": "good for smaller datasets with complex patterns",
            "class": SVR,
            "params": {"kernel": "rbf"},
            "recommended_max_rows": 10000,
        },
    ],
    "classification": [
        {
            "key": "logistic_regression",
            "label": "Logistic Regression",
            "description": "fast, interpretable, works well for linearly separable classes",
            "class": LogisticRegression,
            "params": {"max_iter": 1000, "random_state": 42},
            "recommended_max_rows": None,
        },
        {
            "key": "random_forest",
            "label": "Random Forest",
            "description": "robust, handles non-linear patterns, good all-round default",
            "class": RandomForestClassifier,
            "params": {"n_estimators": 100, "max_depth": 8, "random_state": 42},
            "recommended_max_rows": None,
        },
        {
            "key": "gradient_boosting",
            "label": "Gradient Boosting",
            "description": "often highest accuracy, slower to train",
            "class": GradientBoostingClassifier,
            "params": {"n_estimators": 100, "max_depth": 4, "random_state": 42},
            "recommended_max_rows": 50000,
        },
        {
            "key": "xgboost",
            "label": "XGBoost",
            "description": "like gradient boosting but faster, handles imbalanced classes well",
            "class": XGBClassifier,
            "params": {"n_estimators": 100, "max_depth": 6, "random_state": 42, "verbosity": 0},
            "recommended_max_rows": None,
        },
        {
            "key": "svm",
            "label": "SVM",
            "description": "strong on smaller datasets, good with clear class boundaries",
            "class": SVC,
            "params": {"kernel": "rbf", "probability": True, "random_state": 42},
            "recommended_max_rows": 10000,
        },
    ],
}

# Cross-task models (appear in both)
CROSS_TASK = {"random_forest", "gradient_boosting", "xgboost"}

def get_model(problem_type: str, key: str):
    """Get model entry by problem type and key."""
    models = REGISTRY.get(problem_type, [])
    for m in models:
        if m["key"] == key:
            return m
    return None

def get_default(problem_type: str):
    """Get the recommended default model for a problem type."""
    defaults = {
        "regression": "random_forest",
        "classification": "random_forest",
    }
    return get_model(problem_type, defaults.get(problem_type, "random_forest"))