import random
import math

class NeuralNetwork:
    def __init__(self):
        self.weights = [random.uniform(-1, 1) for _ in range(4)]

    def sigmoid(self, x):
        try:
            return 1 / (1 + math.exp(-x))
        except OverflowError:
            return 0 if x < 0 else 1

    def predict(self, inputs):
        if len(inputs) != 4:
            raise ValueError("Neural Network expects exactly 4 inputs (3 sensors + 1 bias)")
        
        weighted_sum = sum(i * w for i, w in zip(inputs, self.weights))
        
        output = self.sigmoid(weighted_sum)
        
        return output

    def mutate(self):
        mutation_rate = 0.1 
        for i in range(len(self.weights)):
            if random.random() < mutation_rate:
                self.weights[i] += random.uniform(-0.5, 0.5)
                
                self.weights[i] = max(-1, min(1, self.weights[i]))