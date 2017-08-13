# Implement a lot of different networks

from abc import ABC, abstractmethod
import keras


class BaseModel(ABC):
    @abstractmethod
    def __init__(self, mode):
        self.mode = mode

    @abstractmethod
    def build(self):
        pass

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def __str__(self):
        pass


# Testing accuracy with:
# games=145358, options=(BR_Mode, 5, 256, True): 0.6044

class DenseUniform(BaseModel):
    def __init__(self, mode, n_hidden_layers, NN, dropout, batch_size=1000, report=10):
        super().__init__(mode)
        self.n_hidden_layers = n_hidden_layers
        self.NN = NN
        self.dropout = dropout
        self.model = None
        self.batch_size = batch_size  # The higher the better, but need more gpu memory
        self.report = report  # In order to not be overflowed by training/testing logs

    def build(self):
        self.model = keras.models.Sequential()
        self.model.add(keras.layers.Dense(units=self.NN, input_dim=self.mode.INPUT_SIZE, activation='relu'))
        for _ in range(self.n_hidden_layers):  # hidden layers
            self.model.add(keras.layers.Dense(units=self.NN, activation='relu'))
        if self.dropout:
            self.model.add(keras.layers.Dropout(0.4))
        self.model.add(keras.layers.Dense(units=1, activation='sigmoid'))  # reading output
        self.model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

    def __repr__(self):
        return 'DenseUniform(*{!r})'.format(self.mode, self.n_hidden_layers, self.NN)

    def __str__(self):
        # used to name model folder
        return '{!s}_DenseUniform_{}_{}'.format(self.mode, self.n_hidden_layers, self.NN)
