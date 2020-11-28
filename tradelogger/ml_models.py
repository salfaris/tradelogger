from typing import List
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor

BASE_FEATURE_NAME = 'profit_loss'

def ml_prediction_sidebar_pipeline(date_ls: List, profit_loss_ls: List):
    trade_df = ml_next_trade_prep(profit_loss_ls)
    month_df = ml_next_month_prep(date_ls, profit_loss_ls)
    
    trade_pct_pred = get_pct_pred(trade_df)
    monthly_pct_pred = get_pct_pred(month_df)
    
    conv_to_val = lambda pct, current_val: pct * current_val/100.
    
    trade_val_pred = conv_to_val(trade_pct_pred, profit_loss_ls[-1])
    monthly_val_pred = conv_to_val(monthly_pct_pred, month_df.profit_loss[-1])
    
    rounded_trade_pred = round(trade_val_pred, 2)
    rounded_month_pred = round(monthly_val_pred, 2)
    
    return rounded_trade_pred, rounded_month_pred

def ml_next_trade_prep(profit_loss_ls: List):
    df = pd.DataFrame(dict(profit_loss=profit_loss_ls))
    return df

def ml_next_month_prep(date_ls: List, profit_loss_ls: List):
    df = pd.DataFrame(dict(dates=date_ls, profit_loss=profit_loss_ls))
    df.set_index('dates', inplace=True)
    
    # Sum and group by monthly profit loss
    monthly_df = pd.DataFrame(df.resample('M')[BASE_FEATURE_NAME].sum())
    return monthly_df

def get_pct_pred(df: pd.DataFrame):
    # Initial feature name(s) and target name.
    feature_names = [BASE_FEATURE_NAME]
    target_name = 'pl_pct'
    
    # Feature engineering: Consider just MA periods for now.
    ma_periods = [2, 3]
    for i in ma_periods:
        ma_name = 'ma_' + str(i)
        feature_names.append(ma_name)
        df[ma_name] = df.profit_loss.rolling(i).mean()
    
    df[target_name] = df.profit_loss.pct_change()

    df = df.dropna()
    
    features = df[feature_names]
    targets = df[target_name].values
    
    sc = MinMaxScaler()

    features = sc.fit_transform(features)
    
    preds = models(features, targets)
    
    last_pct_pred = preds.ravel()[-1]
    
    return last_pct_pred

def models(features, targets):
    rfr = RandomForestRegressor(n_estimators=200,
                            max_depth=5,
                            max_features=2,
                            min_samples_split=4,
                            oob_score=True,
                            random_state=44)

    # knn = KNeighborsRegressor(n_neighbors=7)
    
    models = [rfr]
    
    preds = []
    
    for model in models:
        model.fit(features, targets)
        pred = model.predict(features).reshape(1, -1)
        preds.append(pred)
    
    ensemble_preds = np.mean(np.vstack(tuple(preds)), axis=0)
    
    return ensemble_preds