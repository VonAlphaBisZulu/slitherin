import os
# NOTE: TFLearn is deprecated and not compatible with TensorFlow 2.x
# This model needs to be migrated to tensorflow.keras
# For now, this will only work if tflearn is installed separately
try:
    import tflearn
    from tflearn.layers.core import input_data, fully_connected
    from tflearn.layers.estimator import regression
    TFLEARN_AVAILABLE = True
except ImportError:
    TFLEARN_AVAILABLE = False
    print("WARNING: TFLearn not available. DNN solver will not work.")
    print("To use DNN solver, install tflearn: pip install tflearn")

from game.helpers.constants import Constants
from game.helpers.singleton import Singleton

# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # Disables TF warnings


class DeepNeuralNetModel(metaclass=Singleton):
    hidden = None
    hidden_node_neurons = Constants.MODEL_FEATURE_COUNT ** 3

    def __init__(self, path):
        if not TFLEARN_AVAILABLE:
            raise ImportError("TFLearn is required for DNN model but not installed")
        self.dnn_model_path = path
        self.dnn_model_file_name = self.dnn_model_path + Constants.MODEL_NAME
        network = input_data(shape=[None, Constants.MODEL_FEATURE_COUNT, 1])
        self.hidden = network = fully_connected(network, self.hidden_node_neurons, activation='relu6')
        network = fully_connected(network, 1, activation='linear')
        network = regression(network, optimizer='adam', loss='mean_square')
        self.model = tflearn.DNN(network)
        # if os.path.isfile(self.dnn_model_file_name+".index"):
        #     self.model.load(self.dnn_model_file_name)

    def save(self):
        self.model.save(self.dnn_model_file_name)

    def get_weights(self):
        return self.model.get_weights(self.hidden.W)

    def set_weights(self, weights):
        self.model.set_weights(self.hidden.W, weights)
