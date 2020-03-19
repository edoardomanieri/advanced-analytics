import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from CustomImputer import DataFrameImputer
import xgboost as xgb
from sklearn.linear_model import LinearRegression, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import utils
from pathlib import Path
from datetime import datetime


directory = "./results/" + datetime.now().strftime("%m-%d-%Y,%H:%M:%S")
Path(directory).mkdir(parents=True, exist_ok=True)
report_file = open(directory + "/report", "w+")

##### min_price
report_file.write("MIN PRICE \n")
train_min = pd.read_csv("train.csv")
train_min.drop(columns=['max_price'], inplace=True)
test_min = pd.read_csv("test.csv")
df = utils.merge_train_test(train_min, test_min, 'min_price')

cat_vars = ['name', 'brand', 'base_name', 'cpu', 'cpu_details', 'gpu', 'os', 'os_details', 'screen_surface']
dummy_vars = ['touchscreen', 'detachable_keyboard', 'discrete_gpu']
target_vars = ['min_price', 'max_price']
target = 'min_price'
num_vars = [col for col in df.columns if col not in cat_vars + dummy_vars + target_vars]
variable_lists = [cat_vars, dummy_vars, target_vars, num_vars]

df = utils.imputation(df, report_file=report_file)
utils.drop_columns(df, ['name', 'base_name', 'pixels_y'], variable_lists, report_file=report_file)
utils.smooth_handling(df, cat_vars, target, report_file=report_file)

estimator = xgb.XGBRegressor(n_estimators=200, max_depth=4, gamma=1, colsample_bytree=0.6, subsample=1, min_child_weight=15)
df_min = utils.fit_predict(df, estimator, target, 'id', 'MIN', report_file=report_file)
df_complete_predictions = utils.get_predictions(df, estimator, target, 'id', 'min_price_pred')
report_file.write("\n\n\n")

##### max_price
report_file.write("MAX PRICE \n")
train_max = pd.read_csv("train.csv")
train_max.drop(columns=['min_price'], inplace=True)
test_max = pd.read_csv("test.csv")
df = utils.merge_train_test(train_max, test_max, 'max_price')

cat_vars = ['name', 'brand', 'base_name', 'cpu', 'cpu_details', 'gpu', 'os', 'os_details', 'screen_surface']
dummy_vars = ['touchscreen', 'detachable_keyboard', 'discrete_gpu']
target_vars = ['min_price', 'max_price']
target = 'max_price'
num_vars = [col for col in df.columns if col not in cat_vars + dummy_vars + target_vars]
variable_lists = [cat_vars, dummy_vars, target_vars, num_vars]

df = utils.imputation(df, report_file=report_file)
utils.drop_columns(df, ['name', 'base_name', 'pixels_y'], variable_lists, report_file=report_file)
df = df.merge(df_complete_predictions, on='id')
utils.smooth_handling(df, cat_vars, target, report_file=report_file)

estimator = xgb.XGBRegressor(n_estimators=200, max_depth=4, gamma=1, colsample_bytree=0.6, subsample=1, min_child_weight=15)
df_max = utils.fit_predict(df, estimator, target, 'id', 'MAX', report_file=report_file)
report_file.write("\n\n\n")

# put together predictions
report_file.write("MERGING \n")
df_out = df_min.merge(df_max, on="id").set_index("id")
df_out.loc[df_out['MAX'] < df_out['MIN'], ['MIN', 'MAX']] = df_out.loc[df_out['MAX'] < df_out['MIN'], ['MIN', 'MAX']].mean(axis=1)
report_file.write("replace values where max smaller than min with mean of two values \n")
report_file.close()
df_out.to_csv(directory + "/result.csv")

