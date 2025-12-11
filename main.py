import pygame, sys, random

# --- TODO: Import AI classes ---
# from neural_network import NeuralNetwork
# from genetic_algorithm import EvolutionManager

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
        self.brain = None # TODO: Initialize NeuralNetwork() here
        self.fitness = 0
        self.alive = True

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
        # TODO: AI Logic
        pass

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

        self.game_over_surface = pygame.transform.scale2x(pygame.image.load('assets/message.png').convert_alpha())
        self.game_over_rect = self.game_over_surface.get_rect(center = (288, 512))
        
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

        # --- AI INITIALIZATION ---
        # TODO: Initialize self.evolution = EvolutionManager(population_size=50)
        # TODO: Initialize self.birds = [] 

    def check_collision(self):
        if self.mode == 'manual':
            for pipe in self.pipe_manager.pipes:
                if self.bird.rect.colliderect(pipe):
                    self.sounds['death'].play()
                    return True
            if self.bird.rect.top <= -100 or self.bird.rect.bottom >= 900:
                return True
            return False
        # TODO: Auto Mode Collision
        return False

    def check_score(self):
        if self.mode == 'manual':
            for pipe in self.pipe_manager.pipes:
                if pipe.centerx == 100:
                    self.score += 0.5
                    if int(self.score) == self.score:
                        self.sounds['score'].play()
                        self.update_background()
                        self.pipe_manager.update_difficulty(self.score)
        # TODO: Auto Score

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
        self.bird.set_skin(self.available_skins[self.current_skin_index])
        if self.available_skins[self.current_skin_index] == 'ghost':
            self.current_bg = self.bg_night
        else:
            self.current_bg = self.bg_day

    def reset_game(self):
        self.state = 'playing'
        self.paused = False
        self.pipe_manager.reset()
        self.score = 0
        
        if self.mode == 'manual':
            self.bird.reset()
        # TODO: Auto Reset

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
                            self.state = 'menu'
                            if self.available_skins[self.current_skin_index] == 'ghost':
                                self.current_bg = self.bg_night
                            else:
                                self.current_bg = self.bg_day

            # --- DRAWING ---
            self.screen.blit(self.current_bg, (0, 0))

            if self.state == 'menu':
                self.draw_menu()
                self.base.move()

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
                        pass # TODO Auto Logic

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
                if self.mode == 'manual': self.bird.draw(self.screen)
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