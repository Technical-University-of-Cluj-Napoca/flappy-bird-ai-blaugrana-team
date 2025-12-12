import pygame, sys, random, copy

# --- TODO: Import AI classes ---
from neural_net import NeuralNetwork
from genetic_alg import EvolutionManager

class Bird:
    def __init__(self, sound_dict):
        self.flap_sound = sound_dict['flap']
        self.frame_index = 0
        self.frames = []
        self.image = None
        self.movement = 0
        self.gravity = 0.25
        self.set_skin('yellow')
        self.rect = self.image.get_rect(center = (100, 512))
        self.ANIMATION_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.ANIMATION_EVENT, 200)

        # --- AI ATTRIBUTES ---
        self.brain = NeuralNetwork()
        self.fitness = 0
        self.alive = True

    def __deepcopy__(self, memo):
        """
        Custom copy method to handle Pygame objects that can't be deepcopied.
        We share the assets (images/sounds) but copy the logic (brain/stats).
        """
        cls = self.__class__
        new_bird = cls.__new__(cls)
        memo[id(self)] = new_bird
        
        for k, v in self.__dict__.items():
            if k in ['flap_sound', 'frames', 'image', 'downflap', 'midflap', 'upflap']:
                setattr(new_bird, k, v)
            else:
                setattr(new_bird, k, copy.deepcopy(v, memo))
        
        return new_bird

    def set_skin(self, color):
        try:
            down = pygame.image.load(f'assets/{color}bird-downflap.png').convert_alpha()
            mid = pygame.image.load(f'assets/{color}bird-midflap.png').convert_alpha()
            up = pygame.image.load(f'assets/{color}bird-upflap.png').convert_alpha()

            if down.get_width() < 45:
                self.downflap = pygame.transform.scale2x(down)
                self.midflap = pygame.transform.scale2x(mid)
                self.upflap = pygame.transform.scale2x(up)
            else:
                self.downflap = down
                self.midflap = mid
                self.upflap = up

            self.frames = [self.downflap, self.midflap, self.upflap]
            self.image = self.frames[self.frame_index]
        except FileNotFoundError:
            print(f"Error: Could not find images for {color} skin.")

    def jump(self):
        self.movement = 0
        self.movement -= 8
        self.flap_sound.play()

    def think(self, pipes):
        # 1. Find the closest pipe
        # If there are no pipes at all (game start), we can't target anything.
        if len(pipes) == 0:
             # Just flap occasionally to stay alive (simple heuristic for empty screen)
             if self.rect.bottom > 600:
                 self.jump()
             return

        # Find the first pipe that is to the right of the bird
        closest_pipe = None
        for pipe in pipes:
            # pipe.right > self.rect.left means we haven't passed it yet
            if pipe.right > self.rect.left:
                closest_pipe = pipe
                break
        
        # If we somehow passed all pipes or none are valid, target the first one in the list
        if not closest_pipe:
            closest_pipe = pipes[0]

        # 2. Calculate Inputs
        # Determine the Y position of the gap center
        if closest_pipe.bottom < 600:
            gap_center_y = closest_pipe.bottom + 150
        else:
            gap_center_y = closest_pipe.top - 150

        # Input 0: Vertical distance to the Gap (Normalized)
        # We want the bird to aim for the center of the gap.
        # If input is negative, bird is above gap. Positive, below gap.
        input_y_diff = (self.rect.centery - gap_center_y) / 500
        
        # Input 1: Horizontal distance to pipe (Normalized)
        # Even if it's 600px away, we shrink it to 0-1 range so the brain can read it.
        input_x_dist = (closest_pipe.left - self.rect.right) / 500
        
        # Input 2: Velocity (Helpful to know if we are falling fast)
        input_velocity = self.movement / 10

        # Input 3: Bias
        inputs = [input_y_diff, input_x_dist, input_velocity, 1]

        # 3. Ask the brain
        output = self.brain.predict(inputs)
        
        # 4. Jump if output > 0.5
        if output > 0.5:
            self.jump()

    def move(self):
        self.movement += self.gravity
        self.rect.centery += self.movement

    def animate(self):
        self.frame_index = (self.frame_index + 1) % 3
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center = (100, self.rect.centery))

    def draw(self, screen):
        rotated_bird = pygame.transform.rotozoom(self.image, -self.movement * 3, 1)
        screen.blit(rotated_bird, self.rect)

    def reset(self):
        self.rect.center = (100, 512)
        self.movement = 0
        self.fitness = 0

class PipeManager:
    def __init__(self):
        self.surface = pygame.image.load('assets/pipe-green.png')
        self.surface = pygame.transform.scale2x(self.surface)
        self.heights = [400, 600, 800]
        self.pipes = []
        self.SPAWN_EVENT = pygame.USEREVENT
        self.spawn_time = 900 
        pygame.time.set_timer(self.SPAWN_EVENT, self.spawn_time)

        self.create_pipe()

    def create_pipe(self):
        random_pos = random.choice(self.heights)
        bottom_pipe = self.surface.get_rect(midtop = (700, random_pos))
        top_pipe = self.surface.get_rect(midbottom = (700, random_pos - 300))
        self.pipes.extend([bottom_pipe, top_pipe])

    def move_pipes(self):
        for pipe in self.pipes:
            pipe.centerx -= 5
        self.pipes = [pipe for pipe in self.pipes if pipe.centerx > -100]

    def draw(self, screen):
        for pipe in self.pipes:
            if pipe.bottom >= 1024:
                screen.blit(self.surface, pipe)
            else:
                flip_pipe = pygame.transform.flip(self.surface, False, True)
                screen.blit(flip_pipe, pipe)

    def update_difficulty(self, score):
        if score > 30:
            new_time = random.choice([800, 900, 1100])
            if new_time != self.spawn_time:
                self.spawn_time = new_time
                pygame.time.set_timer(self.SPAWN_EVENT, self.spawn_time)

    def reset(self):
        self.pipes.clear()
        self.spawn_time = 900
        pygame.time.set_timer(self.SPAWN_EVENT, self.spawn_time)

class Base:
    def __init__(self):
        self.surface = pygame.image.load('assets/base.png').convert()
        self.surface = pygame.transform.scale2x(self.surface)
        self.x_pos = 0

    def move(self):
        self.x_pos -= 1
        if self.x_pos <= -576:
            self.x_pos = 0

    def draw(self, screen):
        screen.blit(self.surface, (self.x_pos, 900))
        screen.blit(self.surface, (self.x_pos + 576, 900))

class Game:
    def __init__(self):
        pygame.mixer.pre_init(frequency=44100, size=16, channels=1, buffer=512)
        pygame.init()
        self.screen = pygame.display.set_mode((576, 1024))
        self.clock = pygame.time.Clock()
        self.game_font = pygame.font.Font('04B_19.ttf', 40)
        self.menu_font = pygame.font.Font('04B_19.ttf', 30)

        self.sounds = {
            'flap': pygame.mixer.Sound('sound/sfx_wing.wav'),
            'death': pygame.mixer.Sound('sound/sfx_hit.wav'),
            'score': pygame.mixer.Sound('sound/sfx_point.wav')
        }

        self.bg_day = pygame.transform.scale2x(pygame.image.load('assets/background-day.png').convert())
        self.bg_night = pygame.transform.scale2x(pygame.image.load('assets/background-night.png').convert())
        self.current_bg = self.bg_day

        try:
            self.game_over_surface = pygame.transform.scale2x(pygame.image.load('assets/gameover.png').convert_alpha())
        except FileNotFoundError:
            # Fallback if you don't have gameover.png, keep using message or print error
            print("Error: gameover.png not found. Please ensure it is in the assets folder.")
            self.game_over_surface = pygame.transform.scale2x(pygame.image.load('assets/message.png').convert_alpha())
        self.game_over_rect = self.game_over_surface.get_rect(center = (288, 512))

        # --- UPDATE 1: Load Get Ready Image ---
        try:
            self.get_ready_surface = pygame.transform.scale2x(pygame.image.load('assets/message.png').convert_alpha())
        except FileNotFoundError:
            self.get_ready_surface = None
        
        if self.get_ready_surface:
            self.get_ready_rect = self.get_ready_surface.get_rect(center = (288, 512))
        
        self.medals = {}
        try:
            self.medals['bronze'] = pygame.image.load('assets/medal_bronze.png').convert_alpha()
            self.medals['silver'] = pygame.image.load('assets/medal_silver.png').convert_alpha()
            self.medals['gold'] = pygame.image.load('assets/medal_gold.png').convert_alpha()
            self.medals['platinum'] = pygame.image.load('assets/medal_platinum.png').convert_alpha()
        except FileNotFoundError:
            pass

        self.btn_manual_rect = pygame.Rect(138, 400, 300, 60)
        self.btn_auto_rect = pygame.Rect(138, 500, 300, 60)
        self.arrow_left_rect = pygame.Rect(180, 620, 50, 50)
        self.arrow_right_rect = pygame.Rect(346, 620, 50, 50)

        self.btn_pause_rect = pygame.Rect(20, 20, 50, 50)
        self.btn_resume_rect = pygame.Rect(138, 400, 300, 60)
        self.btn_menu_rect = pygame.Rect(138, 500, 300, 60)

        self.bird = Bird(self.sounds)
        self.pipe_manager = PipeManager()
        self.base = Base()

        self.state = 'menu'
        self.mode = 'manual'
        self.paused = False
        self.score = 0
        self.high_score = 0
        
        self.available_skins = ['yellow', 'blue', 'red', 'ghost']
        self.current_skin_index = 0

        self.evolution = EvolutionManager(population_size=150) 
        self.birds = [] 
        for _ in range(self.evolution.population_size):
            self.birds.append(Bird(self.sounds))

    def check_collision(self):
        if self.mode == 'manual':
            for pipe in self.pipe_manager.pipes:
                if self.bird.rect.colliderect(pipe):
                    self.sounds['death'].play()
                    return True
            if self.bird.rect.top <= -100 or self.bird.rect.bottom >= 900:
                return True
            return False
        elif self.mode == 'auto':
            any_alive = False
            for bird in self.birds:
                if bird.alive:
                    # Check collision with pipes
                    for pipe in self.pipe_manager.pipes:
                        if bird.rect.colliderect(pipe):
                            bird.alive = False
                            break # Stop checking pipes for this bird
                    
                    # Check collision with ground/ceiling
                    if bird.rect.top <= -100 or bird.rect.bottom >= 900:
                        bird.alive = False
                    
                    if bird.alive:
                        any_alive = True
        return not any_alive

    def check_score(self):
        # Check every pipe to see if it just passed the bird position
        for pipe in self.pipe_manager.pipes:
            if pipe.centerx == 100:
                # Increment score (0.5 for top pipe, 0.5 for bottom = 1 point total)
                self.score += 0.5
                
                # Check if we completed a full point (passed a pair of pipes)
                if int(self.score) == self.score:
                    self.update_background()
                    self.pipe_manager.update_difficulty(self.score)
                    
                    # Play sound only in manual mode (to avoid annoyance)
                    if self.mode == 'manual':
                        self.sounds['score'].play()
                    
                    # --- AI REWARD SYSTEM ---
                    # If we are in auto mode, give a huge fitness boost to survivors.
                    # This tells the AI: "Passing a pipe is MUCH better than just staying alive."
                    if self.mode == 'auto':
                        for bird in self.birds:
                            if bird.alive:
                                bird.fitness += 5  # Bonus reward!

    def update_background(self):
        if self.available_skins[self.current_skin_index] == 'ghost':
            self.current_bg = self.bg_night
            return 
        period = int(self.score) // 10
        self.current_bg = self.bg_day if period % 2 == 0 else self.bg_night

    def display_score(self):
        if self.state == 'playing':
            score_surf = self.game_font.render(str(int(self.score)), True, (255, 255, 255))
            score_rect = score_surf.get_rect(center = (288, 100))
            self.screen.blit(score_surf, score_rect)
        elif self.state == 'game_over':
            score_surf = self.game_font.render(f'Score: {int(self.score)}', True, (255, 255, 255))
            score_rect = score_surf.get_rect(center = (288, 100))
            self.screen.blit(score_surf, score_rect)

            high_score_surf = self.game_font.render(f'High score: {int(self.high_score)}', True, (255, 255, 255))
            high_score_rect = high_score_surf.get_rect(center = (288, 850))
            self.screen.blit(high_score_surf, high_score_rect)
            
            self.draw_medal()

    def draw_medal(self):
        medal_img = None
        if self.score >= 40: medal_img = self.medals.get('platinum')
        elif self.score >= 30: medal_img = self.medals.get('gold')
        elif self.score >= 20: medal_img = self.medals.get('silver')
        elif self.score >= 10: medal_img = self.medals.get('bronze')
        
        if medal_img:
            medal_rect = medal_img.get_rect(center = (175, 512)) 
            self.screen.blit(medal_img, medal_rect)

    def draw_arrow(self, direction, rect):
        color = (255, 255, 255)
        width = 6
        points = [(rect.right-10, rect.top+5), (rect.left+10, rect.centery), (rect.right-10, rect.bottom-5)] if direction == 'left' else [(rect.left+10, rect.top+5), (rect.right-10, rect.centery), (rect.left+10, rect.bottom-5)]
        pygame.draw.lines(self.screen, color, False, points, width)

    def draw_menu(self):
        title_surf = self.game_font.render("FLAPPY BIRD AI", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(288, 200))
        self.screen.blit(title_surf, title_rect)

        pygame.draw.rect(self.screen, (244, 158, 66), self.btn_manual_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), self.btn_manual_rect, 4, border_radius=12)
        manual_text = self.menu_font.render(f"Manual Mode (M)", True, (255, 255, 255)) # Added (M) hint
        self.screen.blit(manual_text, manual_text.get_rect(center=self.btn_manual_rect.center))

        pygame.draw.rect(self.screen, (66, 173, 244), self.btn_auto_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), self.btn_auto_rect, 4, border_radius=12)
        auto_text = self.menu_font.render(f"Auto Mode (A)", True, (255, 255, 255)) # Added (A) hint
        self.screen.blit(auto_text, auto_text.get_rect(center=self.btn_auto_rect.center))
        
        self.draw_arrow('left', self.arrow_left_rect)
        self.draw_arrow('right', self.arrow_right_rect)

        current_color_name = self.available_skins[self.current_skin_index]
        skin_text = self.menu_font.render(current_color_name.upper(), True, (255, 255, 255))
        self.screen.blit(skin_text, skin_text.get_rect(center=(288, 600)))

        self.screen.blit(self.bird.image, self.bird.image.get_rect(center=(288, 650)))

    def draw_pause_menu(self):
        s = pygame.Surface((576, 1024))
        s.set_alpha(128)
        s.fill((0,0,0))
        self.screen.blit(s, (0,0))
        
        pygame.draw.rect(self.screen, (244, 158, 66), self.btn_resume_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), self.btn_resume_rect, 4, border_radius=12)
        resume_text = self.menu_font.render("Resume (P)", True, (255, 255, 255))
        self.screen.blit(resume_text, resume_text.get_rect(center=self.btn_resume_rect.center))

        pygame.draw.rect(self.screen, (200, 60, 60), self.btn_menu_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), self.btn_menu_rect, 4, border_radius=12)
        menu_text = self.menu_font.render("Main Menu", True, (255, 255, 255))
        self.screen.blit(menu_text, menu_text.get_rect(center=self.btn_menu_rect.center))

    def change_skin(self, direction):
        if direction == 'next':
            self.current_skin_index = (self.current_skin_index + 1) % len(self.available_skins)
        else:
            self.current_skin_index = (self.current_skin_index - 1) % len(self.available_skins)
        
        # Update Manual Bird
        self.bird.set_skin(self.available_skins[self.current_skin_index])
        
        # --- NEW: Update All AI Birds ---
        for bird in self.birds:
            bird.set_skin(self.available_skins[self.current_skin_index])
            
        if self.available_skins[self.current_skin_index] == 'ghost':
            self.current_bg = self.bg_night
        else:
            self.current_bg = self.bg_day

    def reset_game(self):
        self.paused = False
        self.pipe_manager.reset()
        self.score = 0
        
        if self.mode == 'manual':
            self.bird.reset()
            self.state = 'get_ready'
        # --- AUTO RESET LOGIC ---
        elif self.mode == 'auto':
            if len(self.birds) > 0:
                self.birds = self.evolution.create_next_generation(self.birds)
            
            # Reset physics AND apply current skin to new generation
            current_skin = self.available_skins[self.current_skin_index]
            for bird in self.birds:
                bird.reset()
                bird.alive = True
                bird.set_skin(current_skin) # Ensure new birds have the right look
            
            # --- CHANGED: Go to Get Ready instead of Playing ---
            self.state = 'get_ready'

        if self.available_skins[self.current_skin_index] == 'ghost':
            self.current_bg = self.bg_night
        else:
            self.current_bg = self.bg_day

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # --- GLOBAL KEYBOARD SHORTCUTS ---
                if event.type == pygame.KEYDOWN:
                    # 'M' -> Switch to Manual Mode & Restart
                    if event.key == pygame.K_m:
                        self.mode = 'manual'
                        self.reset_game()
                    
                    # 'A' -> Switch to Auto Mode & Restart
                    if event.key == pygame.K_a:
                        self.mode = 'auto'
                        self.reset_game()

                    # 'P' or 'ESC' -> Toggle Pause (Only if playing)
                    if (event.key == pygame.K_p or event.key == pygame.K_ESCAPE) and self.state == 'playing':
                        self.paused = not self.paused

                # --- MOUSE EVENTS ---
                if self.state == 'menu':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_manual_rect.collidepoint(event.pos):
                            self.mode = 'manual'
                            self.reset_game()
                        elif self.btn_auto_rect.collidepoint(event.pos):
                            self.mode = 'auto'
                            self.reset_game()
                        elif self.arrow_left_rect.collidepoint(event.pos):
                            self.change_skin('prev')
                        elif self.arrow_right_rect.collidepoint(event.pos):
                            self.change_skin('next')

                elif self.state == 'get_ready':
                    if event.type == self.bird.ANIMATION_EVENT:
                        self.bird.animate()

                    # Start game on Space or Click
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.state = 'playing'
                            self.bird.jump()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.state = 'playing'
                        self.bird.jump()

                elif self.state == 'playing':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE and self.mode == 'manual' and not self.paused:
                            self.bird.jump()

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_pause_rect.collidepoint(event.pos):
                            self.paused = not self.paused
                        if self.paused:
                            if self.btn_resume_rect.collidepoint(event.pos):
                                self.paused = False
                            elif self.btn_menu_rect.collidepoint(event.pos):
                                self.state = 'menu'
                                if self.available_skins[self.current_skin_index] == 'ghost':
                                    self.current_bg = self.bg_night
                                else:
                                    self.current_bg = self.bg_day

                    if not self.paused:
                        if event.type == self.pipe_manager.SPAWN_EVENT:
                            self.pipe_manager.create_pipe()
                        if event.type == self.bird.ANIMATION_EVENT:
                            if self.mode == 'manual':
                                self.bird.animate()

                elif self.state == 'game_over':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            # --- NEW: Decide where to go based on mode ---
                            if self.mode == 'manual':
                                self.state = 'menu'
                            elif self.mode == 'auto':
                                # In auto, Space triggers the next generation immediately
                                self.reset_game()
                                
                            # Reset Background logic (Keep existing...)
                            if self.available_skins[self.current_skin_index] == 'ghost':
                                self.current_bg = self.bg_night
                            else:
                                self.current_bg = self.bg_day

            # --- DRAWING ---
            self.screen.blit(self.current_bg, (0, 0))

            if self.state == 'menu':
                self.draw_menu()
                self.base.move()

            elif self.state == 'get_ready':
                self.pipe_manager.draw(self.screen)
                self.base.draw(self.screen)
                
                # --- NEW: Draw Logic based on Mode ---
                if self.mode == 'manual':
                    self.bird.draw(self.screen)
                elif self.mode == 'auto':
                    # Draw all alive birds (they are all stacked at start)
                    for bird in self.birds:
                        if bird.alive:
                            bird.draw(self.screen)

                if self.get_ready_surface:
                    self.screen.blit(self.get_ready_surface, self.get_ready_rect)
                
                self.display_score()

            elif self.state == 'playing':
                self.pipe_manager.draw(self.screen)
                self.base.draw(self.screen)

                if not self.paused:
                    self.pipe_manager.move_pipes()
                    self.base.move()
                    self.check_score()
                    if self.mode == 'manual':
                        self.bird.move()
                        self.bird.draw(self.screen)
                        if self.check_collision():
                            self.state = 'game_over'
                    elif self.mode == 'auto':
                        # 1. Update Fitness & Think
                        for bird in self.birds:
                            if bird.alive:
                                bird.fitness += 1 # Reward for surviving another frame
                                bird.think(self.pipe_manager.pipes)
                                bird.move()
                                bird.draw(self.screen)
                        
                        # 2. Check collisions for everyone
                        if self.check_collision(): # Returns True if ALL died
                             self.state = 'game_over'
                             # Auto-restart immediately for training speed? 
                             # Or wait for user? usually auto-restart:
                             #self.reset_game()
                if self.paused:
                    if self.mode == 'manual': self.bird.draw(self.screen)
                    self.draw_pause_menu()
                else:
                    # Draw small II button
                    pygame.draw.rect(self.screen, (255, 255, 255), self.btn_pause_rect, 2, border_radius=5)
                    pygame.draw.line(self.screen, (255,255,255), (35, 30), (35, 60), 4)
                    pygame.draw.line(self.screen, (255,255,255), (55, 30), (55, 60), 4)

                self.display_score()

            elif self.state == 'game_over':
                if self.mode == 'manual': 
                    self.bird.draw(self.screen)
                elif self.mode == 'auto':
                    # Draw the dead birds so you see where they failed
                    for bird in self.birds:
                         bird.draw(self.screen)
                        
                self.pipe_manager.draw(self.screen)
                self.base.draw(self.screen)
                self.screen.blit(self.game_over_surface, self.game_over_rect)
                if self.score > self.high_score:
                    self.high_score = self.score
                self.display_score()

            self.base.draw(self.screen)
            pygame.display.update()
            self.clock.tick(120)

if __name__ == "__main__":
    game = Game()
    game.run()