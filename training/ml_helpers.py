import datetime
import random

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score

def gen_random_dates(start_date, end_date, num):
    rand_dates = []

    for _ in range(num):
        days_diff_dates = (end_date - start_date).days
        random_num_days = random.randrange(days_diff_dates)
        new_date = start_date + datetime.timedelta(days=random_num_days)
        rand_dates.append(new_date)

    rand_dates.sort()
    return rand_dates

def pred_scores(y_train, y_test, y_train_pred, y_test_pred):
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    
    print(f"RMSE Train: {train_rmse}")
    print(f"RMSE Test: {test_rmse}")
    print()
    print(f"R2 Train: {train_r2}")
    print(f"R2 Test: {test_r2}")
    print()
    

def model_res(model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    plot_predict(y_train, y_test, y_train_pred, y_test_pred)

def plot_predict(y_train, y_test, y_train_pred, y_test_pred):
    pred_scores(y_train, y_test, y_train_pred, y_test_pred)
    _, ax = plt.subplots()

    ax.scatter(y_train_pred, y_train, label='train')
    ax.scatter(y_test_pred, y_test, label='test')

    ax.set_xlabel('predictions')
    ax.set_ylabel('actual')
    ax.legend(loc='best')
    ax.axis('equal')
    ax.set(xlim=(-4, 4), ylim=(-4, 4))
    plt.show()
