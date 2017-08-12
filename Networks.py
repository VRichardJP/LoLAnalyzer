# Implement a lot of different networks

from abc import ABC, abstractmethod
import keras as krs


class BaseModel(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def __repr__(self):
        pass


class DenseUniform(BaseModel):
    def __init__(self, n_layers, NN):
        super().__init__()
        self.n_layers = n_layers
        self.NN = NN

    def __repr__(self):
        # used to name model folder
        return 'DenseUniform_{}_{}'.format(self.n_layers, self.NN)
