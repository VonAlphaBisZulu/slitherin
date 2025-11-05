from tensorflow.keras.optimizers import RMSprop
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, Conv2D, Flatten, Dense


class DDQNModel:
    """
    Deep Q-Network model for reinforcement learning.

    Fixed for Keras 3.x: Uses Input layer instead of input_shape parameter.
    """

    def __init__(self, input_shape, action_space):
        self.model = Sequential([
            # Use Input layer as first layer (Keras 3.x best practice)
            Input(shape=input_shape),

            Conv2D(16,
                   3,
                   strides=(1, 1),
                   padding="valid",
                   activation="relu",
                   data_format="channels_first"),

            Conv2D(32,
                   3,
                   strides=(1, 1),
                   padding="valid",
                   activation="relu",
                   data_format="channels_first"),

            Flatten(),
            Dense(256, activation="relu"),
            Dense(action_space)
        ])

        self.model.compile(RMSprop(), "MSE", metrics=["accuracy"])


