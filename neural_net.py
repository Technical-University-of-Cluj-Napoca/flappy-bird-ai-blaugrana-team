import random
import math

class NeuralNetwork:
    """
    Implements the Single Layer Perceptron.
    Refer to PDF Section: 'The Brain - a single layer perceptron' [cite: 121]
    """
    def __init__(self):
        # Initialize 4 weights with random values between -1 and 1 [cite: 139]
        # Inputs: Vertical Dist (Top), Horiz Dist, Vertical Dist (Bottom), Bias
        self.weights = [random.uniform(-1, 1) for _ in range(4)]

    def sigmoid(self, x):
        """
        Activation function.
        PDF Formula: 1 / (1 + e^-x) 
        """
        try:
            return 1 / (1 + math.exp(-x))
        except OverflowError:
            # Handle overflow for very large negative x
            return 0 if x < 0 else 1

    def predict(self, inputs):
        """
        Decides if the bird should flap.
        """
        if len(inputs) != 4:
            raise ValueError("Neural Network expects exactly 4 inputs (3 sensors + 1 bias)")
        
        # Calculate the Dot Product
        # Formula: Sum = (i0 * w0) + (i1 * w1) + (i2 * w2) + (i3 * w3) [cite: 157]
        weighted_sum = sum(i * w for i, w in zip(inputs, self.weights))
        
        # Pass the Sum through the sigmoid function [cite: 170]
        output = self.sigmoid(weighted_sum)
        
        # Return the result (value between 0 and 1)
        return output

    def mutate(self):
        """
        Used for evolution.
        With a small probability, modify the weight slightly [cite: 260]
        """
        mutation_rate = 0.1 # 10% chance to mutate a specific weight
        for i in range(len(self.weights)):
            if random.random() < mutation_rate:
                # Add a small random value (mutation)
                self.weights[i] += random.uniform(-0.1, 0.1)
                
                # Clamp values to keep them stable (optional but recommended)
                self.weights[i] = max(-1, min(1, self.weights[i]))
