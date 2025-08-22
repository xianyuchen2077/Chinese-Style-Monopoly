# game_pygame_ui.py
# 使用pygame实现更华丽的中国文化棋盘游戏UI

import pygame
import sys
from game_core import Game, Element, BuildingLevel
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

# 生肖→地支名称（用于日志及界面）
EARTHLY_NAMES = {
    '鼠': '子鼠', '牛': '丑牛', '虎': '寅虎', '兔': '卯兔',
    '龙': '辰龙', '蛇': '巳蛇', '马': '午马', '羊': '未羊',
    '猴': '申猴', '鸡': '酉鸡', '狗': '戌狗', '猪': '亥猪'
}

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
    '牛': '蛮牛冲撞（摧毁途经建筑）',
    '虎': '猛虎分身（双体两回合）',
    '兔': '玉兔疾行（下次步数×2）',
    '龙': '真龙吐息（喷射强制入院）',
    '蛇': '灵蛇隐踪（隐身3回合）',
    '马': '天马守护（减免负面）',
    '羊': '灵羊出窍（灵魂移动）',
    '猴': '灵猴百变（复制技能）',
    '鸡': '金鸡腾翔（飞行落点）',
    '狗': '天狗护体（免疫伤害）',
    '猪': '福猪破障（摧毁建筑-1）',
}

# 技能详细说明（来自 rules.md，精简版）
SKILL_DETAILS = {
    '鼠': '灵鼠窃运：指定玩家控制其下回合移动方向，可反向或停留；对隐身无效。冷却3回合。',
    '牛': '蛮牛冲撞：本回合摧毁经过路径上所有他人建筑；自身获“业障”3回合（租金+50%）。对土减半。冷却3回合。',
    '虎': '猛虎分身：分身为两个实体2回合，各自独立转盘移动，结束合体。分身受伤加倍。冷却3回合。',
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
    player_count = 1
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
        self.has_rolled = False   # 当前玩家是否已转动罗盘
        self.hovered_tile = None   # 当前悬停地块索引
        self.shu_target = None      # 子鼠技能：被选中的目标玩家
        self.shu_sub_modal = None   # 'select_target' | 'select_dir'


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
        self.game = Game(['玩家一', '玩家二'], ['鼠', '牛'])
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
            pos = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if grid_map[r][c] == player.position]
            if not pos: continue
            row, col = pos[0]
            cx = self.margin + col * CELL_SIZE + CELL_SIZE // 2
            cy = self.margin + row * CELL_SIZE + CELL_SIZE // 2
            sprite = self.player_sprites[i] if i < len(self.player_sprites) else None
            if sprite:
                self.screen.blit(sprite, sprite.get_rect(center=(cx, cy)))
            else:
                pygame.draw.circle(self.screen, PLAYER_COLORS[i % 4], (cx, cy), int(CELL_SIZE * 0.32))

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
        rolled = self.has_rolled
        color_spin = (255, 222, 173) if not rolled else (200, 200, 200)
        text_spin  = (139, 69, 19)   if not rolled else (120, 120, 120)
        self.spin_btn_rect = pygame.Rect(info_x+24, btn_y, 140, 44)
        pygame.draw.rect(self.screen, color_spin, self.spin_btn_rect, border_radius=12)
        self.screen.blit(FONT.render('天命罗盘', True, text_spin),
                        (self.spin_btn_rect.x+6, self.spin_btn_rect.y+4))

        # 技能按钮
        color_skill = (176, 224, 230) if not rolled else (200, 200, 200)
        text_skill  = (25, 25, 112)   if not rolled else (120, 120, 120)
        self.skill_btn_rect = pygame.Rect(info_x+24+160, btn_y, 140, 44)
        pygame.draw.rect(self.screen, color_skill, self.skill_btn_rect, border_radius=12)
        self.screen.blit(FONT.render('符咒潜能', True, text_skill),
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
        can_adv = (cur_player.zodiac == '鼠' and
                cur_player.skill_mgr.skills['鼠']['level'] != cur_player.skill_mgr.skills['鼠']['level'].__class__.__name__)
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
            # 冷却信息与状态（简易展示）
            cd = player.cooldowns.get(player.zodiac, 0) if hasattr(player, 'cooldowns') else 0
            positive = 'shield' in player.status if hasattr(player, 'status') else False
            negative = 'skip_turns' in player.status if hasattr(player, 'status') else False
            attr_text = f"状态：{'护盾 ' if positive else ''}{'休息 ' if negative else ''}".strip()
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
        if self.spin_btn_rect.collidepoint(pos):
            if not self.has_rolled:        # 本回合尚未转动
                self.spin_wheel()
            else:                          # 已转动，自动进入下一位
                self.log.append(f'{fmt_name(self.game.players[self.game.current_player_idx])} 本回合已转动罗盘')
                self._scroll_to_bottom()

        # ---------------- 技能按钮 ----------------
        elif self.skill_btn_rect.collidepoint(pos):
            cur = self.game.players[self.game.current_player_idx]
            if cur.zodiac != '鼠':
                self.log.append(f'{fmt_name(cur)} 暂无可用主动技能')
                return
            if cur.skill_mgr.skills['鼠']['cooldown'] > 0:
                self.log.append(f'{fmt_name(cur)} 【灵鼠窃运】冷却中')
                self._scroll_to_bottom()
                return
            # 打开选目标弹框
            self.shu_sub_modal = 'select_target'
            self.active_modal = 'shu_skill'
            self.modal_scroll = 0
            self.draw_info()    # 立即更新

        # ---------------- 升级按钮 ----------------
        elif hasattr(self, 'upgrade_skill_btn_rect') and self.upgrade_btn_rect.collidepoint(pos):
            cur = self.game.players[self.game.current_player_idx]
            if cur.zodiac == '鼠':
                if cur.skill_mgr.upgrade_shu():
                    self.log.append(f'{fmt_name(cur)} 升级【灵鼠窃运】成功！')
                else:
                    self.log.append(f'{fmt_name(cur)} 灵气不足或条件未满足')
                self._scroll_to_bottom()
            self.draw_info()    # 立即更新

        elif hasattr(self, 'buy_btn_rect') and self.buy_btn_rect.collidepoint(pos):
            cur = self.game.players[self.game.current_player_idx]
            if self._can_buy_now(cur) and self.game.buy_property(cur):
                while self.game.log:
                    self.log.append(self.game.log.pop(0))
                    self._scroll_to_bottom()
            self.draw_info()    # 立即更新

        elif hasattr(self, 'upgrade_btn_rect') and self.upgrade_btn_rect.collidepoint(pos):
            cur = self.game.players[self.game.current_player_idx]
            if self._can_upgrade_now(cur) and self.game.upgrade_building(cur):
                while self.game.log:
                    self.log.append(self.game.log.pop(0))
                    self._scroll_to_bottom()
            self.draw_info()    # 立即更新

        elif hasattr(self, 'end_turn_btn_rect') and self.end_turn_btn_rect.collidepoint(pos):
            self.game.next_turn()
            self.has_rolled = False
            self.log.append(f'轮到 {fmt_name(self.game.players[self.game.current_player_idx])}')
            self._scroll_to_bottom()
            self.draw_info()    # 立即更新

    def spin_wheel(self):
        player = self.game.players[self.game.current_player_idx]
        if player.status.get('skip_turns', 0) > 0:
            player.status['skip_turns'] -= 1
            self.log.append(f'{fmt_name(player)} 休息中，跳过回合。')
            self._scroll_to_bottom()
            self.game.next_turn()
            return

        steps = self.game.spin_wheel()
        self._animate_wheel(steps)
        pos = self.game.move_player(player, steps)
        self.log.append(f'{fmt_name(player)} 移动至 {pos}')
        self._scroll_to_bottom()

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

    def _render_shu_skill_modal(self, rect):
        cur = self.game.players[self.game.current_player_idx]
        font = get_chinese_font(20)
        pad = 12
        y = rect.y + pad

        if self.shu_sub_modal == 'select_target':
            title = "【灵鼠窃运】请选择目标玩家："
            self.screen.blit(font.render(title, True, (40, 40, 40)), (rect.x, y))
            y += font.get_linesize() + 8
            btn_h = 36
            for idx, p in enumerate(self.game.players):
                if p is cur:
                    continue  # 不能选自己
                label = f"{fmt_name(p)}"
                tw = font.render(label, True, (0, 0, 0)).get_width()
                btn = pygame.Rect(rect.x, y, tw + 20, btn_h)
                pygame.draw.rect(self.screen, (220, 220, 240), btn, border_radius=6)
                self.screen.blit(font.render(label, True, (0, 0, 0)),
                                (rect.x + 10, y + 4))
                # 缓存按钮区域，供点击
                setattr(self, f'_shu_target_btn_{idx}', btn)
                y += btn_h + 6

        elif self.shu_sub_modal == 'select_dir':
            target = self.shu_target
            title = f"已选择 {fmt_name(target)}，请选择控制方式："
            self.screen.blit(font.render(title, True, (40, 40, 40)), (rect.x, y))
            y += font.get_linesize() + 8
            choices = [('backward', '反向移动'), ('stay', '原地停留')]
            btn_h = 36
            for key, desc in choices:
                tw = font.render(desc, True, (0, 0, 0)).get_width()
                btn = pygame.Rect(rect.x, y, tw + 20, btn_h)
                pygame.draw.rect(self.screen, (220, 220, 240), btn, border_radius=6)
                self.screen.blit(font.render(desc, True, (0, 0, 0)),
                                (rect.x + 10, y + 4))
                setattr(self, f'_shu_dir_btn_{key}', btn)
                y += btn_h + 6


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

        if self.active_modal == 'shu_skill':
            cur = self.game.players[self.game.current_player_idx]
            if self.shu_sub_modal == 'select_target':
                for idx, p in enumerate(self.game.players):
                    if p is cur:
                        continue
                    btn = getattr(self, f'_shu_target_btn_{idx}', None)
                    if btn and btn.collidepoint(pos):
                        self.shu_target = p
                        self.shu_sub_modal = 'select_dir'
                        return True

            elif self.shu_sub_modal == 'select_dir':
                for key in ('backward', 'stay'):
                    btn = getattr(self, f'_shu_dir_btn_{key}', None)
                    if btn and btn.collidepoint(pos):
                        ok, msg = cur.skill_mgr.use_shu(self.shu_target, key)
                        self.log.append(msg)
                        self._scroll_to_bottom()
                        self.active_modal = None
                        self.shu_sub_modal = None
                        self.draw_info()  # 立即刷新
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

            self.draw_board()
            self.draw_info()
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == '__main__':
    count, zodiacs = choose_players_ui()
    pygame.display.init()        # 重新打开主窗口
    ui = GameUI()
    ui.game = Game([f"玩家{i+1}" for i in range(count)], zodiacs)
    ui.player_sprites = ui._load_player_sprites()
    ui.run()