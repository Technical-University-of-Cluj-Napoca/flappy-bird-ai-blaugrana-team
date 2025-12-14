import random
import copy
from neural_net import NeuralNetwork 

class EvolutionManager:
    """
    Handles the population size, fitness calculation, and next generation.
    Refer to PDF Section: 'The Natural Selection Process'
    """
    def __init__(self, population_size):
        self.population_size = population_size
        self.generation_count = 1
        self.species_list = {} # Dictionary to hold {species_id: [birds]}
        self.compatibility_threshold = 0.5 

    def speciation(self, birds):
        """
        Groups birds into species based on weight similarity.
        [cite_start]PDF Formula: Sum(|Wa - Wb|) [cite: 220]
        """
        self.species_list = {}
        
        for bird in birds:
            placed = False
            for species_id, species_birds in self.species_list.items():
                representative = species_birds[0]
                distance = self.get_weight_difference(bird.brain, representative.brain)
                
                if distance < self.compatibility_threshold:
                    self.species_list[species_id].append(bird)
                    placed = True
                    break
            
            if not placed:
                new_id = len(self.species_list)
                self.species_list[new_id] = [bird]

    def get_weight_difference(self, brain_a, brain_b):
        diff = 0
        for wa, wb in zip(brain_a.weights, brain_b.weights):
            diff += abs(wa - wb)
        return diff

    def calculate_fitness(self, birds):
        """
        [cite_start]Updates the fitness scores. [cite: 246]
        """
        self.speciation(birds)

        for species_id, species_birds in self.species_list.items():
            total_fitness = sum(b.fitness for b in species_birds)
            avg_fitness = total_fitness / len(species_birds)
            
            for bird in species_birds:
                bird.species_fitness = avg_fitness

    def create_next_generation(self, dead_birds):
        """
        Logic to create the new population after all birds die.
        """
        self.calculate_fitness(dead_birds)
        new_birds = []

        # [cite_start]1. SORTING [cite: 250]
        sorted_species = sorted(
            self.species_list.values(), 
            key=lambda birds: birds[0].species_fitness, 
            reverse=True
        )

        # [cite_start]2. CHAMPION SELECTION [cite: 258]
        for species_birds in sorted_species:
            species_birds.sort(key=lambda b: b.fitness, reverse=True)
            champion = species_birds[0]
            
            # Clone Champion (Deep copy required)
            champion_clone = copy.deepcopy(champion)
            champion_clone.reset()
            new_birds.append(champion_clone)

        # [cite_start]3. REPRODUCTION & MUTATION [cite: 260]
        while len(new_birds) < self.population_size:
            if not sorted_species:
                break
                
            # Pick random species from top 3
            species = random.choice(sorted_species[:3]) 
            parent = random.choice(species)
            
            child = copy.deepcopy(parent)
            child.reset()
            child.brain.mutate()
            new_birds.append(child)

        self.generation_count += 1
        return new_birds