from typing import List
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor

def ml_pipeline(profit_loss_ls: List):
    df = pd.DataFrame(dict(profit_loss=profit_loss_ls))

    target_name = 'pl_pct'
    
    df[target_name] = df.profit_loss.pct_change()
    feature_names = ['profit_loss']

    ma_periods = [1]
    for i in ma_periods:
        ma_name = 'ma_' + str(i)
        feature_names.append(ma_name)
        df[ma_name] = df.profit_loss.rolling(i).mean()

    df = df.dropna()
    
    features = df[feature_names]
    targets = df[target_name]
    targets = targets.values
    
    sc = MinMaxScaler()

    features = sc.fit_transform(features)
    preds = models(features, targets)
    
    last_pct_pred = preds.ravel()[-1]
    
    trade_pred = last_pct_pred * (profit_loss_ls[-1]/100.)
    trade_pred = round(trade_pred, 2)
    
    return trade_pred

def models(features, targets):
    rfr = RandomForestRegressor(n_estimators=200,
                            max_depth=5,
                            max_features=2,
                            min_samples_split=4,
                            oob_score=True,
                            random_state=44)

    knn = KNeighborsRegressor(n_neighbors=7)
    
    models = [rfr, knn]
    
    preds = []
    
    for model in models:
        model.fit(features, targets)
        pred = model.predict(features).reshape(1, -1)
        preds.append(pred)
    
    ensemble_preds = np.mean(np.vstack(tuple(preds)), axis=0)
    
    return ensemble_preds