import random
import math

class NeuralNetwork:
    """
    Implements the Single Layer Perceptron.
    [cite_start]Refer to PDF Section: 'The Brain - a single layer perceptron' [cite: 121]
    """
    def __init__(self):
        # [cite_start]TODO: Initialize 4 weights with random values between -1 and 1 [cite: 139]
        # Inputs required: 
        #   1. Vertical distance to top pipe
        #   2. Horizontal distance to next pipe
        #   3. Vertical distance to bottom pipe
        #   4. Bias (always 1)
        self.weights = [] 
        pass

    def sigmoid(self, x):
        """
        Activation function.
        [cite_start]PDF Formula: 1 / (1 + e^-x) [cite: 167]
        """
        # TODO: Implement the Sigmoid function logic here
        return 0

    def predict(self, inputs):
        """
        Decides if the bird should flap.
        """
        # TODO: Check that len(inputs) is exactly 4
        
        # TODO: Calculate the Dot Product
        # [cite_start]Formula: Sum = (i0 * w0) + (i1 * w1) + (i2 * w2) + (i3 * w3) [cite: 157]
        
        # TODO: Pass the Sum through the self.sigmoid() function
        
        # TODO: Return the result (value between 0 and 1)
        return 0

    def mutate(self):
        """
        Used for evolution.
        """
        # TODO: Iterate through self.weights
        # [cite_start]TODO: With a small probability (mutation rate), modify the weight slightly [cite: 260]
        pass