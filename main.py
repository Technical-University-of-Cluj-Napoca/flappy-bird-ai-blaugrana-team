import pygame, sys, random, copy, os

# --- Import AI classes ---
from neural_net import NeuralNetwork
from genetic_alg import EvolutionManager

class ScoreManager:
    def __init__(self, filename="highscores.txt"):
        self.filename = filename
        self.manual_best = 0
        self.auto_best = 0
        self.auto_best_gen = 0
        self.load_scores()

    def load_scores(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if line.strip():
                            parts = line.strip().split(",")
                            try:
                                if len(parts) >= 2:
                                    self.manual_best = int(parts[0])
                                    self.auto_best = int(parts[1])
                                if len(parts) >= 3:
                                    self.auto_best_gen = int(parts[2])
                                break 
                            except ValueError:
                                continue 
            except Exception as e:
                print(f"Warning: Could not load scores ({e}).")
        else:
            self.save_scores()

    def save_scores(self):
        try:
            with open(self.filename, "a") as f:
                f.write(f"\n{self.manual_best},{self.auto_best},{self.auto_best_gen}")
        except Exception as e:
            print(f"Error saving score: {e}")
            
    def update_score(self, score, mode, current_gen=0):
        updated = False
        try:
            score_int = int(score)
            if mode == 'manual' or mode == 'surprise':
                if score_int > self.manual_best:
                    self.manual_best = score_int
                    updated = True
            elif mode == 'auto':
                if score_int > self.auto_best:
                    self.auto_best = score_int
                    self.auto_best_gen = current_gen
                    updated = True
            
            if updated:
                self.save_scores()
        except Exception:
            pass
        return updated

    def reset_scores(self):
        self.manual_best = 0
        self.auto_best = 0
        self.auto_best_gen = 0
        self.save_scores()
        print("Scores reset.")

class Bird:
    def __init__(self, sound_dict):
        self.flap_sound = sound_dict['flap']
        self.frame_index = 0
        self.frames = []
        self.image = None
        self.movement = 0
        self.gravity_val = 0.25
        self.jump_force = -6
        self.set_skin('yellow')
        self.gravity_dir = 1 

        if self.image:
            self.rect = self.image.get_rect(center = (100, 512))
        else:
            self.rect = pygame.Rect(100, 512, 34, 24)

        self.ANIMATION_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.ANIMATION_EVENT, 200)
        self.brain = NeuralNetwork()
        self.fitness = 0
        self.alive = True

    def __deepcopy__(self, memo):
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
            s = pygame.Surface((34, 24)); s.fill((255, 255, 0))
            self.frames = [s, s, s]; self.image = s

    def jump(self):
        self.movement = 0
        self.movement = self.jump_force * self.gravity_dir
        if self.flap_sound: self.flap_sound.play()

    def think(self, pipes):
        if len(pipes) == 0:
             if self.rect.bottom > 600: self.jump()
             return
        closest_pipe = None
        for pipe in pipes:
            if pipe.right > self.rect.left:
                closest_pipe = pipe
                break
        if not closest_pipe: closest_pipe = pipes[0]

        if closest_pipe.bottom < 512:
            gap_center_y = closest_pipe.bottom + 150
        else: 
            gap_center_y = closest_pipe.top - 150

        input_y_diff = (self.rect.centery - gap_center_y) / 500
        input_x_dist = (closest_pipe.left - self.rect.right) / 500
        input_velocity = self.movement / 10
        inputs = [input_y_diff, input_x_dist, input_velocity, 1]
        output = self.brain.predict(inputs)
        
        if output > 0.5:
            if self.gravity_dir == 1 and self.movement > 0: self.jump()
            elif self.gravity_dir == -1 and self.movement < 0: self.jump()

    def move(self):
        self.movement += self.gravity_val * self.gravity_dir
        self.rect.centery += self.movement

    def animate(self):
        self.frame_index = (self.frame_index + 1) % 3
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center = (100, self.rect.centery))

    def draw(self, screen):
        angle = -self.movement * 3 * self.gravity_dir
        img_to_draw = self.image
        if self.gravity_dir == -1:
            img_to_draw = pygame.transform.flip(self.image, False, True)
        rotated_bird = pygame.transform.rotozoom(img_to_draw, angle, 1)
        screen.blit(rotated_bird, self.rect)

    def reset(self):
        self.rect.center = (100, 512)
        self.movement = 0
        self.fitness = 0
        self.gravity_dir = 1
        self.alive = True 

class PipeManager:
    def __init__(self):
        try:
            self.surface = pygame.image.load('assets/pipe-green.png')
            self.surface = pygame.transform.scale2x(self.surface)
        except FileNotFoundError:
            self.surface = pygame.Surface((52, 320)); self.surface.fill((0, 255, 0))
        self.heights = [400, 600, 800]
        self.pipes = []
        self.SPAWN_EVENT = pygame.USEREVENT
        self.spawn_time = 1200 
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
            if pipe.bottom >= 1024: screen.blit(self.surface, pipe)
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
        self.spawn_time = 1200
        pygame.time.set_timer(self.SPAWN_EVENT, self.spawn_time)
        self.create_pipe() 

class Base:
    def __init__(self):
        try:
            self.surface = pygame.image.load('assets/base.png').convert()
            self.surface = pygame.transform.scale2x(self.surface)
        except FileNotFoundError:
            self.surface = pygame.Surface((576, 112)); self.surface.fill((200, 200, 100))
        self.x_pos = 0

    def move(self):
        self.x_pos -= 1
        if self.x_pos <= -576: self.x_pos = 0

    def draw(self, screen):
        screen.blit(self.surface, (self.x_pos, 900))
        screen.blit(self.surface, (self.x_pos + 576, 900))

class Game:
    def __init__(self):
        pygame.mixer.pre_init(frequency=44100, size=16, channels=1, buffer=512)
        pygame.init()
        self.screen = pygame.display.set_mode((576, 1024))
        self.clock = pygame.time.Clock()
        
        try:
            self.game_font = pygame.font.Font('04B_19.ttf', 40)
            self.menu_font = pygame.font.Font('04B_19.ttf', 30)
            self.stat_font = pygame.font.Font('04B_19.ttf', 18)
        except FileNotFoundError:
            self.game_font = pygame.font.SysFont('Arial', 40, bold=True)
            self.menu_font = pygame.font.SysFont('Arial', 30, bold=True)
            self.stat_font = pygame.font.SysFont('Arial', 18, bold=True)

        self.sounds = {}
        sound_files = {'flap': 'sound/sfx_wing.wav', 'death': 'sound/sfx_hit.wav', 'score': 'sound/sfx_point.wav'}
        for name, path in sound_files.items():
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except FileNotFoundError:
                self.sounds[name] = None

        try:
            self.bg_day = pygame.transform.scale2x(pygame.image.load('assets/background-day.png').convert())
        except FileNotFoundError:
            self.bg_day = pygame.Surface((576, 1024)); self.bg_day.fill((135, 206, 235))
            
        try:
            self.bg_night = pygame.transform.scale2x(pygame.image.load('assets/background-night.png').convert())
        except FileNotFoundError:
            self.bg_night = self.bg_day 
            
        self.current_bg = self.bg_day

        try:
            self.game_over_surface = pygame.transform.scale2x(pygame.image.load('assets/gameover.png').convert_alpha())
        except FileNotFoundError:
            self.game_over_surface = self.game_font.render("GAME OVER", True, (255, 100, 100))
        self.game_over_rect = self.game_over_surface.get_rect(center = (288, 380))

        try:
            self.get_ready_surface = pygame.transform.scale2x(pygame.image.load('assets/message.png').convert_alpha())
            self.get_ready_rect = self.get_ready_surface.get_rect(center = (288, 512))
        except FileNotFoundError:
            self.get_ready_surface = None
            self.get_ready_rect = None
        
        self.score_manager = ScoreManager()

        self.medals = {}
        medal_files = {
            'bronze': 'assets/medal_bronze.png', 'silver': 'assets/medal_silver.png',
            'gold': 'assets/medal_gold.png', 'platinum': 'assets/medal_platinum.png'
        }
        for name, path in medal_files.items():
            try:
                self.medals[name] = pygame.image.load(path).convert_alpha()
            except FileNotFoundError:
                pass

        # MENU BUTTONS
        self.btn_manual_rect = pygame.Rect(138, 350, 300, 60) 
        self.btn_auto_rect = pygame.Rect(138, 430, 300, 60) 
        self.btn_surprise_rect = pygame.Rect(138, 510, 300, 60) 
        self.btn_home_rect = pygame.Rect(20, 20, 50, 50)

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
        self.available_skins = ['yellow', 'blue', 'red', 'ghost']
        self.current_skin_index = 0
        self.evolution = EvolutionManager(population_size=150) 
        self.birds = [] 
        for _ in range(self.evolution.population_size):
            self.birds.append(Bird(self.sounds))

    def play_sound(self, name):
        if self.sounds.get(name):
            self.sounds[name].play()

    def check_collision(self):
        target_birds = [self.bird] if (self.mode == 'manual' or self.mode == 'surprise') else self.birds
        any_alive = False
        for bird in target_birds:
            if bird.alive:
                for pipe in self.pipe_manager.pipes:
                    if bird.rect.colliderect(pipe):
                        bird.alive = False
                        if self.mode != 'auto': self.play_sound('death')
                        break
                if bird.rect.top <= -100 or bird.rect.bottom >= 900:
                    bird.alive = False
                    if self.mode != 'auto': self.play_sound('death')
                if bird.alive:
                    any_alive = True

        if not any_alive:
            self.score_manager.update_score(self.score, self.mode, current_gen=self.evolution.generation_count)
            if self.mode == 'auto':
                self.reset_game()
            else:
                self.state = 'game_over'
        return not any_alive

    def check_score(self):
        for pipe in self.pipe_manager.pipes:
            if pipe.centerx == 100:
                self.score += 0.5
                if int(self.score) == self.score:
                    # Update Background (checks ghost skin)
                    self.update_background()
                    
                    self.pipe_manager.update_difficulty(self.score)
                    if self.mode != 'auto':
                        self.play_sound('score')
                    
                    if self.mode == 'surprise' and int(self.score) > 0 and int(self.score) % 5 == 0:
                        self.bird.gravity_dir *= -1
                    
                    if self.mode == 'auto':
                        for bird in self.birds:
                            if bird.alive: bird.fitness += 5 
                        if self.score > self.score_manager.auto_best:
                            self.score_manager.auto_best = int(self.score)
                            self.score_manager.auto_best_gen = self.evolution.generation_count

    def update_background(self):
        # --- GHOST SKIN FORCE NIGHT ---
        if self.available_skins[self.current_skin_index] == 'ghost':
            self.current_bg = self.bg_night
            return 
        
        # Standard Day/Night Cycle
        period = int(self.score) // 10
        if period % 2 == 0:
            self.current_bg = self.bg_day
        else:
            self.current_bg = self.bg_night

    def display_score(self):
        if self.state == 'playing':
            score_surf = self.game_font.render(str(int(self.score)), True, (255, 255, 255))
            score_rect = score_surf.get_rect(center = (288, 100))
            shadow_surf = self.game_font.render(str(int(self.score)), True, (0, 0, 0))
            self.screen.blit(shadow_surf, (score_rect.x + 2, score_rect.y + 2))
            self.screen.blit(score_surf, score_rect)
            
            if self.mode == 'surprise' and self.bird.gravity_dir == -1:
                warn_surf = self.stat_font.render("GRAVITY INVERTED!", True, (255, 50, 50))
                self.screen.blit(warn_surf, (10, 100))

            if self.mode == 'auto':
                self.draw_medal(pos=(50, 100))

        elif self.state == 'game_over':
            self.screen.blit(self.game_over_surface, self.game_over_rect)

            board_x, board_y = 144, 440 
            board_w, board_h = 288, 150
            
            pygame.draw.rect(self.screen, (222, 216, 149), (board_x, board_y, board_w, board_h), border_radius=10)
            pygame.draw.rect(self.screen, (84, 56, 71), (board_x, board_y, board_w, board_h), 4, border_radius=10)

            lbl_score = self.stat_font.render("SCORE", True, (230, 100, 60))
            lbl_best = self.stat_font.render("BEST", True, (230, 100, 60))
            self.screen.blit(lbl_score, (board_x + 160, board_y + 20))
            self.screen.blit(lbl_best, (board_x + 160, board_y + 80))

            score_val = self.menu_font.render(f'{int(self.score)}', True, (255, 255, 255))
            self.screen.blit(score_val, (board_x + 230, board_y + 40))

            if self.mode == 'auto':
                current_best = self.score_manager.auto_best
            else:
                current_best = self.score_manager.manual_best
            
            best_val = self.menu_font.render(f'{current_best}', True, (255, 255, 255))
            self.screen.blit(best_val, (board_x + 230, board_y + 100))
            
            self.draw_medal(pos=(board_x + 60, board_y + 75))

            if self.mode == 'auto' and self.score_manager.auto_best_gen > 0:
                gen_text = f'Best achieved in Gen {self.score_manager.auto_best_gen}'
                shadow = self.stat_font.render(gen_text, True, (0,0,0))
                text = self.stat_font.render(gen_text, True, (255, 255, 255))
                rect = text.get_rect(center=(288, 620))
                self.screen.blit(shadow, (rect.x+2, rect.y+2))
                self.screen.blit(text, rect)
                
            info_text = self.stat_font.render("Click anywhere to Restart", True, (255, 255, 255))
            info_rect = info_text.get_rect(center=(288, 650))
            self.screen.blit(info_text, info_rect)

            # --- DRAW HOME BUTTON (WHITE BUTTON / DARK ICON) ---
            pygame.draw.rect(self.screen, (255, 255, 255), self.btn_home_rect, border_radius=8)
            pygame.draw.rect(self.screen, (84, 56, 71), self.btn_home_rect, 3, border_radius=8)
            
            icon_col = (84, 56, 71)
            hx, hy = self.btn_home_rect.x, self.btn_home_rect.y
            pygame.draw.polygon(self.screen, icon_col, [(hx+10, hy+20), (hx+25, hy+10), (hx+40, hy+20)])
            pygame.draw.rect(self.screen, icon_col, (hx+15, hy+20, 20, 20))
            pygame.draw.rect(self.screen, (255, 255, 255), (hx+22, hy+30, 6, 10))

    def draw_medal(self, pos):
        medal_img = None
        color = None
        
        # --- MEDAL LOGIC ---
        # Platinum (40+) only for Manual/Surprise
        if self.score >= 40 and self.mode != 'auto': 
            medal_img = self.medals.get('platinum')
            color = (229, 228, 226)
        elif self.score >= 30: 
            medal_img = self.medals.get('gold')
            color = (255, 215, 0)
        elif self.score >= 20: 
            medal_img = self.medals.get('silver')
            color = (192, 192, 192)
        elif self.score >= 10: 
            medal_img = self.medals.get('bronze')
            color = (205, 127, 50)
        
        if medal_img:
            medal_rect = medal_img.get_rect(center = pos) 
            self.screen.blit(medal_img, medal_rect)
        elif color:
            pygame.draw.circle(self.screen, color, (int(pos[0]), int(pos[1])), 22)
            pygame.draw.circle(self.screen, (255,255,255), (int(pos[0]), int(pos[1])), 22, 2)

    def draw_ai_stats(self):
        margin = 10
        box_width = 220
        box_height = 100
        s = pygame.Surface((box_width, box_height))
        s.set_alpha(160) 
        s.fill((0, 0, 0)) 
        box_rect = s.get_rect(bottomright=(576 - margin, 850)) 
        self.screen.blit(s, box_rect)

        text_x = box_rect.left + 15
        text_y = box_rect.top + 15
        line_height = 25

        gen_surf = self.stat_font.render(f"Gen: {self.evolution.generation_count}", True, (255, 255, 255))
        self.screen.blit(gen_surf, (text_x, text_y))

        alive_surf = self.stat_font.render(f"Alive: {sum(1 for b in self.birds if b.alive)}/{self.evolution.population_size}", True, (255, 255, 255))
        self.screen.blit(alive_surf, (text_x, text_y + line_height))
        
        best_surf = self.stat_font.render(f"Best: {self.score_manager.auto_best} (Gen {self.score_manager.auto_best_gen})", True, (255, 255, 255))
        self.screen.blit(best_surf, (text_x, text_y + line_height * 2))

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
        manual_text = self.menu_font.render(f"Manual Mode (M)", True, (255, 255, 255))
        self.screen.blit(manual_text, manual_text.get_rect(center=self.btn_manual_rect.center))

        pygame.draw.rect(self.screen, (66, 173, 244), self.btn_auto_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), self.btn_auto_rect, 4, border_radius=12)
        auto_text = self.menu_font.render(f"Auto Mode (A)", True, (255, 255, 255))
        self.screen.blit(auto_text, auto_text.get_rect(center=self.btn_auto_rect.center))

        pygame.draw.rect(self.screen, (155, 89, 182), self.btn_surprise_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), self.btn_surprise_rect, 4, border_radius=12)
        surprise_text = self.menu_font.render(f"Surprise Mode (S)", True, (255, 255, 255))
        self.screen.blit(surprise_text, surprise_text.get_rect(center=self.btn_surprise_rect.center))
        
        self.draw_arrow('left', self.arrow_left_rect)
        self.draw_arrow('right', self.arrow_right_rect)

        current_color_name = self.available_skins[self.current_skin_index]
        skin_text = self.menu_font.render(current_color_name.upper(), True, (255, 255, 255))
        self.screen.blit(skin_text, skin_text.get_rect(center=(288, 600)))
        self.screen.blit(self.bird.image, self.bird.image.get_rect(center=(288, 650)))
        
        reset_text = self.stat_font.render("Press 'R' to Reset Scores", True, (200, 200, 200))
        self.screen.blit(reset_text, reset_text.get_rect(center=(288, 900)))

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
        
        for bird in self.birds:
            bird.set_skin(self.available_skins[self.current_skin_index])
            
        # --- FORCE NIGHT FOR GHOST ---
        if self.available_skins[self.current_skin_index] == 'ghost':
            self.current_bg = self.bg_night
        else:
            self.current_bg = self.bg_day

    def reset_game(self):
        self.paused = False
        self.pipe_manager.reset()
        self.score = 0
        
        if self.mode == 'surprise':
            self.bird.reset()
            self.bird.gravity_val = 0.15 
            self.bird.jump_force = -4
            self.state = 'get_ready'
        elif self.mode == 'manual':
            self.bird.reset()
            self.bird.gravity_val = 0.25 
            self.bird.jump_force = -6
            self.state = 'get_ready'
        elif self.mode == 'auto':
            if len(self.birds) > 0:
                self.birds = self.evolution.create_next_generation(self.birds)
            
            current_skin = self.available_skins[self.current_skin_index]
            for bird in self.birds:
                bird.reset()
                bird.gravity_val = 0.25
                bird.jump_force = -6
                bird.alive = True
                bird.set_skin(current_skin)
            
            self.state = 'playing'

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

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m and self.state == 'menu':
                        self.mode = 'manual'
                        self.reset_game()
                    if event.key == pygame.K_a and self.state == 'menu':
                        self.mode = 'auto'
                        self.reset_game()
                    if event.key == pygame.K_s and self.state == 'menu':
                        self.mode = 'surprise'
                        self.reset_game()
                    
                    if (event.key == pygame.K_p or event.key == pygame.K_ESCAPE) and self.state == 'playing':
                        self.paused = not self.paused
                    
                    if event.key == pygame.K_r and self.state == 'menu':
                        self.score_manager.reset_scores()
                        
                    if self.state == 'game_over':
                        if event.key == pygame.K_SPACE:
                            self.reset_game()
                        elif event.key == pygame.K_m: 
                            self.state = 'menu'

                if self.state == 'menu':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_manual_rect.collidepoint(event.pos):
                            self.mode = 'manual'
                            self.reset_game()
                        elif self.btn_auto_rect.collidepoint(event.pos):
                            self.mode = 'auto'
                            self.reset_game()
                        elif self.btn_surprise_rect.collidepoint(event.pos):
                            self.mode = 'surprise'
                            self.reset_game()
                        elif self.arrow_left_rect.collidepoint(event.pos):
                            self.change_skin('prev')
                        elif self.arrow_right_rect.collidepoint(event.pos):
                            self.change_skin('next')

                elif self.state == 'get_ready':
                    if event.type == self.bird.ANIMATION_EVENT:
                        self.bird.animate()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        self.state = 'playing'
                        self.bird.jump()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.state = 'playing'
                        self.bird.jump()

                elif self.state == 'playing':
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.mode != 'auto' and not self.paused:
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
                        if event.type == self.bird.ANIMATION_EVENT and self.mode != 'auto':
                            self.bird.animate()

                elif self.state == 'game_over':
                    # Allow Click Navigation
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_home_rect.collidepoint(event.pos):
                            self.state = 'menu'
                        else:
                            self.reset_game()

            self.screen.blit(self.current_bg, (0, 0))

            if self.state == 'menu':
                self.draw_menu()
                self.base.move()

            elif self.state == 'get_ready':
                self.pipe_manager.draw(self.screen)
                self.base.draw(self.screen)
                if self.mode != 'auto':
                    self.bird.draw(self.screen)
                elif self.mode == 'auto':
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
                    if self.mode != 'auto':
                        self.bird.move()
                        self.bird.draw(self.screen)
                        if self.check_collision():
                            pass
                    elif self.mode == 'auto':
                        for bird in self.birds:
                            if bird.alive:
                                bird.fitness += 1
                                bird.think(self.pipe_manager.pipes)
                                bird.move()
                                bird.draw(self.screen)
                        self.check_collision()
                        self.draw_ai_stats()
                if self.paused:
                    if self.mode != 'auto': self.bird.draw(self.screen)
                    self.draw_pause_menu()
                else:
                    pygame.draw.rect(self.screen, (255, 255, 255), self.btn_pause_rect, 2, border_radius=5)
                    pygame.draw.line(self.screen, (255,255,255), (35, 30), (35, 60), 4)
                    pygame.draw.line(self.screen, (255,255,255), (55, 30), (55, 60), 4)
                self.display_score()

            elif self.state == 'game_over':
                if self.mode != 'auto': 
                    self.bird.draw(self.screen)
                elif self.mode == 'auto':
                    for bird in self.birds:
                         bird.draw(self.screen)
                self.pipe_manager.draw(self.screen)
                self.base.draw(self.screen)
                self.display_score()

            self.base.draw(self.screen)
            pygame.display.update()
            self.clock.tick(120)

if __name__ == "__main__":
    game = Game()
    game.run()