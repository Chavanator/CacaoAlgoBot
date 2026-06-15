import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense


class LSTMPredictor:
    def __init__(self, look_back=5, units=50):
        self.look_back = look_back
        self.units = units
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None

    def build_model(self, input_shape):
        model = Sequential()
        model.add(LSTM(units=self.units, return_sequences=True, input_shape=input_shape))
        model.add(LSTM(units=self.units))
        model.add(Dense(1))
        model.compile(optimizer='adam', loss='mean_squared_error')
        self.model = model
        return model

    def prepare_data(self, closes):
        scaled = self.scaler.fit_transform(np.array(closes).reshape(-1, 1))
        X, y = [], []
        for i in range(len(scaled) - self.look_back):
            X.append(scaled[i:i + self.look_back, 0])
            y.append(scaled[i + self.look_back, 0])
        X = np.array(X)
        y = np.array(y)
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))
        return X, y, scaled

    def train(self, closes, epochs=1, batch_size=1, verbose=2):
        X, y, _ = self.prepare_data(closes)
        if self.model is None:
            self.build_model((X.shape[1], 1))
        self.model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=verbose)
        return self

    def predict_next(self, closes):
        _, _, scaled = self.prepare_data(closes)
        current_sequence = scaled[-self.look_back:].flatten()
        lstm_input = np.reshape(current_sequence, (1, self.look_back, 1))
        prediction = self.model.predict(lstm_input, verbose=0)
        return self.scaler.inverse_transform(prediction)[0, 0]
