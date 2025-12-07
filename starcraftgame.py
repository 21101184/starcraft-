import pygame
import random
import math

# ---------- 설정 및 상수 ----------
WIDTH, HEIGHT = 1200, 800
FPS = 60

# 색상
c_BLACK = (0, 0, 0)
c_WHITE = (255, 255, 255)
c_MARINE = (0, 100, 255)
c_TANK = (50, 50, 150)
c_TURRET = (100, 100, 100)
c_ZERGLING = (200, 50, 50)
c_MUTAL = (150, 0, 150)
c_ULTRA = (100, 50, 0)
c_INFESTED = (50, 200, 50)
c_MINERAL = (0, 255, 255)
c_RED = (255, 50, 50) 
c_GREEN = (50, 255, 50) 


MAX_MINERS_PER_PATCH = 8

# 유닛 스펙 
STATS = {
    'worker': {'cost': 50, 'hp': 60, 'atk': 5, 'range': 20, 'speed': 60, 'cd': 1.0},
    'marine': {'cost': 50, 'hp': 40, 'atk': 6, 'range': 120, 'speed': 45, 'cd': 0.8},
    'tank':   {'cost': 300, 'hp': 150, 'atk': 100, 'range': 280, 'speed': 30, 'cd': 2.0},
    'turret': {'cost': 100, 'hp': 200, 'atk': 20, 'range': 220, 'speed': 0, 'cd': 0.5},
    
    'supply': {'cost': 100, 'hp': 500, 'atk': 0, 'range': 0, 'speed': 0, 'cd': 0},
    'bunker': {'cost': 150, 'hp': 400, 'atk': 0, 'range': 180, 'speed': 0, 'cd': 1.5, 'capacity': 4}, 
    
    'zergling': {'hp': 40, 'atk': 5, 'range': 20, 'speed': 65, 'cd': 0.6},
    'zergling_fast': {'hp': 40, 'atk': 6, 'range': 20, 'speed': 85, 'cd': 0.5},
    'zergling_super': {'hp': 40, 'atk': 8, 'range': 20, 'speed': 85, 'cd': 0.3},
    'mutal': {'hp': 120, 'atk': 9, 'range': 120, 'speed': 70, 'cd': 1.2}, 
    'ultra': {'hp': 500, 'atk': 25, 'range': 30, 'speed': 55, 'cd': 1.5},
    'infested': {'hp': 40, 'atk': 150, 'range': 20, 'speed': 50, 'cd': 0.1}, 
}

EXPANSION_COST = 400
BASE_HP = 2000

# 이미지 로드 관리자 
IMAGES = {}
def load_images():
    files = {
        'marine': 'marine.png', 'tank': 'tank.png', 'turret': 'turret.png', 'worker': 'scv.png',
        'supply': 'supply.png', 'bunker': 'bunker.png', 
        'zergling': 'zergling.png', 'mutal': 'mutal.png', 'ultra': 'ultra.png', 'infested': 'infested.png',
        'base': 'base.png', 'base_enemy': 'hive.png', 
        'smineral' : 'smineral.png', 'lmineral' : 'lmineral.png',
        'infestedbase' : 'infestedbase.png'
    }
    for key, filename in files.items():
        try:
           
            img = pygame.image.load(filename)
            size = 60 if key in ['base', 'base_enemy'] else (45 if key in ['tank', 'ultra'] else 30)
            if key in ['supply', 'bunker']: size = 40 
            if key == 'smineral': size = 15 
            if key == 'lmineral': size = 30
                
            IMAGES[key] = pygame.transform.scale(img, (size, size))
        except:
            
            IMAGES[key] = None

def distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

# ---------- 클래스 정의  ----------

class Unit:
    def __init__(self, pos, u_type, team):
        self.pos = list(pos)
        self.type = u_type
        self.team = team
        
        # 스탯 초기화 
        if 'zergling' in u_type or u_type in STATS: base = STATS[u_type]
        else: base = STATS.get(u_type, STATS['marine'])
            
        self.hp = base['hp']
        self.max_hp = base['hp']
        self.atk = base['atk']
        self.range = base['range']
        self.speed = base['speed']
        self.cooldown_time = base['cd']
        self.radius = 15 
        
        if u_type in ['tank', 'ultra']: self.radius = 25
        elif u_type in ['turret', 'supply', 'bunker']: self.radius = 20
        
        self.cooldown = 0
        self.target = None
        self.target_pos = None
        self.selected = False
        
        # 일꾼 전용 상태 변수
        self.worker_state = 'idle'
        self.carrying_mineral = False
        self.harvest_timer = 0
        self.target_mineral = None 
        

        # 벙커 전용 속성 
        self.cargo = []
        self.capacity = base.get('capacity', 0)
        
        self.img_key = 'zergling' if 'zergling' in u_type else u_type

    def apply_separation(self, all_allies, dt):
        # 건물이나 속도가 0인 유닛, 탑승 중인 유닛은 분리 로직을 적용하지 않음
        if self.speed == 0 or getattr(self, 'is_in_bunker', False): return

        separation_force_x, separation_force_y = 0, 0
        separation_radius = self.radius * 2.5 

        for other in all_allies:
            if other is self: continue 
            
            if other.type == 'marine' and getattr(other, 'is_in_bunker', False): continue

            dist = distance(self.pos, other.pos)
            min_dist = self.radius + other.radius
            
            if dist < separation_radius:
                
                if dist == 0:
                    dist = 0.01
                    dx, dy = random.uniform(-1, 1), random.uniform(-1, 1)
                else:
                    dx = self.pos[0] - other.pos[0]
                    dy = self.pos[1] - other.pos[1]

                if dist < min_dist:
                    strength = 1.0 / (dist * dist) * 10
                else:
                    strength = 1.0 / (dist * dist) * 2

                separation_force_x += dx / dist * strength
                separation_force_y += dy / dist * strength

        
        if separation_force_x != 0 or separation_force_y != 0:
            
            max_force = 150 
            force_mag = math.hypot(separation_force_x, separation_force_y)
            if force_mag > max_force:
                scale = max_force / force_mag
                separation_force_x *= scale
                separation_force_y *= scale

            self.pos[0] += separation_force_x * dt
            self.pos[1] += separation_force_y * dt

    def move(self, dt):
        # 벙커에 탑승 중인 마린은 움직일 수 없습니다.
        if getattr(self, 'is_in_bunker', False): return

        if self.speed == 0: return 
        
        dest = None
        
        # 일꾼 상태에 따른 목표 위치 우선 설정 
        if self.type == 'worker':
            if self.worker_state == 'moving_to_mineral' and self.target_mineral:
                dest = self.target_mineral.pos
            elif self.worker_state == 'returning' and self.target_pos:
                dest = self.target_pos
        
        # 일반 유닛 및 일꾼의 일반 이동 명령 처리
        if dest is None: 
            if self.target_pos:
                dest = self.target_pos
            elif self.target:
                # 공격 대상이 있지만, 사거리 내에 있다면 멈춤
                if distance(self.pos, self.target.pos) <= self.range * 0.8: 
                    return
                dest = self.target.pos

        if dest:
            dx, dy = dest[0] - self.pos[0], dest[1] - self.pos[1]
            dist = math.hypot(dx, dy)
            
            stop_dist = 5 
            # 일꾼이 광물에 접근할 때의 정지 거리를 설정
            if self.type == 'worker' and self.target_mineral:
                # 일꾼은 광물에 완전히 붙어야 하므로 거리를 명확히 설정
                stop_dist = self.radius + self.target_mineral.radius 
            elif self.target and not self.target_pos: 
                # 공격 대상이 있을 때, 공격 사거리 내에 도달하면 멈춤
                stop_dist = self.range * 0.8 
            
            if dist > stop_dist:
                move_dist = self.speed * dt
                self.pos[0] += (dx/dist) * move_dist
                self.pos[1] += (dy/dist) * move_dist
            else:
                # *********** 수정된 부분: 일꾼은 target_pos를 move에서 해제하지 않음 ***********
                if self.type != 'worker':
                    if self.target_pos: 
                        self.target_pos = None 
                
                if self.type == 'marine' and self.target and self.target.type == 'bunker' and self.target_pos == self.target.pos:
                     self.target_pos = None
                     return True
        return False

   
    def update_worker_logic(self, dt, minerals, bases, player_units, player_money_callback):
        if self.type != 'worker': return

        # 채취 대상 자원이 소진되면 초기화
        if self.target_mineral and self.target_mineral.amount <= 0:
            self.target_mineral = None
            self.worker_state = 'idle'
            self.target_pos = None

        # 1) idle → 자동으로 가장 가까운 미네랄 찾기
        if self.worker_state == 'idle':
            valid = [m for m in minerals if m.amount > 0]
            if valid:
                # 가장 가까운 광물 중 miners 수가 적은 것을 우선으로 고른다.
                def score(m):
                    miners = sum(1 for u in player_units if u.type == 'worker' and u.target_mineral == m and u.worker_state in ['moving_to_mineral','harvesting','waiting'])
                    return (miners, distance(self.pos, m.pos))
                best = min(valid, key=lambda m: score(m))
                self.target_mineral = best
                self.worker_state = 'moving_to_mineral'
                self.target_pos = None

        # 2) 미네랄 접근
        if self.worker_state == 'moving_to_mineral' and self.target_mineral:
            if distance(self.pos, self.target_mineral.pos) < max(40, self.radius + self.target_mineral.radius + 4):
                miners_on_patch = sum(1 for u in player_units
                                      if u.type == 'worker'
                                      and u.target_mineral == self.target_mineral
                                      and u.worker_state in ['harvesting', 'waiting'])
                if miners_on_patch < MAX_MINERS_PER_PATCH:
                    self.worker_state = 'harvesting'
                    self.harvest_timer = 0
                else:
                    self.worker_state = 'waiting'
                    self.harvest_timer = 0
                    self.target_pos = None

        # 3) 자원 채취
        if self.worker_state == 'harvesting':
            if not self.target_mineral or self.target_mineral.amount <= 0:
                self.target_mineral = None
                self.worker_state = 'idle'
                return
            self.harvest_timer += dt
            if self.harvest_timer >= 2.0:
                if self.target_mineral.amount > 0:
                    self.target_mineral.amount -= 50
                self.carrying_mineral = True
                self.worker_state = 'returning'
                valid_bases = [b for b in bases if b.active]
                if valid_bases:
                    closest_base = min(valid_bases, key=lambda b: distance(self.pos, b.pos))
                    self.target_pos = closest_base.pos
                else:
                    self.worker_state = 'idle'

        # 4) waiting → 자리 생기면 채취 전환
        if self.worker_state == 'waiting' and self.target_mineral:
            miners_on_patch = sum(1 for u in player_units
                                  if u.type == 'worker'
                                  and u.target_mineral == self.target_mineral
                                  and u.worker_state == 'harvesting')
            if miners_on_patch < MAX_MINERS_PER_PATCH:
                self.worker_state = 'harvesting'
                self.harvest_timer = 0

        # 5) 자원 복귀
        elif self.worker_state == 'returning':
            if not self.target_pos:
                valid_bases = [b for b in bases if b.active]
                if valid_bases:
                    closest = min(valid_bases, key=lambda b: distance(self.pos, b.pos))
                    self.target_pos = closest.pos
            if self.target_pos and distance(self.pos, self.target_pos) < 40:
                player_money_callback(8)
                self.carrying_mineral = False
                self.worker_state = 'idle'
                self.target_pos = None

    def attack_logic(self, dt, enemies):
        if self.type == 'worker': 
            self.target = None
            self.target_pos = None
            return 
            
        # 벙커 유닛은 아래 로직 무시
        if getattr(self, 'is_in_bunker', False): return
        
        current_atk = self.atk
        current_range = self.range
        
        # ... (나머지 일반 유닛 공격 로직) ...
        
        if self.type == 'bunker' and self.cargo:
            if not any(c.type == 'marine' for c in self.cargo): return
            current_atk = sum(c.atk for c in self.cargo if c.type == 'marine')
            current_range = STATS['marine']['range'] * 1.2
            self.cooldown_time = STATS['marine']['cd']
        
        if current_atk == 0:
             return 

        if self.cooldown > 0:
            self.cooldown -= dt

        if self.target:
            if getattr(self.target, 'hp', 0) <= 0:
                self.target = None

        if not self.target and not self.target_pos:
            closest = None
            mindist = current_range + 50
            for e in enemies:
                d = distance(self.pos, e.pos)
                if d < mindist:
                    mindist = d
                    closest = e
            self.target = closest
        
        if self.target:
            self.target_pos = self.target.pos
            
            d = distance(self.pos, self.target.pos)
            target_radius = getattr(self.target, 'radius', 20)
            
            if d <= current_range + target_radius:
                if self.cooldown <= 0:
                    self.target.hp -= current_atk
                    self.cooldown = self.cooldown_time
                    
                    if self.type == 'infested':
                        self.hp = 0

    def draw(self, surf):
        x, y = int(self.pos[0]), int(self.pos[1])
        
        if self.selected:
            pygame.draw.ellipse(surf, c_GREEN, (x-15, y+10, 30, 10), 2)

        if getattr(self, 'is_in_bunker', False): return

        img = IMAGES.get(self.img_key)
        if img:
            rect = img.get_rect(center=(x, y))
            surf.blit(img, rect)
        else:
            color = c_MARINE
            if self.team == 'enemy':
                if 'zergling' in self.type: color = c_ZERGLING
                elif 'mutal' in self.type: color = c_MUTAL
                elif 'ultra' in self.type: color = c_ULTRA
                elif 'infested' in self.type: color = c_INFESTED
            else:
                if self.type == 'tank': color = c_TANK
                elif self.type == 'turret': color = c_TURRET
                elif self.type == 'worker': color = (200, 200, 200)
                elif self.type == 'supply': color = (150, 150, 150)
                elif self.type == 'bunker': color = (120, 120, 180)

            pygame.draw.circle(surf, color, (x, y), self.radius)

        if self.type == 'worker' and self.carrying_mineral:
            smineral_img = IMAGES.get('smineral')
            if smineral_img:
                smineral_rect = smineral_img.get_rect(center=(x + 8, y - 8))
                surf.blit(smineral_img, smineral_rect)
            else:
                 pygame.draw.circle(surf, c_MINERAL, (x+5, y-5), 5)
        
        if self.type == 'bunker' and self.capacity > 0:
            pygame.draw.rect(surf, c_BLACK, (x - 20, y + 25, 40, 5))
            cargo_count = len(self.cargo)
            if cargo_count > 0:
                fill_width = int(40 * (cargo_count / self.capacity))
                pygame.draw.rect(surf, c_MARINE, (x - 20, y + 25, fill_width, 5))
            # 벙커 인원수 표기 
            font_small = pygame.font.SysFont("arial", 12)
            txt = f"{cargo_count}/{self.capacity}"
            txt_surface = font_small.render(txt, True, c_WHITE)
            surf.blit(txt_surface, (x - 15, y + 10))


        hp_pct = max(0, self.hp / self.max_hp)
        hp_bar_len = 24 if self.speed > 0 else 40
        hp_bar_width = 5
        
        pygame.draw.rect(surf, c_RED, (x-hp_bar_len//2, y-self.radius-8, hp_bar_len, hp_bar_width))
        pygame.draw.rect(surf, c_GREEN, (x-hp_bar_len//2, y-self.radius-8, hp_bar_len*hp_pct, hp_bar_width))


class Base:
    def __init__(self, pos, team, is_expansion=False):
        self.pos = list(pos)
        self.team = team
        self.hp = BASE_HP
        self.radius = 40
        self.is_expansion = is_expansion
        self.active = True 

    def draw(self, surf):
        if not self.active: return
        x, y = int(self.pos[0]), int(self.pos[1])
        
        img = IMAGES.get('base' if self.team == 'player' else 'base_enemy')
        if img:
            rect = img.get_rect(center=(x,y))
            surf.blit(img, rect)
        else:
            color = (0, 0, 255) if self.team == 'player' else (200, 0, 0)
            if self.is_expansion: color = (100, 100, 255)
            pygame.draw.rect(surf, color, (x-30, y-30, 60, 60))
        
        hp_pct = max(0, self.hp / BASE_HP)
        pygame.draw.rect(surf, (100,100,100), (x-30, y+35, 60, 6))
        pygame.draw.rect(surf, c_GREEN, (x-30, y+35, 60*hp_pct, 6))

class Mineral:
    def __init__(self, pos):
        self.pos = pos
        self.amount = 3000
        self.radius = 20
        self.miners_attached = 0 

   
    def draw(self, surf, font): 
        if self.amount <= 0: return
        
        img = IMAGES.get('lmineral')
        x, y = self.pos[0], self.pos[1]
        
        if img:
            rect = img.get_rect(center=(x, y))
            surf.blit(img, rect)
        else:
            pygame.draw.rect(surf, c_MINERAL, (x-10, y-15, 20, 30))
            pygame.draw.polygon(surf, (0, 200, 200), [(x, y-15), (x-15, y+5), (x+15, y+5)])

       
        display_count = self.miners_attached
        text_color = c_RED if display_count >= MAX_MINERS_PER_PATCH else c_GREEN
        
        txt = f"{display_count}/{MAX_MINERS_PER_PATCH}" 
        txt_surface = font.render(txt, True, text_color)
        
        # 광물 위쪽에 표시
        surf.blit(txt_surface, (x - txt_surface.get_width() // 2, y - self.radius - 20))


# ---------- 게임 메인  ----------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(f"StarCraft Mini v2.5 (SCV Mining Max {MAX_MINERS_PER_PATCH})")
        self.clock = pygame.time.Clock()
        
        
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        load_images()
        
        self.round = 1 

        MID_X, MID_Y = WIDTH // 2, HEIGHT // 2
        
        self.minerals = [
            # Base Minerals (100, 400 area)
            Mineral((150, 400)), 
            # Expansion Minerals (600, 400 area)
            Mineral((650, 450))
        ]
        
        self.player_base = Base((100, HEIGHT//2), 'player')
        
        self.expansion_base = Base((MID_X, MID_Y), 'player', True) if self.round >= 2 else None
        if self.expansion_base: self.expansion_base.active = False
        
        self.enemy_base = Base((WIDTH-100, HEIGHT//2), 'enemy')
        
        self.player_units = []
        self.enemy_units = []
        
        for _ in range(4):
            # 일꾼 생성 시, 초기 상태는 Unit.__init__에서 'find_mineral'로 설정됩니다.
            self.player_units.append(Unit((150+random.randint(-20,20), HEIGHT//2+random.randint(-20,20)), 'worker', 'player'))

        self.money = 200
        self.state = 'ready' 
        self.wave_queue = []
        self.selected_units = []
        self.build_mode = None 
        
        self.message = ""
        self.message_timer = 0.0
        
        self.spawn_timer = 0.0
        self.spawn_delay = 0.5 
        
        self.spawn_stop_timer = 0.0 

    def add_money(self, amount):
        self.money += amount
        
    def set_message(self, text, duration=2.0):
        """특정 메시지를 일정 시간동안 화면에 표시하도록 설정합니다."""
        self.message = text
        self.message_timer = duration

    def start_round(self):
        self.state = 'playing'
        self.wave_queue = []
        
        self.spawn_stop_timer = 20.0
        
        if self.round == 1:
            self.set_message("Round 1: Zerglings (36 units) will spawn in 20 seconds.", 3.0)
            for _ in range(36): self.wave_queue.append('zergling')
        elif self.round == 2:
            self.set_message("Round 2: Fast Zerglings & Mutalisks (12 each) will spawn in 20 seconds.", 3.0)
            for _ in range(12): self.wave_queue.append('zergling_fast')
            for _ in range(12): self.wave_queue.append('mutal')
        elif self.round == 3:
            msg = "Round 3: Super Zerglings & Ultralisks (Dangerous wave!)"
            if getattr(self, 'exp_destroyed', False):
                for _ in range(10): self.wave_queue.append('infested')
                msg += " + Infested Terrans"
            self.set_message(msg + " will spawn in 20 seconds.", 3.0)
            for _ in range(12): self.wave_queue.append('zergling_super')
            for _ in range(4): self.wave_queue.append('ultra')

        random.shuffle(self.wave_queue)

    def spawn_enemy(self, dt):
        # wave_queue가 없으면 return
        if not self.wave_queue:
            return

        # spawn_stop_timer가 0 이하일 때만 실제 스폰 로직 실행
        if self.spawn_stop_timer > 0:
            return

        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_delay:
            self.spawn_timer = 0
            # FIFO 방식으로 스폰
            u_type = self.wave_queue.pop(0)
            offset_y = random.randint(-150, 150)
            spawn_pos = (self.enemy_base.pos[0]-50, self.enemy_base.pos[1] + offset_y)
            self.enemy_units.append(Unit(spawn_pos, u_type, 'enemy'))

    def update(self, dt):
        
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""
        
        if self.spawn_stop_timer > 0:
            self.spawn_stop_timer -= dt
            if self.spawn_stop_timer <= 0:
                self.set_message("Enemy spawn sequence started!", 2.0)
                self.spawn_timer = 0 # 스폰 타이머 초기화

        
        miners_count = {}
        for m in self.minerals:
            miners_count[m] = 0
            
        for u in self.player_units:
            # 일꾼 유닛이 광물을 대상으로 설정했고, 광물 양이 0보다 크고, 이동 중이거나 채취 중일 때만 카운트
            if u.type == 'worker' and u.target_mineral and u.target_mineral.amount > 0 and u.worker_state in ['moving_to_mineral', 'harvesting']:
                miners_count[u.target_mineral] = miners_count.get(u.target_mineral, 0) + 1

        for m in self.minerals:
            m.miners_attached = miners_count.get(m, 0) 
        # ----------------------------------------------------

        all_enemies = self.enemy_units + ([self.enemy_base] if self.enemy_base.active else [])
        
        my_bases = [self.player_base]
        if self.expansion_base and self.expansion_base.active:
            my_bases.append(self.expansion_base)
        
        all_players = self.player_units + my_bases

        marines_to_remove = []
        # 유닛 복사본에 대해 반복하여 리스트 수정 문제를 피함
        for u in list(self.player_units):
            
            if getattr(u, 'is_in_bunker', False): 
                continue

            u.apply_separation([pu for pu in self.player_units if not getattr(pu, 'is_in_bunker', False)], dt)
            
            if u.type == 'worker':
                # 일꾼 로직 업데이트
                u.update_worker_logic(dt, self.minerals, my_bases, self.player_units, self.add_money)
            
            
            u.attack_logic(dt, all_enemies) 
            
            # 이동 (일꾼이 광물을 찾아 이동하는 것도 포함)
            if u.move(dt) is True: 
                # 벙커 진입 성공
                for pu in self.player_units:
                    if pu.type == 'bunker' and pu.target == u and len(pu.cargo) < pu.capacity:
                        pu.cargo.append(u)
                        u.is_in_bunker = True
                        u.target = None
                        u.selected = False
                        if u in self.selected_units: self.selected_units.remove(u)
                        marines_to_remove.append(u)
                        break
        
        # 벙커에 들어간 마린은 player_units에서 제거 (Unit.move 함수가 True를 반환할 때)
        self.player_units = [u for u in self.player_units if not getattr(u, 'is_in_bunker', False)]

        for u in self.player_units:
            if u.type == 'bunker':
                u.attack_logic(dt, all_enemies)
        
        for u in self.enemy_units:
            u.apply_separation(self.enemy_units, dt)
            
            if u.target and getattr(u.target, 'hp', 0) <= 0:
                 u.target = None
            
            if not u.target:
                targets = [t for t in all_players if getattr(t, 'hp', 0) > 0]
                if targets:
                    closest_target = min(targets, key=lambda t: distance(u.pos, t.pos))
                    u.target = closest_target
                    u.target_pos = None 
            
            if u.target:
                # 적 유닛은 항상 대상을 향해 이동해야 하므로 target_pos를 설정
                u.target_pos = u.target.pos 

            u.attack_logic(dt, all_players) 
            u.move(dt)

        dead_bunkers = [u for u in self.player_units if u.type == 'bunker' and u.hp <= 0]
        for bunker in dead_bunkers:
            self.unload_bunker(bunker, auto_unload=True) 

        self.player_units = [u for u in self.player_units if u.hp > 0]
        self.enemy_units = [u for u in self.enemy_units if u.hp > 0]
        
        if self.player_base.hp <= 0: self.state = 'lose'
        if self.enemy_base.hp <= 0: self.state = 'win'

        if self.expansion_base and self.expansion_base.active:
            if self.expansion_base.hp <= 0:
                self.expansion_base.active = False
                self.exp_destroyed = True

        if self.state == 'playing' and not self.wave_queue and not self.enemy_units:
            if self.round < 3:
                self.round += 1
                self.state = 'ready'
                self.money += 300
                self.set_message(f"Round {self.round} Ready! (Bonus +300)", 3.0)
            else:
                self.state = 'win'

        if self.state == 'playing': self.spawn_enemy(dt)

    def unload_bunker(self, bunker, auto_unload=False):
        """벙커에서 마린을 하차시키고 플레이어 유닛 리스트에 다시 추가합니다."""
        if bunker.type != 'bunker': return

        unload_pos_x = bunker.pos[0] + bunker.radius + 10
        unload_pos_y = bunker.pos[1] 

        unloaded_count = len(bunker.cargo)
        for marine in bunker.cargo:
            marine.pos = [unload_pos_x, unload_pos_y]
            marine.is_in_bunker = False
            marine.target = None
            marine.target_pos = None
            self.player_units.append(marine)
            unload_pos_x += 10

        bunker.cargo = []
        if not auto_unload and unloaded_count > 0:
            self.set_message(f"Unloaded {unloaded_count} Marines from Bunker.", 1.5)


    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                if self.build_mode:
                    if event.button == 1: 
                        cost = STATS[self.build_mode]['cost']
                        if self.money >= cost:
                            self.money -= cost
                            self.player_units.append(Unit((mx, my), self.build_mode, 'player'))
                            self.build_mode = None 
                        else:
                            self.set_message("Insufficient Resources!", 2.0)
                        
                    elif event.button == 3: 
                        self.build_mode = None
                    return True 

                if self.state in ['win', 'lose']:
                    if WIDTH//2 - 150 < mx < WIDTH//2 - 50 and HEIGHT//2 + 50 < my < HEIGHT//2 + 90:
                        self.__init__()
                        return True
                    elif WIDTH//2 + 50 < mx < WIDTH//2 + 150 and HEIGHT//2 + 50 < my < HEIGHT//2 + 90:
                        return False
                    return True 
                
                if event.button == 1 and self.check_ui_click(mx, my):
                    continue 
                
                if event.button == 1: 
                    # 일꾼은 공격할 수 없으므로, 공격 대상 선택 로직은 일반 유닛만 적용
                    clicked_enemy = next((e for e in self.enemy_units if distance((mx, my), e.pos) < e.radius + 10), None)
                    
                    if clicked_enemy:
                        for u in self.selected_units:
                            if u.type != 'worker':
                                u.target = clicked_enemy
                                u.target_pos = None
                    else:
                        clicked_unit = next((u for u in self.player_units if distance((mx, my), u.pos) < u.radius + 10), None)
                        
                        self.selected_units = []
                        for u in self.player_units: u.selected = False
                        
                        if clicked_unit:
                            self.selected_units = [clicked_unit]
                            clicked_unit.selected = True

                elif event.button == 3:
                    
                    clicked_bunker = next((u for u in self.player_units if u.type == 'bunker' and distance((mx, my), u.pos) < u.radius + 10), None)
                    
                    if clicked_bunker:
                        
                        if any(u.type == 'marine' for u in self.selected_units) and len(clicked_bunker.cargo) < clicked_bunker.capacity:
                            for u in self.selected_units:
                                if u.type == 'marine':
                                    u.target = clicked_bunker
                                    u.target_pos = clicked_bunker.pos
                                    self.set_message("Marines moving to Bunker.", 1.0)
                            return True
                        
                        elif clicked_bunker.selected and clicked_bunker.cargo:
                            self.unload_bunker(clicked_bunker)
                            return True
                    
                    clicked_mineral = next((m for m in self.minerals if m.amount > 0 and distance((mx, my), m.pos) < 30), None)
                    
                    # 일반 이동/광물 채취 로직
                    for u in self.selected_units:
                        if u.type == 'worker':
                            if clicked_mineral:
                                u.target_mineral = clicked_mineral
                                u.worker_state = 'moving_to_mineral'
                                u.target = None
                                u.target_pos = None
                            else:
                                u.target_pos = [mx, my]
                                u.target = None
                                u.worker_state = 'idle' 
                                u.target_mineral = None 
                        else:
                            u.target_pos = [mx, my]
                            u.target = None

        return True

    def check_ui_click(self, x, y):
        if y < HEIGHT - 100: return False 
        
        if 20 < x < 120: self.buy_unit('worker'); return True
        elif 130 < x < 230: self.buy_unit('marine'); return True
        
        elif 240 < x < 340 and self.round >= 2:
            self.enter_build_mode('turret'); return True
        elif 350 < x < 450:
            self.buy_unit('tank')
            return True
        
        elif 460 < x < 560:
            self.enter_build_mode('supply'); return True
        elif 570 < x < 670:
            self.enter_build_mode('bunker'); return True
        
        elif 700 < x < 850 and self.round >= 2:
            if self.expansion_base and not self.expansion_base.active:
                if self.money >= EXPANSION_COST:
                    self.money -= EXPANSION_COST
                    self.expansion_base.active = True
                    self.set_message("Expansion activated!", 2.0)
                else:
                    self.set_message("Insufficient Resources! (Expansion)", 2.0)
            return True
        
        return False
    
    def enter_build_mode(self, b_type):
        cost = STATS[b_type]['cost']
        if self.money >= cost:
            self.build_mode = b_type
            self.set_message(f"Build Mode: {b_type.capitalize()} - Click to build (R-Click to cancel)", 2.0)
        else:
            self.set_message(f"Insufficient Resources! ({cost} needed)", 2.0)

    def buy_unit(self, u_type):
        cost = STATS[u_type]['cost']
        if self.money >= cost:
            self.money -= cost
            spos = (self.player_base.pos[0] + random.randint(-50,50), self.player_base.pos[1] + random.randint(-50,50))
            self.player_units.append(Unit(spos, u_type, 'player'))
        else:
            self.set_message("Insufficient Resources!", 2.0)

    def draw(self):
        self.screen.fill((30, 30, 40))

       
        for m in self.minerals: m.draw(self.screen, self.font) 
        
        self.player_base.draw(self.screen)
        self.enemy_base.draw(self.screen)
        if self.expansion_base and self.expansion_base.active: self.expansion_base.draw(self.screen)
        elif self.expansion_base and not self.expansion_base.active:
            x, y = int(self.expansion_base.pos[0]), int(self.expansion_base.pos[1])
            pygame.draw.circle(self.screen, (50, 50, 50), (x, y), self.expansion_base.radius)
            
        for u in self.enemy_units: u.draw(self.screen)
        
        for u in self.player_units: 
            if not getattr(u, 'is_in_bunker', False):
                 u.draw(self.screen)

        if self.build_mode:
            mx, my = pygame.mouse.get_pos()
            pygame.draw.circle(self.screen, c_GREEN, (mx, my), STATS[self.build_mode].get('radius', 20), 1) 
            
            unit_range = STATS[self.build_mode].get('range', 0)
            if self.build_mode == 'bunker':
                marine_range = STATS['marine']['range'] * 1.2 
                pygame.draw.circle(self.screen, c_GREEN, (mx, my), marine_range, 1) 
            elif unit_range > 0:
                pygame.draw.circle(self.screen, c_GREEN, (mx, my), unit_range, 1) 
                
            t_txt = self.font.render("Click to Build (R-Click Cancel)", True, c_GREEN)
            self.screen.blit(t_txt, (mx+20, my))

        self.draw_ui()
        
        if self.message and self.message_timer > 0:
            msg_surface = self.font.render(self.message, True, (255, 255, 0)) 
            msg_rect = msg_surface.get_rect(center=(WIDTH // 2, 40))
            self.screen.blit(msg_surface, msg_rect)

        if self.spawn_stop_timer > 0 and self.state == 'playing':
            remaining = int(self.spawn_stop_timer)
            timer_text = self.font.render(f"Enemy Spawn Paused: {remaining}s", True, c_RED)
            self.screen.blit(timer_text, (WIDTH//2 - 120, 80))

        pygame.display.flip()

    def draw_ui(self):
        info = f"Round: {self.round} | Money: {self.money} | Enemies Left: {len(self.wave_queue) + len(self.enemy_units)}"
        self.screen.blit(self.font.render(info, True, c_WHITE), (20, 20))

        def draw_end_buttons():
            pygame.draw.rect(self.screen, (50, 50, 150), (WIDTH//2 - 150, HEIGHT//2 + 50, 100, 40))
            self.screen.blit(self.font.render("REPLAY", True, c_WHITE), (WIDTH//2 - 130, HEIGHT//2 + 60))
            pygame.draw.rect(self.screen, (150, 50, 50), (WIDTH//2 + 50, HEIGHT//2 + 50, 100, 40))
            self.screen.blit(self.font.render("QUIT", True, c_WHITE), (WIDTH//2 + 75, HEIGHT//2 + 60))

        if self.state == 'ready':
            ready_msg = self.font.render(f"Round {self.round} Ready. Press SPACE to Start Wave", True, (255, 255, 0))
            self.screen.blit(ready_msg, (WIDTH//2 - 180, 80))
        
        if self.state == 'lose':
            self.screen.blit(self.font.render("GAME OVER", True, c_RED), (WIDTH//2 - 50, HEIGHT//2))
            draw_end_buttons()
        elif self.state == 'win':
            self.screen.blit(self.font.render("VICTORY!", True, c_GREEN), (WIDTH//2 - 50, HEIGHT//2))
            draw_end_buttons()

        py = HEIGHT - 80
        def draw_btn(x, text, enable=True):
            color = (50, 50, 60) if enable else (30, 30, 30)
            pygame.draw.rect(self.screen, color, (x, py, 100, 40))
            pygame.draw.rect(self.screen, (200, 200, 200), (x, py, 100, 40), 2) 
            txt = self.font.render(text, True, c_WHITE if enable else (100,100,100))
            self.screen.blit(txt, (x+5, py+10))

        draw_btn(20, "Worker(50)")
        draw_btn(130, "Marine(50)")
        draw_btn(240, "Turret(100)", self.round >= 2)
        draw_btn(350, "Tank(300)", self.round >= 3)
        draw_btn(460, "Supply(100)")
        draw_btn(570, "Bunker(150)")
        
        if self.round >= 2 and self.expansion_base and not self.expansion_base.active:
            pygame.draw.rect(self.screen, (0, 100, 200), (700, py, 150, 40))
            self.screen.blit(self.font.render(f"Activate Multi({EXPANSION_COST})", True, c_WHITE), (705, py+10))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            if not self.handle_input(): running = False
            
            keys = pygame.key.get_pressed()
            if self.state == 'ready' and keys[pygame.K_SPACE]: self.start_round()

            if self.state == 'playing': self.update(dt)
            self.draw()
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()