import random
import copy
# Ensure this import works in your project structure
from neural_net import NeuralNetwork 

class EvolutionManager:
    """
    Handles the population size, fitness calculation, and next generation.
    Refer to PDF Section: 'The Natural Selection Process' [cite: 191]
    """
    def __init__(self, population_size):
        self.population_size = population_size
        self.generation_count = 1
        self.species_list = {} # Dictionary to hold {species_id: [birds]}
        # Threshold variable for Speciation [cite: 227]
        self.compatibility_threshold = 0.5 

    def speciation(self, birds):
        """
        Groups birds into species based on weight similarity.
        PDF Formula: Sum(|Wa - Wb|) 
        """
        # Clear previous species
        self.species_list = {}
        
        for bird in birds:
            placed = False
            for species_id, species_birds in self.species_list.items():
                # Compare with the first bird (representative) of the species
                representative = species_birds[0]
                distance = self.get_weight_difference(bird.brain, representative.brain)
                
                if distance < self.compatibility_threshold:
                    self.species_list[species_id].append(bird)
                    placed = True
                    break
            
            if not placed:
                # Create a new species
                new_id = len(self.species_list)
                self.species_list[new_id] = [bird]

    def get_weight_difference(self, brain_a, brain_b):
        """
        Helper to calculate the difference formula 
        """
        diff = 0
        for wa, wb in zip(brain_a.weights, brain_b.weights):
            diff += abs(wa - wb)
        return diff

    def calculate_fitness(self, birds):
        """
        Updates the fitness scores.
        """
        # First, ensure birds are grouped
        self.speciation(birds)

        # Calculate 'Species Fitness' (Average fitness of all birds in a species) [cite: 246]
        for species_id, species_birds in self.species_list.items():
            total_fitness = sum(b.fitness for b in species_birds)
            avg_fitness = total_fitness / len(species_birds)
            
            # Assign this average to the species (or use it for selection probability)
            for bird in species_birds:
                bird.species_fitness = avg_fitness

    def create_next_generation(self, dead_birds):
        """
        Logic to create the new population after all birds die.
        """
        self.calculate_fitness(dead_birds)
        new_birds = []

        # 1. SORTING
        # Sort species by their fitness (Strongest species first) [cite: 251]
        # We sort the dictionary keys based on the species_fitness of their first bird
        sorted_species = sorted(
            self.species_list.values(), 
            key=lambda birds: birds[0].species_fitness, 
            reverse=True
        )

        # 2. CHAMPION SELECTION
        for species_birds in sorted_species:
            # Sort birds within each species by their individual fitness [cite: 251]
            species_birds.sort(key=lambda b: b.fitness, reverse=True)
            
            # Identify the best bird (Champion) from each species
            champion = species_birds[0]
            
            # Clone the Champion exactly (without mutation) [cite: 258]
            # We need a deep copy to ensure it's a new object
            champion_clone = copy.deepcopy(champion)
            champion_clone.reset() # Ensure score/movement is reset
            new_birds.append(champion_clone)

        # 3. REPRODUCTION & MUTATION
        # Fill the rest of the population
        while len(new_birds) < self.population_size:
            # Select a random species (weighted by fitness ideally, but simple random for now)
            # or simply pick from the top species
            if not sorted_species:
                break
                
            species = random.choice(sorted_species[:3]) # Pick from top 3 species
            parent = random.choice(species) # Pick a random parent from that species
            
            # Clone and mutate [cite: 260]
            child = copy.deepcopy(parent)
            child.reset()
            child.brain.mutate()
            new_birds.append(child)

        self.generation_count += 1
        return new_birds