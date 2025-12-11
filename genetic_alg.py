import random
# from neural_network import NeuralNetwork # Uncomment when logic is ready

class EvolutionManager:
    """
    Handles the population size, fitness calculation, and next generation.
    [cite_start]Refer to PDF Section: 'The Natural Selection Process' [cite: 191]
    """
    def __init__(self, population_size):
        self.population_size = population_size
        self.generation_count = 1
        # [cite_start]TODO: Define a threshold variable for Speciation (e.g. 0.5) [cite: 227]

    def speciation(self, birds):
        """
        Groups birds into species based on weight similarity.
        [cite_start]PDF Formula: Sum(|Wa - Wb|) [cite: 220]
        """
        # TODO: Loop through all birds
        # TODO: Compare each bird's weights to a representative of existing species
        # TODO: If difference < threshold, add to species. Else, create new species.
        pass

    def calculate_fitness(self, birds):
        """
        Updates the fitness scores.
        """
        # [cite_start]TODO: Calculate 'Species Fitness' (Average fitness of all birds in a species) [cite: 246]
        pass

    def create_next_generation(self, dead_birds):
        """
        Logic to create the new population after all birds die.
        """
        new_birds = []

        # 1. SORTING
        # [cite_start]TODO: Sort the species by their fitness (Strongest species first) [cite: 251]
        # TODO: Sort birds within each species by their individual fitness

        # 2. CHAMPION SELECTION
        # TODO: Identify the best bird (Champion) from each species
        # [cite_start]TODO: Clone the Champion exactly (without mutation) into new_birds [cite: 258]

        # 3. REPRODUCTION & MUTATION
        # TODO: Fill the rest of the population (up to self.population_size)
        # [cite_start]TODO: Select parents from good species, clone them, call bird.brain.mutate(), and add to new_birds [cite: 260]

        self.generation_count += 1
        return new_birds