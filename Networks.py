# Implement a lot of different networks

from abc import ABC, abstractmethod
import keras as krs


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


class DenseUniform(BaseModel):
    def __init__(self, mode, n_hidden_layers, NN):
        super().__init__(mode)
        self.n_hidden_layers = n_hidden_layers
        self.NN = NN
        self.model = None
        self.batch_size = 200  # The higher the better, but need more gpu memory

    def build(self):
        self.model = krs.models.Sequential()
        self.model.add(krs.layers.Dense(units=self.NN, input_dim=self.mode.INPUT_SIZE, activation='relu'))
        for _ in range(self.n_hidden_layers):  # hidden layers
            self.model.add(krs.layers.Dense(units=self.NN, activation='relu'))
        self.model.add(krs.layers.Dense(units=1, activation='sigmoid'))  # reading output
        self.model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

    def __repr__(self):
        return 'DenseUniform(*{!r})'.format(self.mode, self.n_hidden_layers, self.NN)

    def __str__(self):
        # used to name model folder
        return '{!s}_DenseUniform_{}_{}'.format(self.mode, self.n_hidden_layers, self.NN)
