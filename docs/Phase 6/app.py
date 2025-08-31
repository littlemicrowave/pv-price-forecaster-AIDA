from flask import Flask, request, render_template
import joblib as jbl
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
import os
import pandas as pd
import numpy as np
import tensorflow as tf


app = Flask(__name__)

def scale_days(day_num, max_range, to_shift_max=365*2):
    return float(day_num) / (max_range + to_shift_max)

script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "../Phase 5/")
column_data = jbl.load(data_dir + "column_data20.pkl")
min_date = jbl.load(data_dir + "min_date0.pkl")
max_date = jbl.load(data_dir + "max_date0.pkl") + pd.Timedelta(days=365 * 2)
max_range = (max_date - min_date).days

unique_catergories = jbl.load(data_dir + "unique_categories20.pkl")
categorical_encoders = jbl.load(data_dir + "categorical_encoders20.pkl")
categorical_scalers = jbl.load(data_dir + "categorical_scalers20.pkl")
binary_encoders = jbl.load(data_dir + "binary_encoders20.pkl")
continous_scalers = jbl.load(data_dir + "continous_scalers20.pkl")
y_scalers = jbl.load(data_dir + "y_scalers20.pkl")
model = xgb.XGBRegressor()
model.load_model(data_dir + "xgb20.json")
#dense_model = tf.keras.models.load_model(data_dir + "dense.h5")
yes_no_cols = {col:["Yes", "No"] for col in column_data["Binary"] if col != "customer"}
binary_cols = column_data["Binary"]
categorical_cols = column_data["Categorial"]
continous_cols = column_data["Continous"]
print(continous_scalers)


@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None

    if request.method == "POST":
        #selected_model = request.form.get("model_choice", "xgb")

        query = pd.DataFrame({key: [request.form[key]] for key in request.form if key != "model_choice"})
        query = query[binary_cols + categorical_cols + continous_cols]
        query["days_from_first"] = pd.to_datetime(query["days_from_first"])
        for col, encoder in binary_encoders.items():
            query[col] = encoder.transform(query[col])
        for col, encoder in categorical_encoders.items():
            query[col] = encoder.transform(query[col])
        for col, scaler in categorical_scalers.items():
            query[col] = scaler.transform(query[col].to_numpy().reshape(-1,1))
        for col, scaler in continous_scalers.items():
            query[col] = scaler.transform(query[col].to_numpy().reshape(-1,1))
        query["days_from_first"] = query["days_from_first"].apply(lambda x: (x - min_date).days)
        query["days_from_first"] = query["days_from_first"].apply(lambda x: scale_days(x, max_range))
        query = query.to_numpy()
        prediction_raw = None
        #if selected_model == "xgb":
        prediction_raw = model.predict(query).reshape(-1, 1)
        '''
        elif  selected_model == "dense":
            query_dense = [query[:,:len(binary_cols)], query[:,len(binary_cols):len(binary_cols) + len(categorical_cols)], query[:,len(binary_cols) + len(categorical_cols):]]
            prediction_raw = dense_model.predict(query_dense)
        '''
        prediction = round(y_scalers["price_per_module"].inverse_transform(prediction_raw)[0, 0], 2)

    return render_template("index.html",
                           prediction=prediction,
                      #     selected_model = selected_model,
                           yes_no_cols=yes_no_cols,
                           customer_values = ["Business", "Consumer"],
                           categorical_cols=unique_catergories,
                           continuous_features=continous_cols,
                           min_date = min_date.strftime('%Y-%m-%d'),
                           max_date = max_date.strftime('%Y-%m-%d'), 
                           min_power = continous_scalers["power_per_module"].inverse_transform([[0]])[0, 0].round(2) + 0.01, 
                           max_power = continous_scalers["power_per_module"].inverse_transform([[1]])[0, 0].round(2) - 0.01 )


if __name__ == '__main__':
    app.run(debug=True)