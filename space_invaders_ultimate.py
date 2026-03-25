import pygame
import random
import math
import sys
import os
import json
from enum import Enum
from datetime import datetime

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2)

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    LEVEL_COMPLETE = 4
    HIGH_SCORES = 5
    BOSS_BATTLE = 6

class PowerUpType(Enum):
    RAPID_FIRE = 1
    SHIELD = 2
    MULTI_SHOT = 3
    SLOW_TIME = 4
    DOUBLE_POINTS = 5
    HEAL = 6
    NUKE = 7

# ==================== BACKGROUND ====================
class Background:
    def __init__(self):
        self.stars = []
        for _ in range(150):
            self.stars.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'speed': random.uniform(0.5, 3),
                'size': random.randint(1, 3),
                'twinkle': random.uniform(0, 2 * math.pi)
            })
    
    def update(self):
        for star in self.stars:
            star['y'] += star['speed']
            if star['y'] > SCREEN_HEIGHT:
                star['y'] = 0
                star['x'] = random.randint(0, SCREEN_WIDTH)
            star['twinkle'] += 0.05
    
    def draw(self, screen):
        screen.fill(BLACK)
        for star in self.stars:
            brightness = int(100 + 155 * (math.sin(star['twinkle']) + 1) / 2)
            color = (brightness, brightness, brightness)
            pygame.draw.circle(screen, color, (int(star['x']), int(star['y'])), star['size'])

# ==================== BOSS ====================
class Boss:
    def __init__(self, level):
        self.level = level
        self.width = 120
        self.height = 100
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = 50
        boss_number = level // 5
        self.health = 50 + (boss_number - 1) * 30
        self.max_health = self.health
        self.speed_x = 2
        self.direction = 1
        self.shoot_cooldown = 0
        self.attack_pattern = 0
        self.pattern_timer = 0
        self.colors = [RED, ORANGE, PURPLE, YELLOW, CYAN]
        self.color = self.colors[min(boss_number - 1, len(self.colors) - 1)]
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    
    def update(self):
        self.x += self.speed_x * self.direction
        if self.x <= 50 or self.x + self.width >= SCREEN_WIDTH - 50:
            self.direction *= -1
        
        self.pattern_timer += 1
        if self.pattern_timer > 180:
            self.pattern_timer = 0
            self.attack_pattern = (self.attack_pattern + 1) % 4
        
        self.rect.x = self.x
        self.rect.y = self.y
        
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = 25
            return self.shoot_pattern()
        else:
            self.shoot_cooldown -= 1
        return []
    
    def shoot_pattern(self):
        bullets = []
        if self.attack_pattern == 0:
            bullets.append(Bullet(self.x + self.width//2 - 2, self.y + self.height, 6, False, 0))
        elif self.attack_pattern == 1:
            for offset in [-15, 0, 15]:
                bullets.append(Bullet(self.x + self.width//2 + offset, self.y + self.height, 6, False, 0))
        elif self.attack_pattern == 2:
            for angle in [-20, -10, 0, 10, 20]:
                bullets.append(Bullet(self.x + self.width//2 - 2, self.y + self.height, 6, False, angle/5))
        elif self.attack_pattern == 3:
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                vx = math.cos(rad) * 3
                vy = math.sin(rad) * 3
                bullets.append(CircularBullet(self.x + self.width//2, self.y + self.height//2, vx, vy))
        return bullets
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 3)
        
        eye_size = 15
        pygame.draw.circle(screen, WHITE, (int(self.x + self.width * 0.3), int(self.y + self.height * 0.3)), eye_size)
        pygame.draw.circle(screen, WHITE, (int(self.x + self.width * 0.7), int(self.y + self.height * 0.3)), eye_size)
        pygame.draw.circle(screen, BLACK, (int(self.x + self.width * 0.3), int(self.y + self.height * 0.3)), eye_size//2)
        pygame.draw.circle(screen, BLACK, (int(self.x + self.width * 0.7), int(self.y + self.height * 0.3)), eye_size//2)
        
        bar_width = self.width
        bar_height = 10
        health_percent = self.health / self.max_health
        pygame.draw.rect(screen, RED, (self.x, self.y - 15, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 15, bar_width * health_percent, bar_height))
        
        font = pygame.font.Font(None, 24)
        pattern_names = ["Straight", "Triple", "Spread", "Circular"]
        text = font.render(f"Pattern: {pattern_names[self.attack_pattern]}", True, WHITE)
        screen.blit(text, (self.x, self.y - 35))
        
        health_text = font.render(f"HP: {self.health}/{self.max_health}", True, WHITE)
        screen.blit(health_text, (self.x, self.y - 55))
    
    def hit(self, damage):
        self.health -= damage
        return self.health <= 0

class CircularBullet:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.is_player = False
        self.width = 6
        self.height = 6
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.lifetime = 180
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.rect.x = self.x
        self.rect.y = self.y
        return 0 <= self.y <= SCREEN_HEIGHT and self.lifetime > 0
    
    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), 3)

# ==================== SAVE MANAGER ====================
class SaveManager:
    def __init__(self):
        self.save_file = "space_invaders_save.json"
    
    def save_game(self, game_data):
        try:
            with open(self.save_file, 'w') as f:
                json.dump({
                    'score': game_data['score'],
                    'level': game_data['level'],
                    'lives': game_data['lives'],
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                }, f)
            return True
        except:
            return False
    
    def load_game(self):
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return None

# ==================== POWER-UP ====================
class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.type = power_type
        self.width = 20
        self.height = 20
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.lifetime = 300
        self.colors = {
            PowerUpType.RAPID_FIRE: CYAN,
            PowerUpType.SHIELD: BLUE,
            PowerUpType.MULTI_SHOT: GREEN,
            PowerUpType.SLOW_TIME: PURPLE,
            PowerUpType.DOUBLE_POINTS: GOLD,
            PowerUpType.HEAL: RED,
            PowerUpType.NUKE: ORANGE
        }
        self.symbols = {
            PowerUpType.RAPID_FIRE: "⚡",
            PowerUpType.SHIELD: "🛡️",
            PowerUpType.MULTI_SHOT: "💥",
            PowerUpType.SLOW_TIME: "🐢",
            PowerUpType.DOUBLE_POINTS: "2x",
            PowerUpType.HEAL: "❤️",
            PowerUpType.NUKE: "💣"
        }
    
    def update(self):
        self.y += 2
        self.lifetime -= 1
        self.rect.y = self.y
        return self.lifetime > 0 and self.y < SCREEN_HEIGHT
    
    def draw(self, screen):
        color = self.colors[self.type]
        points = []
        for i in range(5):
            angle = math.radians(i * 72 - 90)
            x1 = self.x + self.width // 2 + math.cos(angle) * self.width // 2
            y1 = self.y + self.height // 2 + math.sin(angle) * self.height // 2
            points.append((x1, y1))
            angle = math.radians(i * 72 + 36 - 90)
            x2 = self.x + self.width // 2 + math.cos(angle) * self.width // 3
            y2 = self.y + self.height // 2 + math.sin(angle) * self.height // 3
            points.append((x2, y2))
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, WHITE, points, 2)
        font = pygame.font.Font(None, 16)
        text = font.render(self.symbols[self.type], True, WHITE)
        text_rect = text.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
        screen.blit(text, text_rect)

# ==================== PARTICLE ====================
class Particle:
    def __init__(self, x, y, color, velocity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.vx = velocity[0]
        self.vy = velocity[1]
        self.lifetime = lifetime
        self.initial_lifetime = lifetime
        self.size = random.randint(2, 4)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        return self.lifetime > 0
    
    def draw(self, screen):
        alpha = self.lifetime / self.initial_lifetime
        size = int(self.size * alpha)
        if size > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

# ==================== SOUND MANAGER ====================
class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.sound_enabled = True
        self.volume = 0.7
        self.create_sounds()
    
    def create_sounds(self):
        def create_beep(frequency, duration, volume=0.7):
            try:
                sample_rate = 22050
                samples = int(sample_rate * duration)
                import numpy as np
                arr = np.zeros((samples, 2), dtype=np.int16)
                for i in range(samples):
                    t = float(i) / sample_rate
                    value = int(32767 * volume * np.sin(2 * np.pi * frequency * t))
                    arr[i] = [value, value]
                return pygame.sndarray.make_sound(arr)
            except:
                return None
        
        try:
            self.sounds['laser'] = create_beep(880, 0.1, 0.7)
            self.sounds['explosion'] = create_beep(220, 0.3, 0.8)
            self.sounds['powerup'] = create_beep(660, 0.2, 0.7)
            self.sounds['level_up'] = create_beep(440, 0.5, 0.7)
            self.sounds['game_over'] = create_beep(110, 1.0, 0.7)
            self.sounds['hit'] = create_beep(330, 0.15, 0.7)
            self.sounds['boss'] = create_beep(55, 0.5, 0.6)
        except:
            self.sound_enabled = False
    
    def play(self, sound_name):
        if self.sound_enabled and sound_name in self.sounds:
            try:
                if self.sounds[sound_name]:
                    self.sounds[sound_name].set_volume(self.volume)
                    self.sounds[sound_name].play()
            except:
                pass
    
    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
    
    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        return self.sound_enabled

# ==================== PLAYER ====================
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 30
        self.speed = 5
        self.lives = 3
        self.invincible_frames = 0
        self.shoot_cooldown = 0
        self.image = self.create_ship_image()
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        self.rapid_fire_active = False
        self.rapid_fire_timer = 0
        self.shield_active = False
        self.shield_timer = 0
        self.multi_shot_active = False
        self.multi_shot_timer = 0
        self.double_points_active = False
        self.double_points_timer = 0
        self.slow_time_active = False
        self.slow_time_timer = 0
        
        self.score_multiplier = 1
    
    def create_ship_image(self):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        points = [
            (self.width // 2, 0),
            (self.width, self.height),
            (self.width // 2, self.height - 5),
            (0, self.height)
        ]
        pygame.draw.polygon(surface, CYAN, points)
        pygame.draw.polygon(surface, WHITE, points, 2)
        return surface
    
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.invincible_frames > 0:
            self.invincible_frames -= 1
        
        if self.rapid_fire_active:
            self.rapid_fire_timer -= 1
            if self.rapid_fire_timer <= 0:
                self.rapid_fire_active = False
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False
        if self.multi_shot_active:
            self.multi_shot_timer -= 1
            if self.multi_shot_timer <= 0:
                self.multi_shot_active = False
        if self.double_points_active:
            self.double_points_timer -= 1
            if self.double_points_timer <= 0:
                self.double_points_active = False
                self.score_multiplier = 1
        if self.slow_time_active:
            self.slow_time_timer -= 1
            if self.slow_time_timer <= 0:
                self.slow_time_active = False
        
        self.rect.x = self.x
        self.rect.y = self.y
    
    def shoot(self):
        cooldown_max = 5 if self.rapid_fire_active else 15
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = cooldown_max
            bullets = []
            if self.multi_shot_active:
                bullets.append(Bullet(self.x + self.width // 2 - 2, self.y, -8, True, -3))
                bullets.append(Bullet(self.x + self.width // 2 - 2, self.y, -8, True, 0))
                bullets.append(Bullet(self.x + self.width // 2 - 2, self.y, -8, True, 3))
            else:
                bullets.append(Bullet(self.x + self.width // 2 - 2, self.y, -8, True, 0))
            return bullets
        return []
    
    def nuke(self, enemies):
        destroyed = len(enemies)
        enemies.clear()
        return destroyed
    
    def heal(self):
        self.lives = min(5, self.lives + 1)
    
    def draw(self, screen):
        if self.shield_active:
            shield_radius = 30
            for i in range(3):
                radius = shield_radius - i * 5
                pygame.draw.circle(screen, (0, 100, 255), 
                                 (int(self.x + self.width//2), int(self.y + self.height//2)), radius, 2)
        if self.invincible_frames == 0 or (self.invincible_frames // 5) % 2 == 0:
            screen.blit(self.image, (self.x, self.y))
        
        y_offset = 60
        if self.rapid_fire_active:
            text = pygame.font.Font(None, 20).render("⚡ RAPID FIRE", True, CYAN)
            screen.blit(text, (10, y_offset))
            y_offset += 25
        if self.multi_shot_active:
            text = pygame.font.Font(None, 20).render("💥 MULTI-SHOT", True, GREEN)
            screen.blit(text, (10, y_offset))
            y_offset += 25
        if self.shield_active:
            text = pygame.font.Font(None, 20).render("🛡️ SHIELD", True, BLUE)
            screen.blit(text, (10, y_offset))
            y_offset += 25
        if self.double_points_active:
            text = pygame.font.Font(None, 20).render("2x POINTS!", True, GOLD)
            screen.blit(text, (10, y_offset))
        
        for i in range(self.lives):
            heart_x = 10 + i * 30
            pygame.draw.polygon(screen, RED, [
                (heart_x + 15, 20), (heart_x + 25, 30),
                (heart_x + 15, 40), (heart_x + 5, 30)
            ])
    
    def hit(self):
        if self.invincible_frames == 0 and not self.shield_active:
            self.lives -= 1
            self.invincible_frames = 60
            return True
        return False
    
    def apply_powerup(self, powerup_type):
        if powerup_type == PowerUpType.RAPID_FIRE:
            self.rapid_fire_active = True
            self.rapid_fire_timer = 600
        elif powerup_type == PowerUpType.SHIELD:
            self.shield_active = True
            self.shield_timer = 600
        elif powerup_type == PowerUpType.MULTI_SHOT:
            self.multi_shot_active = True
            self.multi_shot_timer = 600
        elif powerup_type == PowerUpType.DOUBLE_POINTS:
            self.double_points_active = True
            self.double_points_timer = 600
            self.score_multiplier = 2
        elif powerup_type == PowerUpType.SLOW_TIME:
            self.slow_time_active = True
            self.slow_time_timer = 600
        elif powerup_type == PowerUpType.HEAL:
            self.heal()
        elif powerup_type == PowerUpType.NUKE:
            return "NUKE"
        return None

# ==================== ENEMY ====================
class Enemy:
    def __init__(self, x, y, enemy_type):
        self.x = x
        self.y = y
        self.type = enemy_type
        self.width = 35
        self.height = 30
        self.speed_x = 1
        if enemy_type == 0:
            self.color = RED
            self.points = 10
            self.health = 1
        elif enemy_type == 1:
            self.color = ORANGE
            self.points = 20
            self.health = 2
        else:
            self.color = PURPLE
            self.points = 30
            self.health = 3
        self.max_health = self.health
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    
    def update(self, direction, drop_amount):
        self.x += direction * self.speed_x
        self.y += drop_amount
        self.rect.x = self.x
        self.rect.y = self.y
    
    def draw(self, screen):
        points = [
            (self.x + self.width // 2, self.y),
            (self.x + self.width - 5, self.y + 10),
            (self.x + self.width, self.y + 20),
            (self.x + self.width - 10, self.y + self.height - 5),
            (self.x + self.width // 2, self.y + self.height),
            (self.x + 10, self.y + self.height - 5),
            (self.x, self.y + 20),
            (self.x + 5, self.y + 10)
        ]
        pygame.draw.polygon(screen, self.color, points)
        pygame.draw.polygon(screen, WHITE, points, 2)
        
        if self.health > 1:
            bar_width = self.width
            bar_height = 4
            health_percent = self.health / self.max_health
            pygame.draw.rect(screen, RED, (self.x, self.y - 8, bar_width, bar_height))
            pygame.draw.rect(screen, GREEN, (self.x, self.y - 8, bar_width * health_percent, bar_height))
        
        eye_y = self.y + 10
        pygame.draw.circle(screen, WHITE, (int(self.x + self.width * 0.3), int(eye_y)), 3)
        pygame.draw.circle(screen, WHITE, (int(self.x + self.width * 0.7), int(eye_y)), 3)
        pygame.draw.circle(screen, BLACK, (int(self.x + self.width * 0.3), int(eye_y)), 1)
        pygame.draw.circle(screen, BLACK, (int(self.x + self.width * 0.7), int(eye_y)), 1)
    
    def shoot(self):
        if random.random() < 0.01:
            return Bullet(self.x + self.width // 2 - 2, self.y + self.height, 5, False, 0)
        return None
    
    def hit(self):
        self.health -= 1
        return self.health <= 0

# ==================== BULLET ====================
class Bullet:
    def __init__(self, x, y, speed, is_player, angle_offset=0):
        self.x = x
        self.y = y
        self.speed = speed
        self.is_player = is_player
        self.angle_offset = angle_offset
        self.width = 4
        self.height = 10
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    
    def update(self):
        self.x += self.angle_offset * 0.5
        self.y += self.speed
        self.rect.x = self.x
        self.rect.y = self.y
        return 0 <= self.y <= SCREEN_HEIGHT
    
    def draw(self, screen):
        color = GREEN if self.is_player else RED
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 1)

# ==================== EXPLOSION ====================
class Explosion:
    def __init__(self, x, y, size='normal'):
        self.x = x
        self.y = y
        self.frames = 30 if size == 'boss' else 20
        self.initial_frames = self.frames
        self.size = size
    
    def update(self):
        self.frames -= 1
        return self.frames > 0
    
    def draw(self, screen):
        if self.frames > 0:
            size_mult = 2 if self.size == 'boss' else 1
            size = int(20 * (1 - self.frames / self.initial_frames) + 5) * size_mult
            alpha = self.frames / self.initial_frames
            color = (255, int(255 * alpha), 0)
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), size)
            for _ in range(5 if self.size == 'boss' else 3):
                angle = random.uniform(0, 2 * math.pi)
                rad = size * random.uniform(0.5, 1)
                x2 = self.x + math.cos(angle) * rad
                y2 = self.y + math.sin(angle) * rad
                pygame.draw.circle(screen, color, (int(x2), int(y2)), size // 3)

# ==================== HIGH SCORE MANAGER ====================
class HighScoreManager:
    def __init__(self):
        self.filename = "space_invaders_highscores.json"
        self.scores = self.load_scores()
    
    def load_scores(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_scores(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.scores[:10], f)
        except:
            pass
    
    def add_score(self, score, player_name="Player"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.scores.append({"name": player_name, "score": score, "date": timestamp})
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:10]
        self.save_scores()
        return self.get_rank(score)
    
    def get_rank(self, score):
        for i, s in enumerate(self.scores):
            if score >= s["score"]:
                return i + 1
        return len(self.scores) + 1
    
    def get_top_scores(self):
        return self.scores[:5]

# ==================== MAIN GAME CLASS ====================
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ULTIMATE SPACE INVADERS")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.font_tiny = pygame.font.Font(None, 24)
        
        self.sound_manager = SoundManager()
        self.high_score_manager = HighScoreManager()
        self.save_manager = SaveManager()
        self.background = Background()
        
        self.reset_game()
    
    def reset_game(self):
        # Start in MENU state
        self.state = GameState.MENU
        self.score = 0
        self.level = 1
        self.player = Player(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT - 60)
        self.enemies = []
        self.bullets = []
        self.particles = []
        self.explosions = []
        self.powerups = []
        self.boss = None
        
        self.enemy_direction = 1
        self.enemy_drop = 0
        self.enemy_speed_multiplier = 1
        self.powerup_spawn_timer = 0
        
        self.player_name = ""
        self.name_input_active = False
        
        # Don't create enemies yet - wait for SPACE in menu
        # self.create_enemies()  # REMOVED - we'll create when game starts
    
    def start_game(self):
        """Start the game from menu"""
        self.state = GameState.PLAYING
        self.level = 1
        self.score = 0
        self.player = Player(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT - 60)
        self.create_enemies()
    
    def create_enemies(self):
        # Check if this level is a boss level (every 5th level)
        if self.level % 5 == 0:
            print(f"=== BOSS BATTLE! Level {self.level} ===")
            self.state = GameState.BOSS_BATTLE
            self.boss = Boss(self.level)
            self.enemies.clear()
            self.sound_manager.play('boss')
            return
        
        # Normal level - create regular enemies
        self.state = GameState.PLAYING
        self.enemies.clear()
        rows = min(3 + self.level // 2, 5)
        cols = min(8 + self.level // 2, 11)
        start_x = (SCREEN_WIDTH - (cols * 45)) // 2
        start_y = 50
        
        for row in range(rows):
            for col in range(cols):
                enemy_type = row % 3
                x = start_x + col * 45
                y = start_y + row * 45
                self.enemies.append(Enemy(x, y, enemy_type))
        
        print(f"Level {self.level} - {len(self.enemies)} enemies spawned")
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    if event.key == pygame.K_SPACE:
                        self.start_game()
                    elif event.key == pygame.K_h:
                        self.state = GameState.HIGH_SCORES
                    elif event.key == pygame.K_s:
                        self.sound_manager.toggle_sound()
                    elif event.key == pygame.K_l:
                        loaded = self.save_manager.load_game()
                        if loaded:
                            self.score = loaded['score']
                            self.level = loaded['level']
                            self.player.lives = loaded['lives']
                            self.create_enemies()
                            print("Game loaded!")
                    elif event.key == pygame.K_UP:
                        self.sound_manager.set_volume(min(1.0, self.sound_manager.volume + 0.1))
                    elif event.key == pygame.K_DOWN:
                        self.sound_manager.set_volume(max(0.0, self.sound_manager.volume - 0.1))
                
                elif self.state == GameState.PLAYING:
                    if event.key == pygame.K_SPACE:
                        bullets = self.player.shoot()
                        for bullet in bullets:
                            self.bullets.append(bullet)
                            self.sound_manager.play('laser')
                    elif event.key == pygame.K_ESCAPE:
                        self.reset_game()
                    elif event.key == pygame.K_s:
                        self.sound_manager.toggle_sound()
                    elif event.key == pygame.K_UP:
                        self.sound_manager.set_volume(min(1.0, self.sound_manager.volume + 0.1))
                    elif event.key == pygame.K_DOWN:
                        self.sound_manager.set_volume(max(0.0, self.sound_manager.volume - 0.1))
                    elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        save_data = {'score': self.score, 'level': self.level, 'lives': self.player.lives}
                        if self.save_manager.save_game(save_data):
                            print("Game saved!")
                
                elif self.state == GameState.BOSS_BATTLE:
                    if event.key == pygame.K_SPACE:
                        bullets = self.player.shoot()
                        for bullet in bullets:
                            self.bullets.append(bullet)
                            self.sound_manager.play('laser')
                    elif event.key == pygame.K_ESCAPE:
                        self.reset_game()
                
                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.reset_game()
                    elif event.key == pygame.K_RETURN:
                        self.name_input_active = True
                
                elif self.state == GameState.LEVEL_COMPLETE:
                    if event.key == pygame.K_SPACE:
                        self.level += 1
                        self.boss = None
                        self.create_enemies()
                        self.sound_manager.play('level_up')
                        print(f"Moving to Level {self.level}")
                
                elif self.state == GameState.HIGH_SCORES:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        self.state = GameState.MENU
                
                if self.name_input_active:
                    if event.key == pygame.K_RETURN:
                        if self.player_name:
                            self.high_score_manager.add_score(self.score, self.player_name)
                            self.name_input_active = False
                            self.player_name = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    elif event.unicode and event.unicode.isprintable():
                        self.player_name += event.unicode
        
        return True
    
    def update_normal(self):
        self.player.update()
        self.background.update()
        
        for bullet in self.bullets[:]:
            if not bullet.update():
                self.bullets.remove(bullet)
        
        edge_reached = False
        for enemy in self.enemies:
            enemy.update(self.enemy_direction * self.enemy_speed_multiplier, self.enemy_drop)
            if enemy.x <= 0 or enemy.x + enemy.width >= SCREEN_WIDTH:
                edge_reached = True
        
        if edge_reached:
            self.enemy_direction *= -1
            self.enemy_drop = 10 * self.enemy_speed_multiplier
        else:
            self.enemy_drop = 0
        
        self.enemy_speed_multiplier = 1 + (self.level - 1) * 0.1
        
        for enemy in self.enemies:
            if enemy.y + enemy.height >= SCREEN_HEIGHT - 80:
                self.state = GameState.GAME_OVER
                self.sound_manager.play('game_over')
        
        if self.enemies and random.random() < 0.02:
            shooter = random.choice(self.enemies)
            bullet = shooter.shoot()
            if bullet:
                self.bullets.append(bullet)
        
        self.powerup_spawn_timer += 1
        if self.powerup_spawn_timer > 300 and len(self.enemies) > 0:
            self.powerup_spawn_timer = 0
            if random.random() < 0.3:
                powerup_type = random.choice(list(PowerUpType))
                x = random.randint(50, SCREEN_WIDTH - 50)
                self.powerups.append(PowerUp(x, 50, powerup_type))
        
        for powerup in self.powerups[:]:
            if not powerup.update():
                self.powerups.remove(powerup)
            if powerup.rect.colliderect(self.player.rect):
                result = self.player.apply_powerup(powerup.type)
                self.powerups.remove(powerup)
                self.sound_manager.play('powerup')
                if result == "NUKE":
                    destroyed = self.player.nuke(self.enemies)
                    self.score += destroyed * 50
        
        for bullet in self.bullets[:]:
            if bullet.is_player:
                for enemy in self.enemies[:]:
                    if bullet.rect.colliderect(enemy.rect):
                        self.bullets.remove(bullet)
                        if enemy.hit():
                            self.enemies.remove(enemy)
                            points = enemy.points * self.player.score_multiplier
                            self.score += points
                            self.explosions.append(Explosion(enemy.x + enemy.width//2, enemy.y + enemy.height//2))
                            self.sound_manager.play('explosion')
                            for _ in range(15):
                                angle = random.uniform(0, 2 * math.pi)
                                speed = random.uniform(1, 8)
                                vx = math.cos(angle) * speed
                                vy = math.sin(angle) * speed
                                self.particles.append(Particle(enemy.x + enemy.width//2, enemy.y + enemy.height//2, enemy.color, (vx, vy), 20))
                        else:
                            self.particles.append(Particle(enemy.x + enemy.width//2, enemy.y + enemy.height//2, YELLOW, (random.uniform(-3, 3), random.uniform(-3, 3)), 10))
                        break
            else:
                if bullet.rect.colliderect(self.player.rect):
                    self.bullets.remove(bullet)
                    if self.player.hit():
                        self.explosions.append(Explosion(self.player.x + self.player.width//2, self.player.y + self.player.height//2))
                        self.sound_manager.play('hit')
                        if self.player.lives <= 0:
                            self.state = GameState.GAME_OVER
                            self.sound_manager.play('game_over')
        
        for particle in self.particles[:]:
            if not particle.update():
                self.particles.remove(particle)
        
        for explosion in self.explosions[:]:
            if not explosion.update():
                self.explosions.remove(explosion)
        
        if len(self.enemies) == 0:
            self.state = GameState.LEVEL_COMPLETE
            self.sound_manager.play('level_up')
    
    def update_boss(self):
        if self.boss:
            self.player.update()
            self.background.update()
            
            for bullet in self.bullets[:]:
                if not bullet.update():
                    self.bullets.remove(bullet)
            
            boss_bullets = self.boss.update()
            self.bullets.extend(boss_bullets)
            
            for bullet in self.bullets[:]:
                if bullet.is_player and bullet.rect.colliderect(self.boss.rect):
                    self.bullets.remove(bullet)
                    if self.boss.hit(10):
                        self.explosions.append(Explosion(self.boss.x + self.boss.width//2, self.boss.y + self.boss.height//2, 'boss'))
                        self.sound_manager.play('explosion')
                        self.score += 500 * (self.level // 5)
                        print(f"BOSS DEFEATED! +{500 * (self.level // 5)} points!")
                        for _ in range(50):
                            angle = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(1, 10)
                            vx = math.cos(angle) * speed
                            vy = math.sin(angle) * speed
                            self.particles.append(Particle(self.boss.x + self.boss.width//2, self.boss.y + self.boss.height//2, self.boss.color, (vx, vy), 30))
                        self.boss = None
                        self.state = GameState.LEVEL_COMPLETE
                    else:
                        self.particles.append(Particle(bullet.x, bullet.y, YELLOW, (random.uniform(-2, 2), random.uniform(-2, 2)), 5))
                    break
            
            for bullet in self.bullets[:]:
                if not bullet.is_player and bullet.rect.colliderect(self.player.rect):
                    self.bullets.remove(bullet)
                    if self.player.hit():
                        self.explosions.append(Explosion(self.player.x + self.player.width//2, self.player.y + self.player.height//2))
                        self.sound_manager.play('hit')
                        if self.player.lives <= 0:
                            self.state = GameState.GAME_OVER
                            self.sound_manager.play('game_over')
            
            for particle in self.particles[:]:
                if not particle.update():
                    self.particles.remove(particle)
            
            for explosion in self.explosions[:]:
                if not explosion.update():
                    self.explosions.remove(explosion)
        else:
            self.state = GameState.LEVEL_COMPLETE
    
    def update(self):
        if self.state == GameState.PLAYING:
            self.update_normal()
        elif self.state == GameState.BOSS_BATTLE:
            self.update_boss()
    
    def draw(self):
        self.background.draw(self.screen)
        
        if self.state == GameState.PLAYING:
            for enemy in self.enemies:
                enemy.draw(self.screen)
        elif self.state == GameState.BOSS_BATTLE and self.boss:
            self.boss.draw(self.screen)
        
        self.player.draw(self.screen)
        
        for bullet in self.bullets:
            bullet.draw(self.screen)
        
        for powerup in self.powerups:
            powerup.draw(self.screen)
        
        for particle in self.particles:
            particle.draw(self.screen)
        
        for explosion in self.explosions:
            explosion.draw(self.screen)
        
        score_text = self.font_small.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        level_text = self.font_small.render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(level_text, (SCREEN_WIDTH - 120, 10))
        
        if self.player.score_multiplier > 1:
            mult_text = self.font_medium.render(f"{self.player.score_multiplier}x SCORE!", True, GOLD)
            mult_rect = mult_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
            self.screen.blit(mult_text, mult_rect)
        
        if self.state == GameState.MENU:
            title = self.font_large.render("ULTIMATE SPACE INVADERS", True, CYAN)
            title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
            self.screen.blit(title, title_rect)
            
            y_start = SCREEN_HEIGHT // 2
            options = [
                ("Press SPACE to Start", WHITE),
                ("Press H for High Scores", WHITE),
                ("Press L to Load Game", GREEN),
                (f"Sound: {'ON' if self.sound_manager.sound_enabled else 'OFF'}", CYAN)
            ]
            
            for i, (text, color) in enumerate(options):
                option = self.font_medium.render(text, True, color)
                option_rect = option.get_rect(center=(SCREEN_WIDTH//2, y_start + i * 50))
                self.screen.blit(option, option_rect)
            
            info = self.font_tiny.render("Every 5th Level: BOSS BATTLE!", True, GOLD)
            info_rect = info.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
            self.screen.blit(info, info_rect)
        
        elif self.state == GameState.BOSS_BATTLE:
            boss_text = self.font_large.render("BOSS BATTLE!", True, RED)
            boss_rect = boss_text.get_rect(center=(SCREEN_WIDTH//2, 100))
            self.screen.blit(boss_text, boss_rect)
        
        elif self.state == GameState.GAME_OVER:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            game_over = self.font_large.render("GAME OVER", True, RED)
            game_over_rect = game_over.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80))
            self.screen.blit(game_over, game_over_rect)
            
            final_score = self.font_medium.render(f"Score: {self.score}", True, WHITE)
            final_score_rect = final_score.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20))
            self.screen.blit(final_score, final_score_rect)
            
            if not self.name_input_active and (len(self.high_score_manager.scores) < 10 or self.score > self.high_score_manager.scores[-1]["score"]):
                enter_name = self.font_small.render("Press ENTER to save your score!", True, GREEN)
                enter_rect = enter_name.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
                self.screen.blit(enter_name, enter_rect)
            elif self.name_input_active:
                name_prompt = self.font_small.render("Enter your name: " + self.player_name + "_", True, WHITE)
                name_rect = name_prompt.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
                self.screen.blit(name_prompt, name_rect)
            
            restart = self.font_small.render("Press SPACE to play again", True, WHITE)
            restart_rect = restart.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100))
            self.screen.blit(restart, restart_rect)
        
        elif self.state == GameState.LEVEL_COMPLETE:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            complete = self.font_large.render("LEVEL COMPLETE!", True, GREEN)
            complete_rect = complete.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(complete, complete_rect)
            
            next_text = f"Press SPACE for Level {self.level + 1}"
            if (self.level + 1) % 5 == 0:
                next_text += " - BOSS BATTLE!"
            next_level = self.font_medium.render(next_text, True, YELLOW)
            next_level_rect = next_level.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            self.screen.blit(next_level, next_level_rect)
        
        elif self.state == GameState.HIGH_SCORES:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            title = self.font_large.render("HIGH SCORES", True, GOLD)
            title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 80))
            self.screen.blit(title, title_rect)
            
            scores = self.high_score_manager.get_top_scores()
            y_pos = 180
            
            if not scores:
                no_scores = self.font_medium.render("No scores yet!", True, WHITE)
                no_scores_rect = no_scores.get_rect(center=(SCREEN_WIDTH//2, y_pos))
                self.screen.blit(no_scores, no_scores_rect)
            else:
                for i, score_data in enumerate(scores):
                    rank_color = GOLD if i == 0 else SILVER if i == 1 else (255, 215, 0) if i == 2 else WHITE
                    rank_text = self.font_medium.render(f"#{i+1}", True, rank_color)
                    self.screen.blit(rank_text, (SCREEN_WIDTH//2 - 200, y_pos))
                    
                    name_text = self.font_medium.render(score_data["name"][:15], True, WHITE)
                    self.screen.blit(name_text, (SCREEN_WIDTH//2 - 120, y_pos))
                    
                    score_text = self.font_medium.render(str(score_data["score"]), True, CYAN)
                    self.screen.blit(score_text, (SCREEN_WIDTH//2 + 50, y_pos))
                    
                    y_pos += 50
            
            back_text = self.font_small.render("Press SPACE or ESC to return", True, WHITE)
            back_rect = back_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 80))
            self.screen.blit(back_text, back_rect)
        
        pygame.display.flip()
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()