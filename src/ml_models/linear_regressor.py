import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression


class LinearRegressorPredictor:
    def __init__(self, look_back=10):
        self.look_back = look_back
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = LinearRegression()

    def prepare_data(self, closes):
        scaled = self.scaler.fit_transform(np.array(closes[-100:]).reshape(-1, 1))
        X, y = [], []
        for i in range(len(scaled) - self.look_back):
            X.append(scaled[i:i + self.look_back, 0])
            y.append(scaled[i + self.look_back, 0])
        return np.array(X), np.array(y), scaled

    def train(self, closes):
        X, y, _ = self.prepare_data(closes)
        self.model.fit(X, y)
        return self

    def predict_next(self, closes):
        _, _, scaled = self.prepare_data(closes)
        input_seq = scaled[-self.look_back:].flatten().reshape(1, -1)
        prediction = self.model.predict(input_seq)
        return self.scaler.inverse_transform(prediction.reshape(-1, 1))[0, 0]
