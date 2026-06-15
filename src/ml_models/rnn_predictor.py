import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, SimpleRNN


class RNNPredictor:
    def __init__(self, look_back=60, units=50):
        self.look_back = look_back
        self.units = units
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None

    def build_model(self, input_shape):
        model = Sequential()
        model.add(SimpleRNN(units=self.units, input_shape=input_shape, return_sequences=False))
        model.add(Dense(1, activation='sigmoid'))
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        self.model = model
        return model

    def prepare_data(self, closes):
        scaled = self.scaler.fit_transform(closes.reshape(-1, 1))
        X, y = [], []
        for i in range(len(scaled) - self.look_back):
            X.append(scaled[i:i + self.look_back, 0])
            y.append(1 if scaled[i + self.look_back, 0] > scaled[i + self.look_back - 1, 0] else 0)
        X = np.array(X)
        y = np.array(y)
        X = X.reshape(X.shape[0], X.shape[1], 1)
        return X, y

    def train(self, closes, epochs=10, batch_size=32, verbose=1):
        X, y = self.prepare_data(closes)
        if self.model is None:
            self.build_model((X.shape[1], 1))
        self.model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=verbose)
        return self

    def predict_probability(self, closes):
        scaled = self.scaler.transform(closes.reshape(-1, 1))
        last_sequence = scaled[-self.look_back:].reshape(1, self.look_back, 1)
        prediction = self.model.predict(last_sequence, verbose=0)
        return prediction[0][0]
