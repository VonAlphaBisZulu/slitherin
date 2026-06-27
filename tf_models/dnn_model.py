import os
import numpy as np

# Migrated from TFLearn to tensorflow.keras for TF 2.x compatibility
try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import Input, Dense, Flatten, Reshape
    from tensorflow.keras.optimizers import Adam
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    print("WARNING: TensorFlow/Keras not available. DNN solver will not work.")

from game.helpers.constants import Constants
from game.helpers.singleton import Singleton

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TF info/warning messages


class DeepNeuralNetModel(metaclass=Singleton):
    """
    Deep Neural Network model using Keras (TF 2.x compatible).

    Migrated from TFLearn to tensorflow.keras.
    Architecture matches original TFLearn implementation.
    """

    def __init__(self, path):
        if not KERAS_AVAILABLE:
            raise ImportError("TensorFlow/Keras is required for DNN model but not installed")

        self.dnn_model_path = path
        self.dnn_model_file_name = self.dnn_model_path + Constants.MODEL_NAME
        self.hidden_node_neurons = Constants.MODEL_FEATURE_COUNT ** 3

        # Build model architecture (matches TFLearn version)
        # Input: [None, MODEL_FEATURE_COUNT, 1]
        # Hidden: fully_connected(125 neurons, relu6)
        # Output: fully_connected(1 neuron, linear)

        inputs = Input(shape=(Constants.MODEL_FEATURE_COUNT, 1))
        x = Flatten()(inputs)  # Flatten for Dense layers
        self.hidden_layer = Dense(self.hidden_node_neurons, activation='relu')(x)
        outputs = Dense(1, activation='linear')(self.hidden_layer)

        self.model = Model(inputs=inputs, outputs=outputs)
        self.model.compile(
            optimizer=Adam(),
            loss='mean_squared_error'
        )

        # Try to load existing model if it exists
        h5_path = self.dnn_model_file_name.replace('.tf', '.h5')
        if os.path.isfile(h5_path):
            try:
                self.model.load_weights(h5_path)
            except Exception as e:
                print(f"Could not load model weights from {h5_path}: {e}")

    def save(self):
        """Save model weights"""
        h5_path = self.dnn_model_file_name.replace('.tf', '.h5')
        self.model.save_weights(h5_path)

    def get_weights(self):
        """Get weights from hidden layer"""
        # Get the first Dense layer's weights (hidden layer)
        return self.model.layers[2].get_weights()[0]  # Layer 2 is the hidden Dense layer

    def set_weights(self, weights):
        """Set weights for hidden layer"""
        # Set the first Dense layer's weights
        current_weights = self.model.layers[2].get_weights()
        current_weights[0] = weights
        self.model.layers[2].set_weights(current_weights)
