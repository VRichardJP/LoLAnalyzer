#!python
# Implement a lot of different networks

from abc import ABC, abstractmethod


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


# Training/Testing accuracy:
# games=145358, options=(BR_Mode, 1, 256, 0.3): 0.5458/0.5321
# games=145358, options=(BR_Mode, 2, 128, 0.2): 0.5427/0.5330
# games=145358, options=(BR_Mode, 2, 256, 0.3): 0.5420/0.5332
# games=145358, options=(BR_Mode, 2, 512, 0.5): 0.5405/0.5312
# games=145358, options=(BR_Mode, 3, 128, 0.2): 0.5407/0.5336
# games=145358, options=(BR_Mode, 3, 256, 0.3): 0.5426/0.5333
# games=145358, options=(BR_Mode, 4, 256, 0.3): 0.5410/0.5323
# games=145358, options=(BR_Mode, 5, 128, 0.3): 0.5354/0.5319
# games=148883, options=(ABOTJMCS_Mode, 3, 512, 0.2): 0.5283/0.5265
# games=148883, options=(ABOTJMCS_Mode, 3, 1024, 0.3): 0.5274/0.5257
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
        import keras  # keras is heavy, we charge the module only when necessary

        self.model = keras.models.Sequential()
        self.model.add(keras.layers.Dense(units=self.NN, input_dim=self.mode.INPUT_SIZE, activation='relu'))
        self.model.add(keras.layers.Dropout(self.dropout))
        for _ in range(self.n_hidden_layers):  # hidden layers
            self.model.add(keras.layers.Dense(units=self.NN, activation='relu'))
            self.model.add(keras.layers.Dropout(self.dropout))
        self.model.add(keras.layers.Dense(units=1, activation='sigmoid'))  # reading output
        self.model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

    def __repr__(self):
        return 'DenseUniform(*{!r})'.format(self.mode, self.n_hidden_layers, self.NN)

    def __str__(self):
        # used to name model folder
        return '{!s}_DenseUniform_{}_{}'.format(self.mode, self.n_hidden_layers, self.NN)


# Training/Testing accuracy:
# games=145358, options=(BR_Mode, 3, 256, 0.3): 0.5371/0.5327
# games=145358, options=(BR_Mode, 3, 512, 0.3): 0.5319/0.5317
# games=148883 , options=(ABOTJMCS_Mode, 4, 512, 0.0): 0.5302/0.5272
# games=148883, options=(ABOTJMCS_Mode, 3, 512, 0.2): 0.5274/0.5297
# games=148883, options=(ABOTJMCS_Mode, 3, 1024, 0.3): 0.5274/0.5257
# games=148883, options=(ABOTJMCS_Mode, 3, 1024, 0.1): 0.5313/0.5262
class DenseDegressive(BaseModel):
    def __init__(self, mode, n_hidden_layers, NN, dropout, batch_size=1000, report=10):
        super().__init__(mode)
        self.n_hidden_layers = n_hidden_layers
        self.NN = NN
        self.dropout = dropout
        self.model = None
        self.batch_size = batch_size  # The higher the better, but need more gpu memory
        self.report = report  # In order to not be overflowed by training/testing logs

    def build(self):
        import keras

        self.model = keras.models.Sequential()
        self.model.add(keras.layers.Dense(units=self.NN, input_dim=self.mode.INPUT_SIZE, activation='relu'))
        self.model.add(keras.layers.Dropout(self.dropout))
        for k in range(self.n_hidden_layers):  # hidden layers
            units = self.NN // (2**(k+1))
            self.model.add(keras.layers.Dense(units=units, activation='relu'))
            self.model.add(keras.layers.Dropout(self.dropout))
        self.model.add(keras.layers.Dense(units=1, activation='sigmoid'))  # reading output
        self.model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

    def __repr__(self):
        return 'DenseDegressive(*{!r})'.format(self.mode, self.n_hidden_layers, self.NN)

    def __str__(self):
        # used to name model folder
        return '{!s}_DenseDegressive_{}_{}'.format(self.mode, self.n_hidden_layers, self.NN)
