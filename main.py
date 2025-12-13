import pygame as pg
import random

pg.init()

# ==================== CONSTANTS ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
FPS = 60
GROUND_TOP = 354
WORLD_SCROLL_SPEED = 5
PLATFORM_HEIGHT = 16
PLATFORM_WIDTH = 64

# =============PLAYER CLASS 
class Player(pg.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.size = 32
        self.rect = pg.Rect(x, y - self.size, self.size, self.size)
        
        # Physics
        self.vy = 0
        self.GRAVITY = 1
        self.JUMP_SPEED = 15
        self.max_jumps = 2
        self.jump_count = 0
        self.on_ground = True
        
        # State
        self.facing_right = True
        self.running = False
        self.in_air = False
        self.anim_index = 0
        self.hp = 3
        
        # Load sprites
        self.idle_frames = []
        self.run_frames = []
        self.jump_image = None
        self.load_sprites()
    
    def load_sprites(self):
        try:
            idle_sheet = pg.image.load("assets/MainCharacters/VirtualGuy/idle.png").convert_alpha()
            _, _, w, h = idle_sheet.get_rect()
            for i in range(w // self.size):
                surf = idle_sheet.subsurface(i * self.size, 0, self.size, self.size)
                self.idle_frames.append(surf)
            
            run_sheet = pg.image.load("assets/MainCharacters/VirtualGuy/run.png").convert_alpha()
            _, _, rw, rh = run_sheet.get_rect()
            for i in range(rw // self.size):
                surf = run_sheet.subsurface(i * self.size, 0, self.size, self.size)
                self.run_frames.append(surf)
            
            self.jump_image = pg.image.load("assets/MainCharacters/VirtualGuy/jump.png").convert_alpha()
        except:
            # Fallback
            self.idle_frames = [pg.Surface((self.size, self.size))]
            self.idle_frames[0].fill((0, 100, 255))
            self.run_frames = [pg.Surface((self.size, self.size))]
            self.run_frames[0].fill((0, 150, 255))
            self.jump_image = pg.Surface((self.size, self.size))
            self.jump_image.fill((100, 200, 255))
    
    def jump(self):
        if self.jump_count < self.max_jumps:
            self.vy = -self.JUMP_SPEED
            self.on_ground = False
            self.jump_count += 1
    
    def apply_gravity_and_collisions(self, platform_rects):
        # Apply gravity with previous position tracking
        prev_bottom = self.rect.bottom
        prev_top = self.rect.top
        self.vy += self.GRAVITY
        self.rect.y += self.vy
        self.on_ground = False

        # Ground collision (most common)
        if self.rect.bottom >= GROUND_TOP:
            self.rect.bottom = GROUND_TOP
            self.vy = 0
            self.on_ground = True
            self.jump_count = 0

        # Check platform collisions
        for plat in platform_rects:
            horizontal_overlap = (self.rect.right > plat.left and self.rect.left < plat.right)
            # Landing on top: we must have been above the platform previously
            if self.vy >= 0 and prev_bottom <= plat.top and self.rect.bottom >= plat.top and horizontal_overlap:
                self.rect.bottom = plat.top
                self.vy = 0
                self.on_ground = True
                self.jump_count = 0
                break
            # Head bump: hitting the underside of a platform while moving up
            if self.vy < 0 and prev_top >= plat.bottom and self.rect.top <= plat.bottom and horizontal_overlap:
                # place player just below the platform and make them fall
                self.rect.top = plat.bottom + 1
                # Make the downward bounce smoother (less jarring)
                self.vy = 4
                self.in_air = True
                break

        self.in_air = not self.on_ground
    
    def update(self, platform_rects, running):
        self.running = running
        self.apply_gravity_and_collisions(platform_rects)
    
    def draw(self, surface):
        if self.in_air:
            image = self.jump_image
        elif self.running:
            if self.anim_index >= len(self.run_frames) - 0.3:
                self.anim_index = 0
            image = self.run_frames[int(self.anim_index)]
            self.anim_index += 0.3
        else:
            if self.anim_index >= len(self.idle_frames) - 0.3:
                self.anim_index = 0
            image = self.idle_frames[int(self.anim_index)]
            self.anim_index += 0.3
        
        # Flip image when facing left
        if not self.facing_right:
            image = pg.transform.flip(image, True, False)
        
        surface.blit(image, self.rect)


# =========== FIRE TRAP CLASS 
class FireTrap(pg.sprite.Sprite):
    def __init__(self, x, y, always_visible=False):
        super().__init__()
        self.world_x = x
        self.world_y = y  # Above platform surface
        self.size = 32
        self.rect = pg.Rect(0, 0, self.size, self.size)
        self.always_visible = always_visible
        self.animation_frame = 0
        self.is_hit = False
        self.hit_timer = 0
        self.load_fire_images()
    
    def load_fire_images(self):
        """Load fire images from assets. Prefer a 32x32 spritesheet and split into frames using subsurface.
        Fallback to single on/off/hit images if necessary."""
        self.frames = []
        try:
            sheet = pg.image.load("assets/Traps/Fire/on.png").convert_alpha()
            sw, sh = sheet.get_size()
            for ty in range(0, sh, 32):
                for tx in range(0, sw, 32):
                    try:
                        frame = sheet.subsurface((tx, ty, 32, 32)).copy()
                        self.frames.append(pg.transform.scale(frame, (self.size, self.size)))
                    except Exception:
                        pass
        except Exception:
            self.frames = []

        # Fallback single images
        try:
            self.fire_on = pg.image.load("assets/Traps/Fire/on.png").convert_alpha()
            self.fire_on = pg.transform.scale(self.fire_on, (self.size, self.size))
        except:
            self.fire_on = None
        try:
            self.fire_off = pg.image.load("assets/Traps/Fire/off.png").convert_alpha()
            self.fire_off = pg.transform.scale(self.fire_off, (self.size, self.size))
        except:
            self.fire_off = None
        try:
            self.fire_hit = pg.image.load("assets/Traps/Fire/hit.png").convert_alpha()
            self.fire_hit = pg.transform.scale(self.fire_hit, (self.size, self.size))
        except:
            self.fire_hit = None
    
    def draw(self, surface, world_x, reveal=False):
        self.rect.x = self.world_x - world_x
        self.rect.y = self.world_y
        
        if -50 <= self.rect.x <= SCREEN_WIDTH + 50:
            if self.is_hit and self.fire_hit:
                surface.blit(self.fire_hit, self.rect)
            elif self.always_visible or reveal:
                # If frames are available from a spritesheet, animate by index
                if self.frames:
                    if not hasattr(self, 'anim_index'):
                        self.anim_index = 0
                    self.anim_index += 0.3
                    idx = int(self.anim_index) % len(self.frames)
                    surface.blit(self.frames[idx], self.rect)
                else:
                    # Alternate between on/off for simple animation
                    self.animation_frame += 0.1
                    if self.fire_on:
                        if int(self.animation_frame) % 2 == 0:
                            surface.blit(self.fire_on, self.rect)
                        else:
                            if self.fire_off:
                                surface.blit(self.fire_off, self.rect)
                            else:
                                surface.blit(self.fire_on, self.rect)
    
    def check_collision(self, player_rect, reveal=False, world_x=0):
        # Convert fire world position to screen coords for comparison with player_rect
        screen_x = self.world_x - world_x
        self.rect.x = screen_x
        self.rect.y = self.world_y
        # Collision applies regardless of visibility: invisible fires still damage the player.
        if not self.is_hit:
            return player_rect.colliderect(self.rect)
        return False
    
    def hit(self):
        """Called when fire hits the player"""
        self.is_hit = True
        self.hit_timer = 30  # Show hit animation for 0.5 seconds


# ========== HEALING ITEM CLASS 
class HealingItem(pg.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.world_x = x
        self.world_y = y
        self.size = 24
        self.rect = pg.Rect(0, 0, self.size, self.size)
        self.collected = False
        self.animation_frame = 0
        self.load_heal_image()
    
    def load_heal_image(self):
        """Load health item from assets"""
        try:
            # Try to load a fruit or item
            heal_img = pg.image.load("assets/Items/Fruits/Apple.png").convert_alpha()
            self.heal_image = pg.transform.scale(heal_img, (self.size, self.size))
        except:
            # Fallback: green circle
            self.heal_image = None
    
    def draw(self, surface, world_x):
        if self.collected:
            return
        
        self.rect.x = self.world_x - world_x
        self.rect.y = self.world_y
        
        if -50 <= self.rect.x <= SCREEN_WIDTH + 50:
            if self.heal_image:
                # Pulsing animation
                self.animation_frame += 0.05
                scale = 1.0 + 0.1 * (0.5 + 0.5 * (1 if int(self.animation_frame) % 2 == 0 else -1))
                scaled_img = pg.transform.scale(self.heal_image, 
                                               (int(self.size * scale), int(self.size * scale)))
                surface.blit(scaled_img, (self.rect.x - int(self.size * (scale - 1) / 2), 
                                         self.rect.y - int(self.size * (scale - 1) / 2)))
            else:
                # Fallback: green circle
                pg.draw.circle(surface, (0, 255, 0), 
                              (int(self.rect.centerx), int(self.rect.centery)), 
                              self.size // 2)
    
    def check_collision(self, player_rect):
        # Deprecated signature kept for safety — prefer check_collision_world(player_rect, world_x)
        self.rect.x = self.world_x
        self.rect.y = self.world_y
        if player_rect.colliderect(self.rect):
            self.collected = True
            return True
        return False

    def check_collision_world(self, player_rect, world_x=0):
        """Check collision where player's rect is in screen coords and item is in world coords.
        Converts item to screen coords then checks collision."""
        screen_x = self.world_x - world_x
        self.rect.x = screen_x
        self.rect.y = self.world_y
        if player_rect.colliderect(self.rect):
            self.collected = True
            return True
        return False


# ===========LEVEL CLASS
class Level:
    def __init__(self):
        try:
            self.bg_tile = pg.image.load("assets/Background/Blue.png").convert_alpha()
            _, _, self.bg_w, self.bg_h = self.bg_tile.get_rect()
        except:
            self.bg_tile = pg.Surface((200, 200))
            self.bg_tile.fill((50, 150, 255))
            self.bg_w, self.bg_h = 200, 200
        
        try:
            terrain_sheet = pg.image.load("assets/Terrain/Terrain.png").convert_alpha()
            self.ground_tile = terrain_sheet.subsurface(96, 0, 48, 64).copy()
        except:
            self.ground_tile = pg.Surface((48, 64))
            self.ground_tile.fill((100, 200, 100))
        # Precompute a rotated tile for vertical wall drawing
        try:
            self.wall_tile = pg.transform.rotate(self.ground_tile, 90)
        except Exception:
            self.wall_tile = self.ground_tile
        
        # Block size (width and height) used for platform placement
        self.tile_w = 48  # full block width
        self.tile_h = self.ground_tile.get_height()  # full block height (use actual asset height)
        
        # Platform blocks - continuous generation
        # store both block positions and platform group starts
        self.platform_positions = []
        self.platform_groups = []
        self.group_fire_counts = []
        self.prev_group_had_invisible = False
        self.generate_initial_platforms()
        
        # Fire traps (initially invisible)
        self.fire_traps = []
        self.last_fire_x = 0
        self.generate_fire_traps()
        
        # Healing items
        self.heal_items = []
        self.last_heal_x = 0
        self.generate_heal_items()
    
    def generate_initial_platforms(self):
        """Generate initial platforms - each platform has 4 blocks side by side"""
        # Each platform is 4 blocks (48 pixels each = 192 pixels total)
        # Platforms are spaced to allow jumping between them
        platform_groups = [
            (150, 280),   # Platform 1: Y=280 (lower)
            (400, 250),   # Platform 2: Y=250 (middle)
            (650, 220),   # Platform 3: Y=220 (higher)
            (900, 250),   # Platform 4: Y=250 (middle)
            (1150, 280),  # Platform 5: Y=280 (lower)
        ]
        
        self.platform_positions = []
        self.platform_groups = []
        # Add a left-side wall filling the whole column at x=0 so the player cannot move left past it
        wall_x = 0
        # Use the rotated wall tile height for vertical spacing so blocks touch with no gaps
        wall_block_h = self.wall_tile.get_height()
        blocks_high = (SCREEN_HEIGHT // wall_block_h) + 3
        # Build wall from bottom up so blocks stick together exactly using wall_tile height
        for i in range(blocks_high):
            wall_y = GROUND_TOP - wall_block_h * (i + 1)
            self.platform_positions.append((wall_x, wall_y))

        for start_x, y in platform_groups:
            # Record platform group start for spawning fires/heals
            self.platform_groups.append((start_x, y))
            # Add 4 blocks for each platform (tile_w pixels wide each, sticking together)
            for i in range(4):
                self.platform_positions.append((start_x + i * self.tile_w, y))
    
    def generate_fire_traps(self):
        """Generate initial fire traps for existing platform groups.
        Ensures at most 2 fires per platform group and positions them above the platform."""
        if not self.fire_traps:
            for gi, (start_x, y) in enumerate(self.platform_groups):
                # Decide how many fires: bias toward fewer (0, 1, or 2)
                num = random.choices([0, 1, 2], weights=[50, 40, 10], k=1)[0]
                # If the previous two groups had zero fires, force at least one here
                if len(self.group_fire_counts) >= 2 and self.group_fire_counts[-1] == 0 and self.group_fire_counts[-2] == 0 and num == 0:
                    num = random.choices([1, 2], weights=[80, 20], k=1)[0]
                # record
                self.group_fire_counts.append(num)
                indices = list(range(4))
                random.shuffle(indices)
                for i in range(min(num, 2)):
                    idx = indices[i]
                    fx = start_x + idx * self.tile_w + (self.tile_w - 32) // 2
                    fy = y - 40  # above platform
                    # Bias toward visible fires; invisible fires rarer
                    invisible_prob = 0.18
                    always_visible = random.random() > invisible_prob
                    self.fire_traps.append(FireTrap(fx, fy, always_visible))

    def update_fire_traps(self, world_x):
        # New fires are spawned when new platform groups are created (see Game.update_playing).
        # Keep this function as a no-op to avoid arbitrary spawns.
        return

    def generate_heal_items(self):
        """Generate healing items at the start: at most one per platform group and rarer."""
        # Make heals more frequent at start
        if not self.heal_items:
            for (start_x, y) in self.platform_groups:
                # Increased probability to spawn a heal on this platform group
                if random.random() < 0.28:  # ~28% chance
                    idx = random.randrange(4)
                    hx = start_x + idx * self.tile_w + (self.tile_w - 24) // 2
                    hy = y - 60
                    self.heal_items.append(HealingItem(hx, hy))

    def update_heal_items(self, world_x):
        # New heals are spawned when new platform groups are created (see Game.update_playing).
        return

    def spawn_fires_for_group(self, start_x, y):
        """Spawn fires for a newly created platform group (max 2)."""
        # increase chance of having a fire (appear a bit more)
        num = random.choices([0, 1, 2], weights=[30, 50, 20], k=1)[0]
        # enforce no 3 consecutive empties
        if len(self.group_fire_counts) >= 2 and self.group_fire_counts[-1] == 0 and self.group_fire_counts[-2] == 0 and num == 0:
            num = random.choices([1, 2], weights=[80, 20], k=1)[0]
        # record
        self.group_fire_counts.append(num)
        indices = list(range(4))
        random.shuffle(indices)

        # Track whether this group contains any invisible fires
        group_has_invisible = False

        for i in range(min(num, 2)):
            idx = indices[i]
            fx = start_x + idx * self.tile_w + (self.tile_w - 32) // 2
            # sometimes place fire on ground instead of just above platform
            if random.random() < 0.18:
                fy = GROUND_TOP - 32
            else:
                fy = y - 40
            # Invisible fires should be rarer — roughly 1 every 3-5 groups
            invisible_prob = 0.20
            always_visible = random.random() > invisible_prob
            if not always_visible:
                group_has_invisible = True
            self.fire_traps.append(FireTrap(fx, fy, always_visible))

        # Avoid two consecutive groups being invisible-only (no consecutive 'black platforms')
        if group_has_invisible and self.prev_group_had_invisible:
            # ensure at least one visible fire in this group: flip the first fire to visible
            for f in reversed(self.fire_traps[-min(num,2):]):
                if not f.always_visible:
                    f.always_visible = True
                    group_has_invisible = False
                    break

        self.prev_group_had_invisible = group_has_invisible

    def spawn_heal_for_group(self, start_x, y):
        """Possibly spawn a single heal for a new platform group (rare)."""
        if random.random() < 0.28:  # increased to ~28% chance
            attempts = 4
            chosen = None
            for _ in range(attempts):
                idx = random.randrange(4)
                hx = start_x + idx * self.tile_w + (self.tile_w - 24) // 2
                hy = y - 60
                # ensure sufficient gap from any fire on this group (>= 80 px)
                too_close = False
                for f in self.fire_traps:
                    # check world-x distance for fires near this group's range
                    if abs(f.world_x - hx) < 80 and abs(f.world_y - hy) < 80:
                        too_close = True
                        break
                if not too_close:
                    chosen = (hx, hy)
                    break
            if chosen:
                self.heal_items.append(HealingItem(chosen[0], chosen[1]))
    
    def draw_background(self, surface, world_x):
        offset_x = -world_x % self.bg_w
        for i in range(-1, SCREEN_WIDTH // self.bg_w + 2):
            for j in range(-1, SCREEN_HEIGHT // self.bg_h + 2):
                rect = self.bg_tile.get_rect(topleft=(i * self.bg_w + offset_x, j * self.bg_h))
                surface.blit(self.bg_tile, rect)
    
    def draw_ground(self, surface, world_x):
        offset_x = -world_x % self.tile_w
        for i in range(-3, SCREEN_WIDTH // self.tile_w + 4):
            rect = self.ground_tile.get_rect(topleft=(i * self.tile_w + offset_x, GROUND_TOP))
            surface.blit(self.ground_tile, rect)
    
    def get_platform_rects(self, world_x):
        rects = []
        for (px, py) in self.platform_positions:
            # Convert world coordinates to screen coordinates so they match player's rect
            screen_x = px - world_x
            rect = pg.Rect(screen_x, py, self.tile_w, self.tile_h)
            rects.append(rect)
        return rects
    
    def draw_platforms(self, surface, world_x):
        for (px, py) in self.platform_positions:
            screen_x = px - world_x
            if px == 0:
                # Left wall: draw rotated wall tile so it looks vertical
                rect = self.wall_tile.get_rect(topleft=(screen_x, py))
                surface.blit(self.wall_tile, rect)
            else:
                rect = self.ground_tile.get_rect(topleft=(screen_x, py))
                surface.blit(self.ground_tile, rect)
    
    def draw_fire_traps(self, surface, world_x, reveal=False):
        for fire in self.fire_traps:
            # Only draw if within screen bounds
            fire.rect.x = fire.world_x - world_x
            if -50 <= fire.rect.x <= SCREEN_WIDTH + 50:
                fire.draw(surface, world_x, reveal)


# ========== GAME CLASS
class Game:
    def __init__(self):
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("Time Runner")
        self.clock = pg.time.Clock()
        self.font_big = pg.font.SysFont(None, 60)
        self.font_small = pg.font.SysFont(None, 28)
        
        self.level = Level()
        # Place player just right of the left wall (wall is at x=0, tile_w wide)
        start_x = self.level.tile_w + 10
        self.player = Player(start_x, GROUND_TOP)
        self.world_x = 0
        
        # Game states
        self.state = "intro"
        self.running = True
        self.score = 0
        self.tab_revealed = False
        self.tab_cooldown = 0
        self.tab_duration = 0  # duration in frames (set when used)
        # cache for fast grayscale overlay approach
        self._grayscale_cache = None
        self._grayscale_dirty = True
    
    def reset(self):
        self.level = Level()
        start_x = self.level.tile_w + 10
        self.player = Player(start_x, GROUND_TOP)
        self.world_x = 0
        self.state = "intro"
        self.score = 0
        self.tab_revealed = False
        self.tab_cooldown = 0
    
    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.running = False
                
                if self.state == "intro":
                    if event.key == pg.K_SPACE:
                        self.state = "playing"
                
                elif self.state == "playing":
                    if event.key in (pg.K_SPACE, pg.K_UP):
                        self.player.jump()
                    
                    # TAB to reveal fire (always available, cooldown after use)
                    if event.key == pg.K_TAB:
                        # only allow if not already revealed and cooldown finished
                        if (not self.tab_revealed) and self.tab_cooldown <= 0:
                            self.tab_revealed = True
                            # reveal for 15 seconds
                            self.tab_duration = 15 * FPS
                            # cooldown will start after reveal ends (set later)
                            # mark grayscale cache dirty so it will be recomputed (or re-applied)
                            self._grayscale_dirty = True
                
                elif self.state == "gameover":
                    if event.key == pg.K_r:
                        self.reset()
    
    def update_playing(self):
        keys = pg.key.get_pressed()
        running = False
        
        # Player movement - only scroll when player presses keys
        if keys[pg.K_RIGHT]:
            self.world_x += WORLD_SCROLL_SPEED
            self.player.facing_right = True
            running = True
            self.score += 1  # Score increases as world scrolls
        if keys[pg.K_LEFT]:
            if self.world_x > 0:
                self.world_x -= WORLD_SCROLL_SPEED
                # Decrease score when running left (do not go below 0)
                self.score = max(0, self.score - 1)
            # Make left movement animate as well (use flipped run frames)
            self.player.facing_right = False
            running = True
        
        # Generate new platforms ahead - each platform has 4 blocks
        if self.level.platform_positions:
            last_x = max([p[0] for p in self.level.platform_positions])
            if last_x < self.world_x + SCREEN_WIDTH + 500:
                # Create a new 4-block platform with good spacing
                platform_start_x = last_x + 250  # Space between platforms
                # Different base heights for jumping; then raise them by 5-80 px to add variation
                base_y = random.choice([220, 250, 280])
                raise_amt = random.randint(5, 80)
                platform_y = max(80, base_y - raise_amt)
                # Record the new platform group
                self.level.platform_groups.append((platform_start_x, platform_y))
                for i in range(4):
                    self.level.platform_positions.append((platform_start_x + i * self.level.tile_w, platform_y))
                # Spawn fires and possible heal for this new group
                self.level.spawn_fires_for_group(platform_start_x, platform_y)
                self.level.spawn_heal_for_group(platform_start_x, platform_y)
        
        # Generate new fire traps
        self.level.update_fire_traps(self.world_x)
        
        # Get platforms
        platform_rects = self.level.get_platform_rects(self.world_x)
        
        # Update player
        self.player.update(platform_rects, running)
        
        # Update fire traps
        self.level.update_fire_traps(self.world_x)
        
        # Update healing items
        self.level.update_heal_items(self.world_x)
        
        # Update TAB ability
        if self.tab_revealed:
            self.tab_duration -= 1
            if self.tab_duration <= 0:
                # reveal ended; start cooldown of 20 seconds
                self.tab_revealed = False
                self.tab_cooldown = 20 * FPS

        if self.tab_cooldown > 0:
            self.tab_cooldown -= 1
        
        # Check fire collision
        fire_to_remove = []
        for i, fire in enumerate(self.level.fire_traps):
            if fire.check_collision(self.player.rect, self.tab_revealed, self.world_x):
                fire.hit()  # Show hit animation
                self.player.hp -= 1
                fire_to_remove.append(i)
                if self.player.hp <= 0:
                    self.state = "gameover"
            elif fire.is_hit:
                fire.hit_timer -= 1
                if fire.hit_timer <= 0:
                    fire_to_remove.append(i)
        
        # Remove fires after hit animation (reverse order)
        for i in reversed(fire_to_remove):
            self.level.fire_traps.pop(i)
        
        # Check healing item collision
        heal_to_remove = []
        for i, heal in enumerate(self.level.heal_items):
            if not heal.collected and heal.check_collision_world(self.player.rect, self.world_x):
                self.player.hp = min(3, self.player.hp + 1)  # Restore 1 HP, max 3
                heal_to_remove.append(i)
        
        # Remove collected heals
        for i in reversed(heal_to_remove):
            self.level.heal_items.pop(i)
        
        # Fall off screen = game over
        if self.player.rect.y > SCREEN_HEIGHT:
            self.state = "gameover"
    
    def draw_intro(self):
        self.screen.fill((20, 20, 40))
        
        title = self.font_big.render("Time RUNNER", True, (255, 100, 0))
        info = self.font_small.render("Press SPACE to start", True, (200, 200, 200))
        controls = self.font_small.render("Arrow Keys: Move | SPACE: Jump | TAB: Reveal Fire", True, (180, 180, 180))
        info2 = self.font_small.render("TAB reveal: 15s  |  cooldown: 20s after use", True, (150, 200, 255))
        
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 100)))
        self.screen.blit(controls, controls.get_rect(center=(SCREEN_WIDTH // 2, 180)))
        self.screen.blit(info2, info2.get_rect(center=(SCREEN_WIDTH // 2, 220)))
        self.screen.blit(info, info.get_rect(center=(SCREEN_WIDTH // 2, 300)))
    
    def draw_hud(self):
        # HUD color / position settings
        hud_x = 50  # moved from 10 to 50
        hp_text_color = (5, 31, 64)  # dark navy blue for text
        hp_fill_color = (0, 180, 255)  # cyan color for the HP bar fill

        # HP bar
        hp_text = self.font_small.render(f"HP: {self.player.hp}/3", True, hp_text_color)
        self.screen.blit(hp_text, (hud_x, 10))

        # HP visual bar
        bar_width = 100
        bar_height = 20
        bar_x = hud_x
        bar_y = 40

        # Background
        pg.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))

        # HP fill
        hp_percentage = self.player.hp / 3
        pg.draw.rect(self.screen, hp_fill_color, (bar_x, bar_y, bar_width * hp_percentage, bar_height))

        # Border
        pg.draw.rect(self.screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 2)

        # TAB ability status (use same color as HP)
        if self.tab_cooldown <= 0:
            tab_text = self.font_small.render("TAB: REVEAL [READY]", True, hp_text_color)
        else:
            seconds_left = self.tab_cooldown // 60
            tab_text = self.font_small.render(f"TAB: {seconds_left}s cooldown", True, hp_text_color)
        self.screen.blit(tab_text, (SCREEN_WIDTH - 250, 50))

        # Score display
        score_text = self.font_small.render(f"Score: {self.score}", True, hp_text_color)
        self.screen.blit(score_text, (SCREEN_WIDTH - 140, 10))

        # Reveal indicator
        if self.tab_revealed:
            reveal_text = self.font_small.render("FIRE REVEALED!", True, (255, 100, 0))
            self.screen.blit(reveal_text, (SCREEN_WIDTH // 2 - 100, 10))
    
    def draw_playing(self):
        self.level.draw_background(self.screen, self.world_x)
        self.level.draw_ground(self.screen, self.world_x)
        self.level.draw_platforms(self.screen, self.world_x)
        # Draw only visible fires initially; invisible fires will be drawn colored when TAB is active
        self.level.draw_fire_traps(self.screen, self.world_x, reveal=False)

        # Draw healing items
        for heal_item in self.level.heal_items:
            if not heal_item.collected:
                heal_item.draw(self.screen, self.world_x)

        self.player.draw(self.screen)

        self.draw_hud()

        # If TAB reveal active: apply a fast grayscale-like overlay, then draw invisible fires colored on top
        if self.tab_revealed:
            # Use a fast overlay approach rather than slow per-pixel conversion.
            # Create a desaturating multiply overlay to approximate grayscale quickly.
            overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert_alpha()
            overlay.fill((120, 120, 120))
            # Multiply colors to desaturate
            self.screen.blit(overlay, (0, 0), special_flags=pg.BLEND_RGB_MULT)

            # Draw invisible fires on top in color
            for fire in self.level.fire_traps:
                if not fire.always_visible and not fire.is_hit:
                    fire.draw(self.screen, self.world_x, reveal=True)
    
    def draw_gameover(self):
        self.level.draw_background(self.screen, self.world_x)
        self.level.draw_ground(self.screen, self.world_x)
        self.level.draw_platforms(self.screen, self.world_x)
        # Draw only visible fires; invisible ones will be highlighted if TAB is active
        self.level.draw_fire_traps(self.screen, self.world_x, reveal=False)
        
        # Draw healing items
        for heal_item in self.level.heal_items:
            if not heal_item.collected:
                heal_item.draw(self.screen, self.world_x)
        
        self.player.draw(self.screen)
        
        overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        text = self.font_big.render("GAME OVER", True, (255, 50, 50))
        final_score = pg.font.SysFont(None, 40).render(f"Final Score: {self.score}", True, (255, 200, 100))
        info = self.font_small.render("Press R to restart or ESC to quit", True, (255, 255, 255))
        
        self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, 120)))
        self.screen.blit(final_score, final_score.get_rect(center=(SCREEN_WIDTH // 2, 180)))
        self.screen.blit(info, info.get_rect(center=(SCREEN_WIDTH // 2, 250)))

        # If TAB reveal active on gameover screen: apply fast overlay then draw invisible fires colored
        if self.tab_revealed:
            overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert_alpha()
            overlay.fill((120, 120, 120))
            self.screen.blit(overlay, (0, 0), special_flags=pg.BLEND_RGB_MULT)
            for fire in self.level.fire_traps:
                if not fire.always_visible and not fire.is_hit:
                    fire.draw(self.screen, self.world_x, reveal=True)
    
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            
            if self.state == "intro":
                self.draw_intro()
            elif self.state == "playing":
                self.update_playing()
                self.draw_playing()
            elif self.state == "gameover":
                self.draw_gameover()
            
            pg.display.flip()
        
        pg.quit()


# ========MAIN ENTRY
if __name__ == "__main__":
    game = Game()
    game.run()
