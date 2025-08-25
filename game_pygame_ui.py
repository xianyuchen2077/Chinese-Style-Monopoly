# game_pygame_ui.py
# 使用pygame实现更华丽的中国文化棋盘游戏UI

import pygame
import sys
from game_core import Game, Element, BuildingLevel, EARTHLY_NAMES, SkillLevel
import os
import math

# Color definitions
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)
BLUE = (135, 206, 250)
BG_COLOR = (245, 235, 200)
GRID_COLOR = (80, 80, 80)
PLAYER_COLORS = [(220,20,60), (30,144,255), (34,139,34), (255,140,0)]

# 生肖代表色（用于地皮所有权五角星）
ZODIAC_COLORS = {
    '鼠': (128, 128, 128),
    '牛': (139, 69, 19),
    '虎': (255, 165, 0),
    '兔': (152, 251, 152),
    '龙': (65, 105, 225),
    '蛇': (123, 104, 238),
    '马': (205, 92, 92),
    '羊': (175, 238, 238),
    '猴': (218, 112, 214),
    '鸡': (255, 215, 0),
    '狗': (160, 82, 45),
    '猪': (255, 182, 193),
}

ZODIAC_FILES = {
    '鼠': 'shu.png', '牛': 'niu.png', '虎': 'hu.png', '兔': 'tu.png',
    '龙': 'long.png', '蛇': 'she.png', '马': 'ma.png', '羊': 'yang.png',
    '猴': 'hou.png', '鸡': 'ji.png', '狗': 'gou.png', '猪': 'zhu.png'
}

# Five-element fill colors
ELEMENT_COLORS = {
    Element.GOLD: (255, 215, 0),      # 金 - 金色
    Element.WOOD: (34, 139, 34),      # 木 - 绿色
    Element.WATER: (70, 130, 180),    # 水 - 蓝色
    Element.FIRE: (220, 20, 60),      # 火 - 红色
    Element.EARTH: (160, 82, 45),     # 土 - 棕色
}

# Special tile border colors
SPECIAL_BORDER_COLORS = {
    'start': (255, 140, 0),       # 橙色
    'encounter': (186, 85, 211),  # 紫色
    'hospital': (0, 191, 255),    # 深天蓝
}

# Board parameters
GRID_SIZE = 13
CELL_SIZE = 60      # 稍微减小，避免与顶部/设置重叠
MARGIN = 60         # 更大边距
INFO_WIDTH = 500    # 信息区宽

SKILL_SUMMARY = {
    '鼠': '灵鼠窃运（控向/停留）',
    '牛': '蛮牛冲撞（摧毁/业障）',
    '虎': '猛虎分身（双体/奖惩）',
    '兔': '玉兔疾行（下次步数×2/×3）',
    '龙': '真龙吐息（喷射强制入院）',
    '蛇': '灵蛇隐踪（隐身3回合）',
    '马': '天马守护（减免负面）',
    '羊': '灵羊出窍（灵魂移动）',
    '猴': '灵猴百变（复制技能）',
    '鸡': '金鸡腾翔（飞行落点）',
    '狗': '天狗护体（免疫伤害）',
    '猪': '福猪破障（摧毁建筑-1）',
}

# 技能详细说明
SKILL_DETAILS = {
    '鼠': '灵鼠窃运：指定玩家控制其若干回合移动方向/技能，可反向或停留，对隐身无效。',
    '牛': '蛮牛冲撞：本回合破坏经过路径上所有他人建筑；自身获“业障”（租金+50%）。对土减半。',
    '虎': '猛虎分身：分为两个实体2-3回合，各自独立转盘移动。I级奖励减半，II级伤害减免50%，III级可主动合体且奖励1.5倍。冷却3-4回合。',
    '兔': '玉兔疾行：下一次转盘结果×2，加速期间无法购买地皮。冷却3回合。',
    '龙': '真龙吐息：直线喷火，路径玩家强制入“太医院”，火焰被建筑阻挡。每局最多3次。冷却4回合。',
    '蛇': '灵蛇隐踪：隐身3回合，不可被锁定或影响；期间不能购地和用攻击技能。冷却5回合。',
    '马': '天马守护：常驻被动，负面效果减半，小于1000的扣款免疫，每回合恢复500元气。',
    '羊': '灵羊出窍：灵魂移动3回合，本体留原地；灵魂不触发格效，期间可传送本体。步数减半。冷却5回合。',
    '猴': '灵猴百变：复制一名玩家当前可用技能（一次性），可复制冷却中的技能，使用后原冷却不变。冷却2回合。',
    '鸡': '金鸡腾翔：从自有/公共地皮起飞降落至另一处自有/公共地皮，跨越≤1拐角。冷却3回合。',
    '狗': '天狗护体：被动触发，免疫直接伤害，每触发需跳过下回合，每回合最多2次。',
    '猪': '福猪破障：发射激光摧毁直线路径第一个建筑（等级-1），对金减半，对特殊建筑无效。冷却2回合。',
}

pygame.init()
pygame.font.init()
# 中文字体加载，优先项目目录下字体
def get_chinese_font(size):
    font_paths = [
        os.path.join(os.path.dirname(__file__), 'simhei.ttf'),  # 项目目录下
        'C:/Windows/Fonts/msyh.ttc',  # 微软雅黑
        'C:/Windows/Fonts/simhei.ttf',  # 黑体
        'C:/Windows/Fonts/simsun.ttc',  # 宋体
    ]
    for path in font_paths:
        if os.path.exists(path):
            return pygame.font.Font(path, size)
    return pygame.font.SysFont('Arial', size)  # 兜底英文
FONT = get_chinese_font(28)
FONT_SMALL = get_chinese_font(20)
FONT_BOLD_NAME = get_chinese_font(20)
try:
    FONT_BOLD_NAME.set_bold(True)
except Exception:
    pass
FONT_INDEX = get_chinese_font(16)
try:
    FONT_INDEX.set_bold(True)
except Exception:
    pass

def choose_players_ui():
    """简单的人数/生肖选择界面，返回 (人数, [生肖])"""
    pygame.init()
    screen = pygame.display.set_mode((500, 400))
    font = get_chinese_font(24)
    clock = pygame.time.Clock()

    # 基本数据
    player_count = 2
    zodiac_list = list(ZODIAC_FILES.keys())
    choices = []

    # 控件坐标
    count_rect = pygame.Rect(200, 80, 100, 40)
    ok_rect = pygame.Rect(200, 320, 100, 40)
    zodiac_rects = [pygame.Rect(100 + (i % 6) * 60, 160 + (i // 6) * 60, 50, 50) for i in range(12)]

    while True:
        screen.fill(BG_COLOR)
        # 标题
        title = font.render('请选择人数与生肖', True, BLACK)
        screen.blit(title, title.get_rect(center=(250, 40)))
        # 人数
        pygame.draw.rect(screen, WHITE, count_rect)
        txt = font.render(str(player_count), True, BLACK)
        screen.blit(txt, txt.get_rect(center=count_rect.center))
        # 生肖按钮
        for i, rect in enumerate(zodiac_rects):
            col = (220, 220, 220) if zodiac_list[i] in choices else WHITE
            pygame.draw.rect(screen, col, rect)
            txt = get_chinese_font(18).render(zodiac_list[i], True, BLACK)
            screen.blit(txt, txt.get_rect(center=rect.center))
        # OK按钮
        pygame.draw.rect(screen, GOLD, ok_rect)
        ok_txt = font.render('开始', True, BLACK)
        screen.blit(ok_txt, ok_txt.get_rect(center=ok_rect.center))

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if count_rect.collidepoint(e.pos):
                    player_count = (player_count % 4) + 1   # 1~4循环
                elif ok_rect.collidepoint(e.pos) and len(choices) == player_count:
                    pygame.display.quit()
                    return player_count, choices[:player_count]
                else:
                    for i, rect in enumerate(zodiac_rects):
                        if rect.collidepoint(e.pos):
                            if zodiac_list[i] in choices:
                                choices.remove(zodiac_list[i])
                            elif len(choices) < player_count:
                                choices.append(zodiac_list[i])
        pygame.display.flip()
        clock.tick(60)

def fmt_name(player):
    """返回统一格式：[玩家名]角色名"""
    return f"[{player.name}]{EARTHLY_NAMES[player.zodiac]}"

class GameUI:
    def __init__(self):
        # 动态压缩边距/信息区宽度以适配屏幕，不改变格子大小
        display_info = pygame.display.Info()
        screen_w, screen_h = display_info.current_w, display_info.current_h
        base_grid_w = GRID_SIZE * CELL_SIZE
        base_grid_h = GRID_SIZE * CELL_SIZE
        margin = MARGIN
        desired_h = base_grid_h + 2 * margin
        max_h = int(screen_h * 0.90)
        self.log_scroll = 0
        self.has_rolled = False     # 当前玩家是否已转动罗盘
        self.hovered_tile = None    # 当前悬停地块索引
        self.shu_target = None      # 子鼠技能：被选中的目标玩家
        self.shu_sub_modal = None   # 'select_target' | 'select_dir'
        self.hu_merge_mode   = None        # 'selecting_merge'
        self.hu_merge_cells  = []          # [idx1, idx2]
        self.hu_merge_player = None        # 当前正在合体的虎玩家
        self.ji_sub_modal = None   # 'select_from' | 'select_to'
        self.ji_mode = None        # 'selecting_from' | 'selecting_to'
        self.ji_valid_tiles = []   # 当前可选择的地皮列表

        if desired_h > max_h:
            margin = max(20, (max_h - base_grid_h) // 2)
        info_width = INFO_WIDTH
        desired_w = base_grid_w + 2 * margin + info_width
        max_w = int(screen_w * 0.95)
        if desired_w > max_w:
            info_width = max(260, max_w - (base_grid_w + 2 * margin))
            if base_grid_w + 2 * margin + info_width > max_w:
                margin = max(12, (max_w - base_grid_w - info_width) // 2)
        self.margin = margin
        self.info_width = info_width
        self.width = base_grid_w + self.margin * 2 + self.info_width
        self.height = base_grid_h + self.margin * 2
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('中国文化棋盘游戏')
        self.clock = pygame.time.Clock()
        self.game = Game(['玩家一', '玩家二'], ['鼠', '牛'])    #不要初始化为None，会炸！
        self.selected_skill = None
        self.log = []
        self.tile_props = self._build_tile_props()
        self.base_dir = os.path.dirname(__file__)
        self.player_sprites = self._load_player_sprites()
        self._wheel_surface_cache = None
        # 顶部菜单与模态框
        self.menu_rects = {}
        self.active_modal = None  # 'rules' | 'heroes' | 'settings'
        self.modal_scroll = 0
        self.volume = 0.6
        try:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)
        except Exception:
            pass

    def _build_tile_props(self):
        props = {}
        for tile in self.game.board.tiles:
            color = ELEMENT_COLORS.get(tile.element, WHITE)
            props[tile.idx] = {
                'name': tile.name,
                'element': tile.element,
                'special': tile.special,
                'color': color,
            }
        return props

    def _load_player_sprites(self):
        folder = os.path.join(self.base_dir, 'assets', 'Character')
        os.makedirs(folder, exist_ok=True)
        sprites = []
        for player in self.game.players:
            file_name = ZODIAC_FILES.get(player.zodiac, None)
            path = os.path.join(folder, file_name) if file_name else None
            if path and os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                size = int(CELL_SIZE * 0.8)
                img = pygame.transform.smoothscale(img, (size, size))
                sprites.append(img)
            else:
                sprites.append(None)
        return sprites

    def _draw_player_sprite(self, idx, cx, cy, alpha=255):
        sprite = self.player_sprites[idx] if idx < len(self.player_sprites) else None
        if sprite:
            img = sprite.copy()
            img.set_alpha(alpha)
            self.screen.blit(img, img.get_rect(center=(cx, cy)))
        else:
            color = PLAYER_COLORS[idx % 4]
            radius = int(CELL_SIZE * 0.32)
            pygame.draw.circle(self.screen, (*color, alpha), (cx, cy), radius)

    def draw_board(self):
        # 背景
        self.screen.fill(BG_COLOR)

        # 顶部菜单栏
        self._draw_top_menu()

        # 1. 生成格子编号映射
        grid_map = [[-1 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        idx = 0
        # 上边
        for i in range(GRID_SIZE):
            grid_map[0][i] = idx; idx += 1
        # 右边
        for i in range(1, GRID_SIZE):
            grid_map[i][GRID_SIZE-1] = idx; idx += 1
        # 下边
        for i in range(GRID_SIZE-2, -1, -1):
            grid_map[GRID_SIZE-1][i] = idx; idx += 1
        # 左边
        for i in range(GRID_SIZE-2, 0, -1):
            grid_map[i][0] = idx; idx += 1

        # 2. 画格子
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                idx = grid_map[row][col]
                if idx == -1:
                    continue
                x = self.margin + col * CELL_SIZE
                y = self.margin + row * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                # 填充颜色 & 边框
                tile_info = self.tile_props.get(idx, None)
                base_color = WHITE if tile_info is None else tile_info['color']

                # 寅虎技能模式下合体的暗化效果
                if self.hu_merge_mode == 'selecting_merge':
                    # 暗化整个棋盘
                    overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 180))
                    self.screen.blit(overlay, (0, 0))

                    # 仅高亮主体 & 分身格子
                    for idx in self.hu_merge_cells:
                        pos = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if grid_map[r][c] == idx]
                        if not pos:
                            continue
                        r, c = pos[0]
                        x = self.margin + c * CELL_SIZE
                        y = self.margin + r * CELL_SIZE
                        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                        pygame.draw.rect(self.screen, (0, 255, 0, 180), rect, 5)  # 绿色高亮边框
                # 酉鸡技能模式下的暗化效果
                elif self.ji_mode == 'selecting_to':
                    if idx in [t.idx for t in self.ji_valid_tiles]:
                        # 可选择的地皮保持原色
                        final_color = base_color
                        # 添加高亮边框
                        pygame.draw.rect(self.screen, base_color, rect)
                        pygame.draw.rect(self.screen, (255, 255, 0), rect, 3)  # 金色高亮边框
                    else:
                        # 其他地皮暗化（降低亮度约1/3）
                        dark_color = tuple(int(c * 0.4) for c in base_color)
                        pygame.draw.rect(self.screen, dark_color, rect)
                        pygame.draw.rect(self.screen, GRID_COLOR, rect, 1)
                else:
                    # 正常模式
                    pygame.draw.rect(self.screen, base_color, rect)
                    pygame.draw.rect(self.screen, GRID_COLOR, rect, 1)

                # 特殊边框
                if tile_info and tile_info.get('special'):
                    border_color = SPECIAL_BORDER_COLORS.get(tile_info['special'], (255, 0, 255))
                    pygame.draw.rect(self.screen, border_color, rect, 4)

                # 左上角编号
                pygame.draw.circle(self.screen, BLACK, (x + 13, y + 13), 10)
                idx_text = FONT_INDEX.render(str(idx), True, WHITE)
                self.screen.blit(idx_text, idx_text.get_rect(center=(x + 13, y + 13)))

                # 底部名称
                if tile_info and tile_info.get('name'):
                    name = tile_info['name']
                    max_w = CELL_SIZE - 8
                    size = 18
                    min_size = 10
                    while size >= min_size:
                        f = get_chinese_font(size)
                        try: f.set_bold(True)
                        except: pass
                        test = f.render(name, True, (40, 40, 40))
                        if test.get_width() <= max_w: break
                        size -= 1
                    name_text = test
                    name_rect = name_text.get_rect(midbottom=(x + CELL_SIZE//2, y + CELL_SIZE - 4))
                    self.screen.blit(name_text, name_rect)

                # 所有权五角星
                tile_obj = self.game.board.tiles[idx]
                if tile_obj.owner:
                    star_color = ZODIAC_COLORS.get(tile_obj.owner.zodiac, GOLD)
                    self._draw_star((x + CELL_SIZE - 14, y + 14), 8, star_color)

        # 3. 画玩家棋子
        for i, player in enumerate(self.game.players):
            # 1. 画主体
            pos = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if grid_map[r][c] == player.position]
            if not pos: continue
            row, col = pos[0]
            cx = self.margin + col * CELL_SIZE + CELL_SIZE // 2
            cy = self.margin + row * CELL_SIZE + CELL_SIZE // 2
            self._draw_player_sprite(i, cx, cy, alpha=255)

            # 2. 画分身
            # ========== 寅虎分身绘制 ==========
            if player.zodiac == '虎' and player.has_clone():
                if player.zodiac == '虎' and player.clone_idx is not None:
                    pos2 = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)
                            if grid_map[r][c] == player.clone_idx]
                    if pos2:
                        row2, col2 = pos2[0]
                        cx2 = self.margin + col2*CELL_SIZE + CELL_SIZE//2
                        cy2 = self.margin + row2*CELL_SIZE + CELL_SIZE//2
                        self._draw_player_sprite(i, cx2, cy2, alpha=255)   # 半透明

            # ========== 未羊灵魂出窍半透明灵魂绘制 ==========
            elif player.zodiac == '羊':
                skill = player.skill_mgr.skills['羊']
                soul = skill['soul_pos']
                if soul is not None and soul != player.position:
                    soul_pos = [(r, c) for r in range(GRID_SIZE)
                                        for c in range(GRID_SIZE)
                                        if grid_map[r][c] == soul]
                    if soul_pos:
                        sr, sc = soul_pos[0]
                        sx = self.margin + sc * CELL_SIZE + CELL_SIZE // 2
                        sy = self.margin + sr * CELL_SIZE + CELL_SIZE // 2
                        self._draw_player_sprite(i, sx, sy, alpha=200)

        # 4. === 地皮悬停检测 ===
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_tile = None
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                idx = grid_map[row][col]
                if idx == -1: continue
                x = self.margin + col * CELL_SIZE
                y = self.margin + row * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                if rect.collidepoint(mouse_pos):
                    self.hovered_tile = idx
                    break   # 找到一块即可


    def draw_info(self):
        # Info area background
        info_x = GRID_SIZE * CELL_SIZE + self.margin * 2
        pygame.draw.rect(self.screen, (230,230,250), (info_x, 0, self.info_width, self.height))
        # Player info boxes（两列布局，内容自适应，技能悬停提示，当前回合高亮）
        box_pad = 12
        col_gap = 12
        cols = 2
        col_w = (self.info_width - (cols + 1) * col_gap) // cols
        row_h = 210

        # 按钮集合
        btn_y = max(300, 20 + 2 * (row_h + col_gap))

        # 罗盘按钮
        cur_player = self.game.players[self.game.current_player_idx]
        is_controlled = 'shu_control' in cur_player.status and cur_player.status['shu_control'].get('direction') == 'stay'
        can_spin = not self.has_rolled and cur_player.can_move and not is_controlled
        color_spin = (255, 222, 173) if can_spin else (200, 200, 200)
        text_spin  = (139, 69, 19)   if can_spin else (120, 120, 120)
        self.spin_btn_rect = pygame.Rect(info_x+24, btn_y, 140, 44)
        pygame.draw.rect(self.screen, color_spin, self.spin_btn_rect, border_radius=12)
        self.screen.blit(FONT.render('天命罗盘', True, text_spin),
                        (self.spin_btn_rect.x+6, self.spin_btn_rect.y+4))

        # 技能按钮
        cur_player = self.game.players[self.game.current_player_idx]
        can_skill = (
            not self.has_rolled
            and cur_player.skill_mgr.can_use_active_skill()
            and not (cur_player.status.get('shu_control', {}).get('direction') == 'stay')
        )
        color_skill = (176, 224, 230) if can_skill else (200, 200, 200)
        text_skill  = (25, 25, 112)   if can_skill else (120, 120, 120)
        self.skill_btn_rect = pygame.Rect(info_x+24+160, btn_y, 140, 44)
        pygame.draw.rect(self.screen, color_skill, self.skill_btn_rect, border_radius=12)
        skill_text = '灵魂归位' if cur_player.zodiac == '羊' and cur_player.skill_mgr.skills['羊']['soul_pos'] else '符咒潜能'
        self.screen.blit(FONT.render(skill_text, True, text_skill),
                        (self.skill_btn_rect.x+6, self.skill_btn_rect.y+4))

        # === 第二行：购地 | 加盖 | 进阶 ===
        buy_y = btn_y + 56
        btn_w = 90          # 每个按钮宽度
        gap   = 12          # 按钮间距
        start_x = info_x + 24
        cur_player = self.game.players[self.game.current_player_idx]

        # 1. 购地
        self.buy_btn_rect = pygame.Rect(start_x, buy_y, btn_w, 40)
        buy_ok = self._can_buy_now(cur_player)
        color_buy = (208,240,192) if buy_ok else (200,200,200)
        text_buy  = (0,100,0)     if buy_ok else (120,120,120)
        pygame.draw.rect(self.screen, color_buy, self.buy_btn_rect, border_radius=10)
        self.screen.blit(
            FONT_SMALL.render('购地', True, text_buy),
            (
                self.buy_btn_rect.x + (self.buy_btn_rect.width // 2) - (FONT_SMALL.size('购地')[0] // 2),
                self.buy_btn_rect.y + (self.buy_btn_rect.height // 2) - (FONT_SMALL.size('购地')[1] // 2)
            )
        )

        # 2. 加盖
        self.upgrade_btn_rect = pygame.Rect(start_x + btn_w + gap, buy_y, btn_w, 40)
        up_ok = self._can_upgrade_now(cur_player)
        color_up = (255,228,196) if up_ok else (200,200,200)
        text_up  = (139,69,19)   if up_ok else (120,120,120)
        pygame.draw.rect(self.screen, color_up, self.upgrade_btn_rect, border_radius=10)
        self.screen.blit(
            FONT_SMALL.render('加盖', True, text_up),
            (
                self.upgrade_btn_rect.x + (self.upgrade_btn_rect.width // 2) - (FONT_SMALL.size('加盖')[0] // 2),
                self.upgrade_btn_rect.y + (self.upgrade_btn_rect.height // 2) - (FONT_SMALL.size('加盖')[1] // 2)
            )
        )

        # 3. 进阶（技能升级）
        self.advance_btn_rect = pygame.Rect(start_x + (btn_w + gap) * 2, buy_y, btn_w, 40)
        can_adv = self._can_advance_skill(cur_player)   # 暂未开发进阶功能
        color_advance = (220,220,220) if can_adv else (200,200,200)
        text_advance  = (100,50,50)   if can_adv else (120,120,120)
        pygame.draw.rect(self.screen, color_advance, self.advance_btn_rect, border_radius=10)
        self.screen.blit(
            FONT_SMALL.render('进阶', True, text_advance),
            (
                self.advance_btn_rect.x + (self.advance_btn_rect.width // 2) - (FONT_SMALL.size('进阶')[0] // 2),
                self.advance_btn_rect.y + (self.advance_btn_rect.height // 2) - (FONT_SMALL.size('进阶')[1] // 2)
            )
        )

        # 回合结束按钮
        end_y = btn_y
        color_end = (150, 150, 200)
        text_end = (115, 251, 253)
        self.end_turn_btn_rect = pygame.Rect(info_x + 350, end_y, 100, 100)
        pygame.draw.rect(self.screen, color_end, self.end_turn_btn_rect, border_radius=8)
        # 大号加粗字体
        big_font = get_chinese_font(22)
        try:
            big_font.set_bold(True)
        except Exception:
            pass
        # 分两行渲染
        line1 = big_font.render('回合', True, text_end)
        line2 = big_font.render('结束', True, text_end)
        # 居中放置
        center_x = self.end_turn_btn_rect.centerx
        center_y = self.end_turn_btn_rect.centery
        self.screen.blit(line1, line1.get_rect(center=(center_x, center_y - 12)))
        self.screen.blit(line2, line2.get_rect(center=(center_x, center_y + 12)))

        def render_fit(text, max_w, color, bold=False, base=20, min_size=12):
            for size in range(base, min_size - 1, -1):
                f = get_chinese_font(size)
                try:
                    f.set_bold(bold)
                except Exception:
                    pass
                surf = f.render(text, True, color)
                if surf.get_width() <= max_w:
                    return surf
            f = get_chinese_font(min_size)
            try:
                f.set_bold(bold)
            except Exception:
                pass
            return f.render(text, True, color)

        for idx, player in enumerate(self.game.players[:4]):
            col = idx % cols
            row = idx // cols
            bx = info_x + col_gap + col * (col_w + col_gap)
            by = 20 + row * (row_h + col_gap)
            box_rect = pygame.Rect(bx, by, col_w, row_h)
            is_active = (idx == self.game.current_player_idx)
            base_color = (250,250,255)
            glow = pygame.Surface((col_w, row_h), pygame.SRCALPHA)
            if is_active:
                pygame.draw.rect(glow, (255,255,200,90), glow.get_rect(), border_radius=12)
                self.screen.blit(glow, (bx, by))
            pygame.draw.rect(self.screen, base_color, box_rect, border_radius=10)
            pygame.draw.rect(self.screen, (180,180,210), box_rect, width=2, border_radius=10)
            # Title
            title = f"{player.name}（{player.zodiac}）"
            title_surf = render_fit(title, col_w - 2*box_pad, PLAYER_COLORS[idx%4], bold=True, base=20)
            self.screen.blit(title_surf, (bx + box_pad, by + box_pad))
            # Lines
            y0 = by + box_pad + title_surf.get_height() + 6
            line_gap = 6
            skill_short = SKILL_SUMMARY.get(player.zodiac, '')
            if '（' in skill_short:
                skill_short = skill_short.split('（')[0]

            # 正确获取冷却时间
            cd = 0
            if hasattr(player, 'skill_mgr') and player.zodiac in player.skill_mgr.skills:
                cd = player.skill_mgr.skills[player.zodiac]['cooldown']

            # 正确获取状态信息
            positive_states = []
            negative_states = []
            if hasattr(player, 'status'):
                if 'shield' in player.status: positive_states.append('护盾')
                if 'tiger_split' in player.status: positive_states.append('分身')
                if 'skip_turns' in player.status: negative_states.append('休息')
                if 'karma' in player.status: negative_states.append('业障')
                if 'shu_control' in player.status: negative_states.append('被控')

            status_parts = positive_states + negative_states
            attr_text = f"状态：{' '.join(status_parts)}" if status_parts else "状态：正常"

            items = [
                (f"金币：{player.money}", BLACK),
                (f"位置：{player.position}", BLACK),
                (f"冷却：{cd}", (100,100,100)),
                (f"{attr_text}", (100,100,100)) if attr_text else ("", (0,0,0)),
                (f"技能：{skill_short}", (64,64,64)),
            ]
            skill_rect = None
            for t, c in items:
                surf = render_fit(t, col_w - 2*box_pad, c, bold=False, base=18, min_size=12)
                pos = (bx + box_pad, y0)
                self.screen.blit(surf, pos)
                if t.startswith('技能：'):
                    skill_rect = pygame.Rect(pos[0], pos[1], surf.get_width(), surf.get_height())
                y0 += surf.get_height() + line_gap

            # 鼠标悬停技能提示
            if skill_rect and skill_short:
                mouse_pos = pygame.mouse.get_pos()
                if skill_rect.collidepoint(mouse_pos):
                    detail = SKILL_DETAILS.get(player.zodiac, '')
                    self._draw_tooltip(mouse_pos, detail, max_w=260)

        # === 日志区域 ===
        log_rect = pygame.Rect(info_x + 16, self.height - 280,
                            self.info_width - 32, 260)
        pygame.draw.rect(self.screen, (245, 245, 245), log_rect, border_radius=8)

        log_font = get_chinese_font(18)
        line_h = log_font.get_linesize()

        # 计算可显示行数
        visible_lines = log_rect.height // line_h
        total_lines = len(self.log)
        # 限制滚动范围
        self.log_scroll = max(0, min(self.log_scroll, total_lines - visible_lines))

        # 绘制可见日志
        y = log_rect.y + 4
        for line in self.log[self.log_scroll:self.log_scroll + visible_lines]:
            self.screen.blit(log_font.render(line, True, (80, 80, 80)),
                            (log_rect.x + 8, y))
            y += line_h

        # 绘制滚动条（仅当日志过多）
        if total_lines > visible_lines:
            bar_h = log_rect.height * visible_lines // total_lines
            bar_y = log_rect.y + (self.log_scroll / (total_lines - visible_lines)) * \
                    (log_rect.height - bar_h)
            pygame.draw.rect(self.screen, (180, 180, 180),
                            (log_rect.right - 12, bar_y, 8, bar_h))

        # === 地皮悬停详情弹窗 ===
        if self.hovered_tile is not None:
            self._draw_tile_tooltip(self.hovered_tile, pygame.mouse.get_pos())

        # 模态框覆盖
        if self.active_modal:
            self._draw_modal_overlay()

    def _draw_tile_tooltip(self, idx, mouse_pos):
        tile = self.game.board.tiles[idx]
        if tile.special:          # 特殊格子不显示详情
            return

        # 基本信息
        name  = tile.name
        elem  = tile.element.value if tile.element else '无'
        price = tile.price
        level = tile.level.value
        upgrade_cost = self.game.upgrade_cost(tile) if level < 4 else 0

        # 各级租金（按 rules.md）
        rent_empty = int(price * 0.2)
        rent_hut   = int(price * 0.5)
        rent_tile  = int(price * 1.2)
        rent_inn   = int(price * 2.0)
        rent_pal   = int(price * 3.5)

        # 特殊效果
        effects = {
            Element.GOLD: '宫殿租金+20%',
            Element.WOOD: '每回合恢复500元气',
            Element.WATER: '过起点奖励+1000',
            Element.FIRE: '租金×2 但火灾几率20%',
            Element.EARTH: '完全免疫破坏'
        }
        effect = effects.get(tile.element, '无')

        # 抵押
        mortgage = price // 2

        # 文本列表
        lines = [
            f'【{name}】',
            f'五行: {elem}',
            f'等级: {level}/4',
            f'售价: {price} 金币',
            f'升级费: {upgrade_cost} 金币' if upgrade_cost else '',
            f'租金:',
            f'  空地: {rent_empty}',
            f'  茅屋: {rent_hut}',
            f'  瓦房: {rent_tile}',
            f'  客栈: {rent_inn}',
            f'  宫殿: {rent_pal}',
            f'抵押: {mortgage} 金币',
            f'特效: {effect}'
        ]
        lines = [l for l in lines if l]

        # 绘制
        font = get_chinese_font(16)
        line_h = font.get_linesize() + 2
        pad = 8
        max_w = max(font.render(l, True, (0,0,0)).get_width() for l in lines)
        tip_w = max_w + pad * 2
        tip_h = len(lines) * line_h + pad * 2

        # 防止出界
        px = min(mouse_pos[0] + 12, self.width - tip_w - 6)
        py = min(mouse_pos[1] + 12, self.height - tip_h - 6)
        rect = pygame.Rect(px, py, tip_w, tip_h)

        pygame.draw.rect(self.screen, (255, 255, 240), rect, border_radius=8)
        pygame.draw.rect(self.screen, (180, 180, 150), rect, 1, border_radius=8)

        y = py + pad
        for line in lines:
            self.screen.blit(font.render(line, True, (30, 30, 30)), (px + pad, y))
            y += line_h

    def _scroll_to_bottom(self):
        """把日志滚动条拉到最底，始终显示最新"""
        log_font = get_chinese_font(18)
        visible_lines = 260 // log_font.get_linesize()
        self.log_scroll = max(0, len(self.log) - visible_lines)

    def _get_clicked_tile(self, pos):
        """根据点击位置获取地皮索引"""
        # 生成格子编号映射（与draw_board中的逻辑一致）
        grid_map = [[-1 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        idx = 0
        # 上边
        for i in range(GRID_SIZE):
            grid_map[0][i] = idx; idx += 1
        # 右边
        for i in range(1, GRID_SIZE):
            grid_map[i][GRID_SIZE-1] = idx; idx += 1
        # 下边
        for i in range(GRID_SIZE-2, -1, -1):
            grid_map[GRID_SIZE-1][i] = idx; idx += 1
        # 左边
        for i in range(GRID_SIZE-2, 0, -1):
            grid_map[i][0] = idx; idx += 1

        # 检查点击位置
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                idx = grid_map[row][col]
                if idx == -1: continue
                x = self.margin + col * CELL_SIZE
                y = self.margin + row * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                if rect.collidepoint(pos):
                    return idx
        return None

    def handle_click(self, pos):
        # 模态框点击优先
        if self.active_modal:
            # 点击遮罩关闭或处理设置交互
            if self._modal_handle_click(pos):
                return
            self.active_modal = None
            return
        # 菜单点击
        for key, rect in self.menu_rects.items():
            if rect.collidepoint(pos):
                self.active_modal = key
                self.modal_scroll = 0
                return

        cur = self.game.players[self.game.current_player_idx]
        # ---------------- 罗盘按钮 ----------------
        if self.spin_btn_rect.collidepoint(pos):
            # 检查是否被子鼠控制停留，如果是则直接返回，不执行任何操作
            if 'shu_control' in cur.status and cur.status['shu_control'].get('direction') == 'stay':
                # 添加提示信息
                self.log.append(f'{fmt_name(cur)} 被【灵鼠窃运】禁锢，无法行动')
                self._scroll_to_bottom()
                return  # 直接返回，不执行后续的罗盘逻辑

            if not self.has_rolled:        # 本回合尚未转动
                self.spin_wheel()
                self.has_rolled = True     # 标记已转动
            else:                          # 已转动，自动进入下一位
                self.log.append(f'{fmt_name(cur)} 本回合已转动罗盘')
                self._scroll_to_bottom()

        # ---------------- 技能按钮 ----------------
        elif self.skill_btn_rect.collidepoint(pos):
            cur = self.game.players[self.game.current_player_idx]

            # 根据生肖自动选择目标逻辑
            if cur.zodiac == '鼠':
                # 子鼠需要弹窗选目标
                if cur.skill_mgr.skills['鼠']['cooldown'] == 0:
                    self.shu_sub_modal = 'select_target'
                    self.active_modal = 'shu_skill'
                else:
                    self.log.append(f'{fmt_name(cur)} 【灵鼠窃运】冷却中')
            elif cur.zodiac == '牛':
                if self.has_rolled:
                    self.log.append(f'{fmt_name(cur)} 本回合已转动罗盘，无法再使用技能')
                    self._scroll_to_bottom()
                    return
                ok, msg = cur.skill_mgr.use_active_skill(game=self.game)
                self.log.append(msg)
                if ok:
                    level = cur.skill_mgr.skills['牛']['level']
                    if level == SkillLevel.I:
                        self.log.append("获得业障状态2回合，租金支出+50%")
                    elif level == SkillLevel.II:
                        self.log.append("获得业障状态1回合，终点50%几率额外摧毁")
                    else:
                        self.log.append("无业障，终点100%摧毁他人建筑")
            elif cur.zodiac == '虎':
                # 检查是否分身
                if hasattr(cur, 'skill_mgr') and cur.skill_mgr.skills['虎']['split_turns'] > 0:
                    # 罗盘已转完，准备进入合体高亮
                    if cur.skill_mgr.skills['虎']['split_turns'] == 0:
                        self.hu_merge_player = cur
                        self.hu_merge_cells  = [cur.position, cur.get_clone_position()]
                        self.hu_merge_mode   = 'selecting_merge'
                        self.log.append("请选择合体位置（点击高亮格子）")
                        self._scroll_to_bottom()
                    else:
                        remaining = cur.skill_mgr.skills['虎']['split_turns']
                        self.log.append(f'{fmt_name(cur)} 已处于分身状态，剩余{remaining}回合')
                        self._scroll_to_bottom()
                    return  # 让转盘/合体流程接管

                # 未分身则发动技能
                if self.has_rolled:
                    self.log.append(f'{fmt_name(cur)} 本回合已转动罗盘，无法再使用技能')
                    self._scroll_to_bottom()
                    return

                ok, msg = cur.skill_mgr.use_active_skill(game=self.game)
                self.log.append(msg)
                if ok:
                    level = cur.skill_mgr.skills['虎']['level']
                    duration = 2 if level == SkillLevel.I else 3
                    effects = {
                        SkillLevel.I: "奖励减半，无伤害减免",
                        SkillLevel.II: "伤害减免50%，奖励正常",
                        SkillLevel.III: "伤害减免80%，奖励1.5倍，回合结束后点击高亮格子合体"
                    }
                    self.log.append(f"分身效果：{effects[level]}，持续{duration}回合")
            elif cur.zodiac == '兔':
                # 卯兔无目标
                ok, msg = cur.skill_mgr.use_active_skill()
                self.log.append(msg)
            elif cur.zodiac == '羊':
                # 未羊的技能只能在转动罗盘前使用
                if self.has_rolled:
                    self.log.append(f'{fmt_name(cur)} 本回合已转动罗盘，无法再使用技能')
                    self._scroll_to_bottom()
                    return
                # 未羊无目标
                ok, msg = cur.skill_mgr.use_active_skill()
                self.log.append(msg)
            elif cur.zodiac == '鸡':
                # 酉鸡的技能只能在转动罗盘前使用
                if self.has_rolled:
                    self.log.append(f'{fmt_name(cur)} 本回合已转动罗盘，无法再使用技能')
                    self._scroll_to_bottom()
                    return
                # 酉鸡无目标
                if cur.skill_mgr.skills['鸡']['cooldown'] == 0:
                    self._start_ji_landing_selection()
                else:
                    self.log.append(f'{fmt_name(cur)} 【金鸡腾翔】冷却中')
            else:
                self.log.append(f'{fmt_name(cur)} 暂无可用主动技能')
            self._scroll_to_bottom()
            self.draw_info()    # 立即更新

        # ---------------- 升级按钮 ----------------
        elif hasattr(self, 'upgrade_skill_btn_rect') and self.upgrade_btn_rect.collidepoint(pos):
            if cur.zodiac == '鼠':
                if cur.skill_mgr.upgrade_shu():
                    self.log.append(f'{fmt_name(cur)} 升级【灵鼠窃运】成功！')
                else:
                    self.log.append(f'{fmt_name(cur)} 灵气不足或条件未满足')
            elif cur.zodiac == '牛':
                if cur.skill_mgr.upgrade_niu():
                    level = cur.skill_mgr.skills['牛']['level']
                    self.log.append(f'{fmt_name(cur)} 升级【蛮牛冲撞】至{level.name}级成功！')
                    upgraded = True
            elif cur.zodiac == '虎':
                if cur.skill_mgr.upgrade_hu():
                    level = cur.skill_mgr.skills['虎']['level']
                    level_name = {SkillLevel.II: 'II', SkillLevel.III: 'III'}[level]
                    self.log.append(f'{fmt_name(cur)} 升级【猛虎分身】至{level_name}级成功！')
                    upgraded = True
            elif cur.zodiac == '兔':
                if cur.skill_mgr.upgrade_tu():
                    self.log.append(f'{fmt_name(cur)} 升级【玉兔疾行】成功！')
                    upgraded = True
            elif cur.zodiac == '鸡':
                if cur.skill_mgr.upgrade_ji():
                    self.log.append(f'{fmt_name(cur)} 升级【金鸡腾翔】成功！')
                    upgraded = True
            if not upgraded:
                self.log.append(f'{fmt_name(cur)} 灵气不足或条件未满足')
            self._scroll_to_bottom()
            self.draw_info()    # 立即更新

        elif hasattr(self, 'buy_btn_rect') and self.buy_btn_rect.collidepoint(pos):
            if self._can_buy_now(cur) and self.game.buy_property(cur):
                while self.game.log:
                    self.log.append(self.game.log.pop(0))
                    self._scroll_to_bottom()
            self.draw_info()    # 立即更新

        elif hasattr(self, 'upgrade_btn_rect') and self.upgrade_btn_rect.collidepoint(pos):
            if self._can_upgrade_now(cur) and self.game.upgrade_building(cur):
                while self.game.log:
                    self.log.append(self.game.log.pop(0))
                    self._scroll_to_bottom()
            self.draw_info()    # 立即更新

        # ---------------- 回合结束按钮 ----------------
        elif hasattr(self, 'end_turn_btn_rect') and self.end_turn_btn_rect.collidepoint(pos):
            self.game.next_turn()
            self.has_rolled = False
            # 把游戏日志同步到 UI 日志
            while self.game.log:
                self.log.append(self.game.log.pop(0))
            self._scroll_to_bottom()
            self.draw_info()

        # ---------------- 酉鸡技能：地皮点击处理 ----------------
        if self.ji_mode == 'selecting_to':
            clicked_tile = self._get_clicked_tile(pos)
            if clicked_tile is not None and clicked_tile in [t.idx for t in self.ji_valid_tiles]:
                self._handle_ji_landing_click(clicked_tile)
                return

    def spin_wheel(self):
        player = self.game.players[self.game.current_player_idx]

        dice_result = self.game.spin_wheel()

        if not player.can_move:
            reason = "被【灵鼠窃运】禁锢，无法行动" if player.status.get('shu_control', {}).get('direction') == 'stay' else "无法移动"
            self.log.append(f'{fmt_name(player)} {reason}')
            self._scroll_to_bottom()
            return

        if player.status.get('skip_turns', 0) > 0:
            player.status['skip_turns'] -= 1
            self.log.append(f'{fmt_name(player)} 休息中，跳过回合。')
            self._scroll_to_bottom()
            self.game.next_turn()   # 休息回合，无法进行任何操作
            return

        # 动画
        self._animate_wheel(dice_result)

        # 通过Player的move_step方法处理方向和控制效果
        final_steps = player.move_step(dice_result)

        # 记录移动前的位置用于日志
        old_pos = player.position

        # 执行移动
        new_pos = self.game.move_player(player, final_steps)

        # 详细的移动日志
        if final_steps == 0:
            if player.zodiac == '羊' and player.skill_mgr.skills['羊']['soul_pos'] is not None:
                self.log.append(f'{fmt_name(player)} 本体留在原地')
            else:
                self.log.append(f'{fmt_name(player)} 被迫停留在原地')
        elif final_steps > 0:
            self.log.append(f'{fmt_name(player)} 顺时针移动{final_steps}步：{old_pos} → {new_pos}')
        else:
            self.log.append(f'{fmt_name(player)} 逆时针移动{abs(final_steps)}步：{old_pos} → {new_pos}')
        self._scroll_to_bottom()

        # 将游戏日志同步到UI日志
        while self.game.log:
            self.log.append(self.game.log.pop(0))
        self._scroll_to_bottom()

        # 触发格子效果
        self.game.after_trigger(player)
        while self.game.log:
            self.log.append(self.game.log.pop(0))
        self._scroll_to_bottom()

    def use_skill(self):
        cur = self.game.players[self.game.current_player_idx]
        z = cur.zodiac
        tip = SKILL_SUMMARY.get(z, '（详见规则）')
        self.log.append(f'[{cur.name}] {z}：{tip}')
        self._scroll_to_bottom()

    def _create_wheel_surface(self, radius):
        # 预渲染一个10等分转盘，丰富配色
        size = radius * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (radius, radius)
        colors = [
            (255, 215, 0), (135, 206, 250), (255, 182, 193), (152, 251, 152), (221, 160, 221),
            (240, 230, 140), (176, 224, 230), (255, 160, 122), (173, 216, 230), (250, 250, 210)
        ]
        for i in range(10):
            start_ang = i * (2 * math.pi / 10)
            end_ang = (i + 1) * (2 * math.pi / 10)
            seg_color = colors[i % len(colors)]
            points = [center]
            steps = 30  # 扇区边缘更平滑
            for s in range(steps + 1):
                a = start_ang + (end_ang - start_ang) * (s / steps)
                px = center[0] + radius * math.cos(a)
                py = center[1] + radius * math.sin(a)
                points.append((px, py))
            pygame.draw.polygon(surf, seg_color, points)
        # 外圈描边
        pygame.draw.circle(surf, (60, 60, 60), center, radius, 4)
        # 内圆装饰
        pygame.draw.circle(surf, (40, 40, 40), center, radius * 0.15)
        # 数字不绘制在这里，而是在动画时叠加
        return surf

    def _animate_wheel(self, result_num):
        # 模态动画：遮罩 + 转盘旋转减速
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        radius = int(min(self.width, self.height) * 0.28)
        if not self._wheel_surface_cache or self._wheel_surface_cache.get_width() != radius * 2:
            self._wheel_surface_cache = self._create_wheel_surface(radius)
        angle = 0.0
        speed = 24.0
        decel = 0.98
        min_speed = 0.8
        while speed > min_speed:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            angle = (angle + speed) % 360.0
            speed *= decel
            self.screen.blit(overlay, (0,0))
            rotated = pygame.transform.rotozoom(self._wheel_surface_cache, angle, 1.0)
            rect = rotated.get_rect(center=(self.width//2, self.height//2))
            self.screen.blit(rotated, rect)
            # 绘制竖直数字（始终保持向上）
            f = get_chinese_font(26)
            for i in range(10):
                mid_ang = (i + 0.5) * (2 * math.pi / 10)
                # 计算未旋转前的坐标
                rx = radius * 0.65 * math.cos(mid_ang)
                ry = radius * 0.65 * math.sin(mid_ang)
                # 应用旋转变换
                cos_a = math.cos(math.radians(-angle))
                sin_a = math.sin(math.radians(-angle))
                tx = self.width // 2 + (rx * cos_a - ry * sin_a)
                ty = self.height // 2 + (rx * sin_a + ry * cos_a)
                num = str(i + 1)
                ts = f.render(num, True, (25, 25, 25))
                rect = ts.get_rect(center=(tx, ty))
                self.screen.blit(ts, rect)
            # 顶部高亮扇形
            self._draw_top_highlight(radius)
            # 装饰指针
            self._draw_pointer(radius)
            pygame.display.flip()
            self.clock.tick(60)
        # 计算与结果对齐的角度，使指针正好指向结果扇区中心
        # 我们约定数字1在顶部右侧第一个扇区，顺时针递增。
        # 指针固定朝上（-90度），因此需要旋转角度使得目标扇区中心到达顶部。
        sector_angle = 360.0 / 10.0
        # 令0度在右侧，-90度在上方。目标中心角：result_num扇区的中心相对右侧角度
        target_center_deg = (result_num - 0.5) * sector_angle  # 从右侧顺时针
        # 目标是让该中心到达-90度，故需要总旋转角≈(target_center_deg + 90)
        final_rotation = (target_center_deg + 90.0) % 360.0
        # 快速旋转到位的微动画
        for _ in range(12):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            angle = (angle + (final_rotation - angle) * 0.35) % 360.0
            self.screen.blit(overlay, (0,0))
            rotated = pygame.transform.rotozoom(self._wheel_surface_cache, angle, 1.0)
            rect = rotated.get_rect(center=(self.width//2, self.height//2))
            self.screen.blit(rotated, rect)
            # 绘制竖直数字（始终保持向上）
            f = get_chinese_font(26)
            for i in range(10):
                mid_ang = (i + 0.5) * (2 * math.pi / 10)
                # 计算未旋转前的坐标
                rx = radius * 0.65 * math.cos(mid_ang)
                ry = radius * 0.65 * math.sin(mid_ang)
                # 应用旋转变换
                cos_a = math.cos(math.radians(-angle))
                sin_a = math.sin(math.radians(-angle))
                tx = self.width // 2 + (rx * cos_a - ry * sin_a)
                ty = self.height // 2 + (rx * sin_a + ry * cos_a)
                num = str(i + 1)
                ts = f.render(num, True, (25, 25, 25))
                rect = ts.get_rect(center=(tx, ty))
                self.screen.blit(ts, rect)
            self._draw_top_highlight(radius)
            self._draw_pointer(radius)
            pygame.display.flip()
            self.clock.tick(60)
        # 停留显示结果
        for _ in range(36):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            self.screen.blit(overlay, (0,0))
            rotated = pygame.transform.rotozoom(self._wheel_surface_cache, angle, 1.0)
            rect = rotated.get_rect(center=(self.width//2, self.height//2))
            self.screen.blit(rotated, rect)
            # 绘制竖直数字（始终保持向上）
            f = get_chinese_font(26)
            for i in range(10):
                mid_ang = (i + 0.5) * (2 * math.pi / 10)
                # 计算未旋转前的坐标
                rx = radius * 0.65 * math.cos(mid_ang)
                ry = radius * 0.65 * math.sin(mid_ang)
                # 应用旋转变换
                cos_a = math.cos(math.radians(-angle))
                sin_a = math.sin(math.radians(-angle))
                tx = self.width // 2 + (rx * cos_a - ry * sin_a)
                ty = self.height // 2 + (rx * sin_a + ry * cos_a)
                num = str(i + 1)
                ts = f.render(num, True, (25, 25, 25))
                rect = ts.get_rect(center=(tx, ty))
                self.screen.blit(ts, rect)
            self._draw_top_highlight(radius)
            self._draw_pointer(radius)
            res = f"步数 {result_num}"
            f = get_chinese_font(36)
            try:
                f.set_bold(True)
            except Exception:
                pass
            ts = f.render(res, True, (255,255,255))
            self.screen.blit(ts, ts.get_rect(center=(self.width//2, self.height//2)))
            pygame.display.flip()
            self.clock.tick(60)

    def _draw_top_menu(self):
        """菜单栏绘制"""
        bar_h = 36
        pygame.draw.rect(self.screen, (50,50,70), (0, 0, self.width, bar_h))
        items = [('rules', '规则'), ('heroes', '英雄'), ('settings', '设置')]
        x = 12
        self.menu_rects = {}
        for key, label in items:
            f = get_chinese_font(20)  # 字体小一号
            surf = FONT_SMALL.render(label, True, (255,255,255))
            rect = pygame.Rect(x, 4, surf.get_width()+20, bar_h-8)
            pygame.draw.rect(self.screen, (80,80,110), rect, border_radius=8)
            # 居中
            self.screen.blit(surf, surf.get_rect(center=rect.center))
            self.menu_rects[key] = rect
            x += rect.width + 8

    def _draw_tooltip(self, mouse_pos, text, max_w=260):
        tip_font = get_chinese_font(16)
        # 逐字换行
        lines = []
        remaining = text
        while remaining:
            cut = ''
            for i in range(1, len(remaining)+1):
                s = tip_font.render(remaining[:i], True, (30,30,30))
                if s.get_width() > max_w - 12:
                    cut = remaining[:i-1]
                    remaining = remaining[i-1:]
                    break
            if not cut:
                cut = remaining
                remaining = ''
            lines.append(cut)
        line_h = tip_font.render('测', True, (0,0,0)).get_height()
        tip_w = min(max_w, max(tip_font.render(l, True, (0,0,0)).get_width() for l in lines) + 12)
        tip_h = line_h * len(lines) + 12
        px = min(mouse_pos[0] + 12, self.width - tip_w - 6)
        py = min(mouse_pos[1] + 12, self.height - tip_h - 6)
        tip_rect = pygame.Rect(px, py, tip_w, tip_h)
        pygame.draw.rect(self.screen, (255, 255, 240), tip_rect, border_radius=6)
        pygame.draw.rect(self.screen, (180, 180, 150), tip_rect, 1, border_radius=6)
        ty = py + 6
        for line in lines:
            self.screen.blit(tip_font.render(line, True, (30,30,30)), (px + 6, ty))
            ty += line_h

    def _draw_pointer(self, radius):
        tip_x = self.width//2
        tip_y = self.height//2 - radius + 40
        base_w = 16
        # 指针主体
        pygame.draw.polygon(self.screen, (255,215,0), [(tip_x, tip_y), (tip_x-base_w, tip_y-28), (tip_x+base_w, tip_y-28)])
        pygame.draw.polygon(self.screen, (139,69,19), [(tip_x, tip_y), (tip_x-base_w, tip_y-28), (tip_x+base_w, tip_y-28)], 2)
        pygame.draw.circle(self.screen, (255,215,0), (tip_x, tip_y-40), 13)
        pygame.draw.circle(self.screen, (139,69,19), (tip_x, tip_y-40), 13, 2)

    def _draw_top_highlight(self, radius):
        # 顶部扇形高亮
        highlight = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cx = self.width//2
        cy = self.height//2
        ang_span = math.pi * 2 / 10
        start = -math.pi/2 - ang_span/2
        end = -math.pi/2 + ang_span/2
        points = [(cx, cy)]
        steps = 24
        r = radius
        for s in range(steps+1):
            a = start + (end - start) * (s / steps)
            points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        pygame.draw.polygon(highlight, (255,255,255,60), points)
        self.screen.blit(highlight, (0,0))

    def _draw_modal_overlay(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        self.screen.blit(overlay, (0,0))
        w = int(self.width * 0.66)
        h = int(self.height * 0.7)
        x = (self.width - w)//2
        y = (self.height - h)//2
        panel = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, (250,250,255), panel, border_radius=12)
        pygame.draw.rect(self.screen, (150,150,200), panel, 2, border_radius=12)
        title_map = {'rules': '规则', 'heroes': '英雄', 'settings': '设置'}
        key = self.active_modal if isinstance(self.active_modal, str) else ''
        title = title_map.get(key, '')
        self.screen.blit(FONT.render(title, True, (60,60,90)), (x+16, y+10))
        content_rect = pygame.Rect(x+16, y+50, w-32, h-66)
        if self.active_modal in ('rules', 'heroes'):
            self._render_modal_text(content_rect, self._load_modal_text(self.active_modal))
        elif self.active_modal == 'settings':
            self._render_settings(content_rect)
        elif self.active_modal == 'shu_skill':
            self._render_shu_skill_modal(content_rect)

    def _render_modal_text(self, rect, text):
        font = get_chinese_font(18)
        lines = []
        for raw_line in text.split('\n'):
            remaining = raw_line
            while remaining:
                cut = ''
                for i in range(1, len(remaining)+1):
                    s = font.render(remaining[:i], True, (30,30,30))
                    if s.get_width() > rect.width - 8:
                        cut = remaining[:i-1]
                        remaining = remaining[i-1:]
                        break
                if not cut:
                    cut = remaining
                    remaining = ''
                lines.append(cut)
        line_h = font.render('测', True, (0,0,0)).get_height() + 4
        max_lines = rect.height // line_h
        start = max(0, self.modal_scroll)
        lines_to_draw = lines[start:start+max_lines]
        y = rect.y
        for ln in lines_to_draw:
            self.screen.blit(font.render(ln, True, (30,30,30)), (rect.x, y))
            y += line_h

    def _render_settings(self, rect):
        # 简易音量滑条
        label = FONT_SMALL.render('音量', True, (40,40,40))
        self.screen.blit(label, (rect.x, rect.y))
        bar = pygame.Rect(rect.x, rect.y+28, rect.width, 10)
        pygame.draw.rect(self.screen, (200,200,220), bar, border_radius=5)
        knob_x = bar.x + int(self.volume * bar.width)
        pygame.draw.circle(self.screen, (100,149,237), (knob_x, bar.y+5), 8)
        tips = ['基础设置占位：图像质量（高/中/低）、语言、提示开关']
        y = bar.y + 30
        for t in tips:
            self.screen.blit(FONT_SMALL.render(t, True, (80,80,80)), (rect.x, y))
            y += 24

    def _render_generic_modal(self, title, items, prefix, data_key):
        font = get_chinese_font(20)
        pad = 12; line_h = font.get_linesize(); btn_h = line_h + 18
        w = max(font.render(title, True, (0,0,0)).get_width(),
                max([font.render(it, True, (0,0,0)).get_width() for it in items])) + 100
        h = (len(items) + 1) * (btn_h + 10) + 24
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (self.width // 2, self.height // 2)
        pygame.draw.rect(self.screen, (250,250,255), rect, border_radius=10)
        pygame.draw.rect(self.screen, (150,150,200), rect, 2, border_radius=10)

        tw_title = font.render(title, True, (40,40,40)).get_width()
        y = rect.y + pad
        self.screen.blit(font.render(title, True, (40,40,40)),
                         (rect.centerx - tw_title // 2, y))
        y += line_h + 8

        for idx, text in enumerate(items):
            tw = font.render(text, True, (0,0,0)).get_width()
            btn_rect = pygame.Rect(rect.centerx - (tw + 20) // 2, y, tw + 20, btn_h)
            pygame.draw.rect(self.screen, (220,220,240), btn_rect, border_radius=6)
            self.screen.blit(font.render(text, True, (0,0,0)),
                            (btn_rect.x + 10, btn_rect.y + 2))
            setattr(self, f'_{prefix}_btn_{idx}', (btn_rect, idx, data_key))
            y += btn_h + 6

    def _render_shu_skill_modal(self, base_rect):
        """
        子鼠技能弹窗：较小、居中、只包内容
        """
        # cur = self.game.players[self.game.current_player_idx]
        # if self.shu_sub_modal == 'select_target':
        #     title = "选择目标"
        #     labels = [fmt_name(p) for p in self.game.players]
        #     items = labels
        #     key = 'target'
        # elif self.shu_sub_modal == 'select_dir':
        #     title = f"已选 {fmt_name(self.shu_target)}"
        #     items = ['反向移动', '原地停留']
        #     key = 'direction'
        # else:
        #     return
        # self._render_generic_modal(title, items, 'shu', key)
        font = get_chinese_font(20)
        pad = 12
        line_h = font.get_linesize()

        # 1. 先画半透明遮罩（防止大白框再出现）
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # 2. 生成内容
        if self.shu_sub_modal == 'select_target':
            title = "选择目标"
            labels = [fmt_name(p) for p in self.game.players]
            items = labels
        elif self.shu_sub_modal == 'select_dir':
            title = f"已选 {fmt_name(self.shu_target)}"
            items = ['反向移动', '原地停留']
        else:
            return

        # 3. 计算最小宽高
        btn_h   = line_h + 18            # 按钮高度：↑ 数值越大，按钮越"高"
        margins = 2 * pad                # 上下/左右留白：↑ 数值越大，整个弹窗四周空白越多
        w = max(font.render(title, True, (0, 0, 0)).get_width(),   # 标题文字宽度
                *[font.render(t, True, (0, 0, 0)).get_width()      # 按钮文字宽度
                for t in items]) \
            + 2 * pad + 50                                         # 横向总留白：↑ 50 越大 → 弹窗越宽
        h = (len(items) + 1) * (btn_h + 15) + margins - 50              # 纵向总高度：
        # ↑ (len(items)+1) 包含标题行
        # ↑ (btn_h + 10)   每行(按钮+行间距)高度，10 越大 → 行间距越大
        # ↑ margins        上下总留白
        # 如果想让窗口"更大/更小"，只需微调：
        #   - btn_h          → 按钮本身高度
        #   - 2*pad + 50     → 左右内边距（w）
        #   - btn_h + 10     → 上下行距（h）
        #   - margins        → 四周留白

        # 4. 画弹窗
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (self.width // 2, self.height // 2)
        pygame.draw.rect(self.screen, (250, 250, 255), rect, border_radius=10)
        pygame.draw.rect(self.screen, (150, 150, 200), rect, 2, border_radius=10)

        # 5. 标题居中
        tw_title = font.render(title, True, (40, 40, 40)).get_width()
        y = rect.y + pad
        self.screen.blit(font.render(title, True, (40, 40, 40)),
                        (rect.centerx - tw_title // 2, y))
        y += line_h + 8

        # 6. 按钮居中
        for idx, text in enumerate(items):
            tw = font.render(text, True, (0, 0, 0)).get_width()
            btn_rect = pygame.Rect(rect.centerx - (tw + 20) // 2, y, tw + 20, btn_h)
            pygame.draw.rect(self.screen, (220, 220, 240), btn_rect, border_radius=6)
            self.screen.blit(font.render(text, True, (0, 0, 0)),
                            (btn_rect.x + 10, btn_rect.y + 2))
            # 缓存点击区域 - 修复：为方向选择使用英文键名
            if self.shu_sub_modal == 'select_target':
                setattr(self, f'_shu_target_btn_{idx}', btn_rect)
            else:  # select_dir
                # 根据中文文本映射到英文键名
                key_map = {'反向移动': 'backward', '原地停留': 'stay'}
                key = key_map.get(text, text)
                setattr(self, f'_shu_dir_btn_{key}', btn_rect)
            y += btn_h + 6

    def _start_ji_landing_selection(self):
        """开始酉鸡技能降落点选择模式"""
        cur = self.game.players[self.game.current_player_idx]
        level = cur.skill_mgr.skills['鸡']['level']

        # 检查当前位置是否符合起飞条件
        current_tile = self.game.board.tiles[cur.position]

        def allow_start(t):
            return t.owner == cur or (t.owner is None and self.game._is_property_tile(t)) or t.special in ('start', 'encounter', 'hospital')

        # 添加对特殊格子（公共格子）的支持
        def is_public_special(t):
            return t.special in ('start', 'encounter', 'hospital')

        if not (allow_start(current_tile) or is_public_special(current_tile)):
            self.log.append(f'{fmt_name(cur)} 当前位置无法起飞')
            return

        # 根据技能等级确定可降落的地皮，包含特殊格子
        if level == SkillLevel.I:
            valid_tiles = [t for t in self.game.board.tiles
                        if allow_start(t) or is_public_special(t)]
        elif level == SkillLevel.II:
            valid_tiles = [t for t in self.game.board.tiles
                        if (t.owner is None and self.game._is_property_tile(t)) or is_public_special(t)]
        else:  # SkillLevel.III
            valid_tiles = [t for t in self.game.board.tiles
                        if self.game._is_property_tile(t) or is_public_special(t)]

        # 过滤掉当前位置
        self.ji_valid_tiles = [t for t in valid_tiles if t.idx != cur.position]

        # 验证距离限制（拐角数）
        final_valid_tiles = []
        max_corners = {SkillLevel.I: 0, SkillLevel.II: 1, SkillLevel.III: 2}[level]
        for tile in self.ji_valid_tiles:
            corners = cur.skill_mgr._count_corners(cur.position, tile.idx, 48)
            if corners <= max_corners:
                final_valid_tiles.append(tile)

        self.ji_valid_tiles = final_valid_tiles

        if not self.ji_valid_tiles:
            self.log.append(f'{fmt_name(cur)} 当前等级下无可降落地点')
            self._scroll_to_bottom()
            return

        self.ji_mode = 'selecting_to'
        current_name = current_tile.name
        self.log.append(f'{fmt_name(cur)} 从「{current_name}」起飞，请选择降落地点...')
        self._scroll_to_bottom()

    def _handle_ji_landing_click(self, tile_idx):
        """处理酉鸡技能降落点点击"""
        cur = self.game.players[self.game.current_player_idx]

        # 执行技能
        ok, msg = cur.skill_mgr.use_active_skill(
            option={'from_idx': cur.position, 'to_idx': tile_idx},
            game=self.game
        )
        self.log.append(msg)
        self._scroll_to_bottom()

        # 退出选择模式
        self._exit_ji_selection()

    def _exit_ji_selection(self):
        """退出酉鸡技能选择模式"""
        self.ji_mode = None
        self.ji_valid_tiles = []

    def _modal_handle_click(self, pos):
        if self.active_modal == 'settings':
            w = int(self.width * 0.66)
            h = int(self.height * 0.7)
            x = (self.width - w) // 2
            y = (self.height - h) // 2
            content_rect = pygame.Rect(x + 16, y + 50, w - 32, h - 66)
            bar = pygame.Rect(content_rect.x, content_rect.y + 28, content_rect.width, 10)
            if bar.collidepoint(pos):
                rel = (pos[0] - bar.x) / max(1, bar.width)
                self.volume = max(0.0, min(1.0, rel))
                try:
                    pygame.mixer.music.set_volume(self.volume)
                except Exception:
                    pass
                return True

        # ---------- 子鼠技能 ----------
        if self.active_modal == 'shu_skill':
            cur = self.game.players[self.game.current_player_idx]
            # 1. 选择目标
            if self.shu_sub_modal == 'select_target':
                for idx, p in enumerate(self.game.players):
                    btn = getattr(self, f'_shu_target_btn_{idx}', None)
                    if btn and btn.collidepoint(pos):
                        if p is cur:
                            return True
                        self.shu_target = p
                        self.shu_sub_modal = 'select_dir'   # 立即切换到方向选择
                        return True                         # 保持弹窗

            # 2. 选择技能（反向/停留）
            elif self.shu_sub_modal == 'select_dir':
                for key in ('backward', 'stay'):
                    btn = getattr(self, f'_shu_dir_btn_{key}', None)
                    if btn and btn.collidepoint(pos):
                        ok, msg = cur.skill_mgr.use_shu([self.shu_target], key)
                        # 立即追加详细日志
                        direction_text = "反向移动" if key == 'backward' else "原地停留一回合"
                        self.log.append(
                            f"{fmt_name(cur)} 对 {fmt_name(self.shu_target)} 发动【灵鼠窃运】："
                            f"强制其{direction_text}"
                        )
                        self._scroll_to_bottom()
                        # 关闭弹窗，刷新界面
                        self.active_modal = None
                        self.shu_sub_modal = None
                        self.draw_info()    # 立即刷新
                        return True
            return False

        # ---------- 酉鸡技能 ----------
        if self.active_modal == 'ji_skill':
            cur = self.game.players[self.game.current_player_idx]
            level = cur.skill_mgr.skills['鸡']['level']

            # 动态收集当前可选格子
            def allow_start(t):
                return t.owner == cur or (t.owner is None and self.game._is_property_tile(t))

            if self.ji_sub_modal == 'select_from':
                tiles = [t for t in self.game.board.tiles if allow_start(t)]
                next_phase = 'select_to'
                key = 'from_idx'
            elif self.ji_sub_modal == 'select_to':
                if level == SkillLevel.I:
                    tiles = [t for t in self.game.board.tiles if allow_start(t)]
                elif level == SkillLevel.II:
                    tiles = [t for t in self.game.board.tiles if t.owner is None and self.game._is_property_tile(t)]
                else:
                    tiles = [t for t in self.game.board.tiles if self.game._is_property_tile(t)]
                tiles = [t for t in tiles if t.idx != self.ji_from]
                next_phase = None
                key = 'to_idx'
            else:
                return False

            for idx, tile in enumerate(tiles):
                btn, i, k = getattr(self, f'_ji_btn_{idx}', (None, None, None))
                if btn and btn.collidepoint(pos):
                    if k == 'from_idx':
                        self.ji_from = tile.idx
                        self.ji_sub_modal = next_phase
                        return True
                    elif k == 'to_idx':
                        ok, msg = cur.skill_mgr.use_active_skill(option={'from_idx': self.ji_from, 'to_idx': tile.idx})
                        self.log.append(msg)
                        self._scroll_to_bottom()
                        self.active_modal = None
                        self.ji_sub_modal = None
                        self.draw_info()
                        return True
            return False

    def _load_modal_text(self, kind):
        # 从 rules.md 读取全文，或仅显示英雄节选
        try:
            path = os.path.join(self.base_dir, 'rules.md')
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            content = '未找到规则文件。'
        if kind == 'rules':
            return content
        if kind == 'heroes':
            # 使用技能详情拼接
            lines = ['十二生肖技能一览：']
            for z, det in SKILL_DETAILS.items():
                lines.append(f'{z}：{det}')
            return '\n'.join(lines)
        return ''

    def _draw_star(self, center, outer_r, color):
        # 绘制五角星
        cx, cy = center
        points = []
        inner_r = outer_r * 0.5
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            r = outer_r if i % 2 == 0 else inner_r
            points.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, (50,50,50), points, 1)

    def _can_buy_now(self, player):
        tile = self.game.current_tile(player)
        return (
            self.game._is_property_tile(tile) and
            tile.owner is None and
            player.money >= tile.price
        )

    def _can_upgrade_now(self, player):
        tile = self.game.current_tile(player)
        return (
            self.game._is_property_tile(tile) and
            tile.owner is player and
            tile.level != BuildingLevel.PALACE and
            not player.status.get('just_bought') and
            player.money >= self.game.upgrade_cost(tile)
        )

    def _can_advance_skill(self, player):
        if not hasattr(player, 'skill_mgr'):
            return False
        z = player.zodiac
        if z not in player.skill_mgr.skills:
            return False
        sk = player.skill_mgr.skills[z]
        lvl, used, eng = sk['level'], sk['used'], player.energy
        if z == '鼠':
            return (lvl == SkillLevel.I and used >= 3 and eng >= 100) or \
                (lvl == SkillLevel.II and used >= 6 and eng >= 250)
        elif z == '牛':
            return (lvl == SkillLevel.I and used >= 2 and eng >= 150) or \
                (lvl == SkillLevel.II and used >= 4 and eng >= 300)
        elif z == '虎':
            return (lvl == SkillLevel.I and used >= 2 and eng >= 200) or \
                (lvl == SkillLevel.II and used >= 4 and eng >= 400)
        elif z == '兔':
            return (lvl == SkillLevel.I and used >= 3 and eng >= 100) or \
                (lvl == SkillLevel.II and used >= 6 and eng >= 200)
        elif z == '鸡':
            return (lvl == SkillLevel.I and used >= 3 and eng >= 200) or \
                (lvl == SkillLevel.II and used >= 6 and eng >= 400)
        return False

    def run(self):
        log_font = get_chinese_font(18)          # 提前拿到字体，供滚轮使用
        line_h   = log_font.get_linesize()
        visible_lines = 260 // line_h            # 260 是日志区域高度

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # ⬇ 滚轮日志滚动
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:        # 滚轮上
                        self.log_scroll = max(0, self.log_scroll - 1)
                    elif event.button == 5:      # 滚轮下
                        max_scroll = max(0, len(self.log) - visible_lines)
                        self.log_scroll = min(max_scroll, self.log_scroll + 1)
                    else:
                        self.handle_click(event.pos)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.ji_mode == 'selecting_to':
                            self._exit_ji_selection()
                            self.log.append('取消技能选择')
                            self._scroll_to_bottom()

            self.draw_board()
            self.draw_info()
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == '__main__':
    count, zodiacs = choose_players_ui()
    pygame.display.init()        # 重新打开主窗口
    ui = GameUI()
    ui.game = Game([f"玩家{i+1}" for i in range(count)], zodiacs)
    # 重新绑定 game 到每个玩家
    for p in ui.game.players:
        p.game = ui.game
    ui.player_sprites = ui._load_player_sprites()
    ui.run()