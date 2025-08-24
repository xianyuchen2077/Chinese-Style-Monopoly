# game_core.py
# 游戏核心逻辑模块

from code import interact
import random
from enum import Enum
from typing import Self, Optional

# 五行元素
class Element(Enum):
    GOLD = '金'
    WOOD = '木'
    WATER = '水'
    FIRE = '火'
    EARTH = '土'

# 建筑等级
class BuildingLevel(Enum):
    EMPTY = 0
    HUT = 1
    TILE = 2
    INN = 3
    PALACE = 4

# 技能等级
class SkillLevel(Enum):
    I = 1
    II = 2
    III = 3

# 生肖→地支名称（用于日志及界面）
EARTHLY_NAMES = {
    '鼠': '子鼠', '牛': '丑牛', '虎': '寅虎', '兔': '卯兔',
    '龙': '辰龙', '蛇': '巳蛇', '马': '午马', '羊': '未羊',
    '猴': '申猴', '鸡': '酉鸡', '狗': '戌狗', '猪': '亥猪'
}

# 统一日志玩家名称
def fmt_name(player):
    """返回统一格式：[玩家名]角色名"""
    return f"[{player.name}]{EARTHLY_NAMES[player.zodiac]}"

# ===== 子鼠技能数据结构 =====
SKILL_SHU = {
    'level': SkillLevel.I,
    'cooldown': 0,
    'used': 0
}

# ===== 丑牛技能数据结构 =====
SKILL_NIU = {
    'level': SkillLevel.I,
    'cooldown': 0,
    'used': 0
}

# ===== 卯兔技能数据结构 =====
SKILL_RABBIT = {
    'level': SkillLevel.I,
    'cooldown': 0,
    'used': 0,
    'active': False,       # True=已获得加速
    'multiplier': 2        # 当前倍率（I/II=2，III=3）
}

# ===== 未羊技能数据结构 =====
SKILL_YANG = {
    'level': SkillLevel.I,
    'cooldown': 0,
    'used': 0,
    'soul_pos': None,     # 灵魂当前位置
    'soul_turns': 0,      # 灵魂出窍剩余回合
    'max_dist': 12        # I/II/III 对应 12/17/23
}

# ===== 酉鸡技能数据结构 =====
SKILL_JI = {
    'level': SkillLevel.I,
    'cooldown': 0,
    'used': 0
}

class SkillManager:
    """每个玩家自带一个实例，负责冷却、升级与触发"""
    def __init__(self, player):
        self.player = player
        self.skills = {
            '鼠': SKILL_SHU.copy(),
            '牛': SKILL_NIU.copy(),
            '兔': SKILL_RABBIT.copy(),
            '羊': SKILL_YANG.copy(),
            '鸡': SKILL_JI.copy()
        }

    def can_use_active_skill(self):
        z = self.player.zodiac
        if z in self.skills:
            return self.skills[z]['cooldown'] == 0
        return False

    # ------------- 统一外部调用接口 ----------------
    def use_active_skill(self, target_list=None, option=None, game=None):
        """
        target_list: list[Player] 可为空/单/多
        option:      额外参数
        """
        z = self.player.zodiac
        if z == '鼠':
            return self.use_shu(target_list, option)
        elif z == '牛':
            return self.use_niu(target_list, option, game)
        elif z == '兔':
            return self.use_tu(target_list, option)
        elif z == '羊':
            return self.use_yang(target_list, option)
        elif z == '鸡':
            return self.use_ji(target_list, option, game)
        else:
            return False, "暂无主动技能"

    # ------------- 鼠 - 灵鼠窃运 ----------------
    def use_shu(self, target_list, direction):
        """
        direction: 'backward' | 'stay'
        """
        if not target_list:
            return False, "未选择目标"

        skill = self.skills['鼠']
        if skill['cooldown'] > 0:
            return False, "【灵鼠窃运】技能冷却中"

        level = skill['level']
        turns = 2 if level == SkillLevel.III else 1 # 只有III级可以操控两个回合
        lock_skill = level != SkillLevel.I          # 技能等级II级以上能够封锁技能

        # 支持多目标
        for target in target_list:
            if direction == 'backward':     # 反向
                target.clockwise = not target.clockwise
            elif direction == 'stay':       # 原地停留
                target.status['shu_control'] = {
                    'turns': turns,
                    'direction': 'stay',
                    'lock_skill': lock_skill
                }
                target.can_move = False

        # 技能冷却
        skill['cooldown'] = 4 if level == SkillLevel.III else 3
        skill['used'] += 1

        names = ",".join(fmt_name(p) for p in target_list)
        return True, f"{self.player.name} 对 [{names}] 发动【灵鼠窃运】"

    def upgrade_shu(self):
        skill = self.skills['鼠']
        lvl, used, eng = skill['level'], skill['used'], self.player.energy

        if lvl == SkillLevel.I and used >= 3 and eng >= 100:
            skill['level'] = SkillLevel.II
            self.player.energy -= 100
            return True

        if lvl == SkillLevel.II and used >= 6 and eng >= 250:
            skill['level'] = SkillLevel.III
            self.player.energy -= 250
            return True
        return False

    # ------------- 牛 - 蛮牛冲撞 ----------------
    def use_niu(self, target_list=None, option=None, game=None) -> tuple[bool, str]:
        """
        丑牛·蛮牛冲撞
        无需目标参数，对移动路径上的建筑造成破坏
        game: Game实例，通过参数传递
        """
        skill = self.skills['牛']
        if skill['cooldown'] > 0:
            return False, "【蛮牛冲撞】冷却中"

        if game is None:
            return False, "需要传递游戏实例参数"

        level = skill['level']
        self.player.status['niu_rampage'] = {
            'level': level,
            'path_tiles': []
        }

        # 设置业障状态
        if level == SkillLevel.I:
            self.player.status['karma'] = 2
        elif level == SkillLevel.II:
            self.player.status['karma'] = 1
        # III级无业障

        skill['cooldown'] = 3
        skill['used'] += 1

        return True, f"{fmt_name(self.player)} 发动【蛮牛冲撞】，横冲直撞破坏沿途建筑！"

    def upgrade_niu(self):
        """升级丑牛技能"""
        skill = self.skills['牛']
        lvl, used, eng = skill['level'], skill['used'], self.player.energy

        if lvl == SkillLevel.I and used >= 2 and eng >= 150:
            skill['level'] = SkillLevel.II
            self.player.energy -= 150
            return True
        if lvl == SkillLevel.II and used >= 4 and eng >= 300:
            skill['level'] = SkillLevel.III
            self.player.energy -= 300
            return True
        return False

    # ------------- 兔 - 玉兔疾行 ----------------
    def use_tu(self, target_list=None, option=None):
        skill = self.skills['兔']
        if skill['cooldown'] > 0:
            return False, "【玉兔疾行】冷却中"
        skill['active'] = True
        skill['cooldown'] = 3
        skill['used'] += 1
        return True, f"{self.player.name} 发动【玉兔疾行】加速{skill['multiplier']}倍"

    def upgrade_tu(self):
        skill = self.skills['兔']
        lvl, used, eng = skill['level'], skill['used'], self.player.energy
        if lvl == SkillLevel.I and used >= 3 and eng >= 100:
            skill['level'] = SkillLevel.II
            self.player.energy -= 100
            return True
        if lvl == SkillLevel.II and used >= 6 and eng >= 200:
            skill['level'] = SkillLevel.III
            skill['multiplier'] = 3
            self.player.energy -= 200
            return True
        return False

    # ------------- 羊 - 灵羊出窍 ----------------
    def use_yang(self, target_list, option=None):
        skill = self.skills['羊']

        # 1. 灵魂已出窍 → 归位
        if skill['soul_pos'] is not None:
            self.player.position = skill['soul_pos']
            skill['soul_pos'] = None
            skill['soul_turns'] = 0
            skill['cooldown'] = 5
            return True, f"{fmt_name(self.player)} 灵魂归位，本体传送到 {self.player.position} 格"

        # 2. 灵魂出窍（仅标记）
        if skill['cooldown'] > 0:
            return False, "【灵羊出窍】冷却中"

        skill['soul_pos'] = self.player.position
        skill['soul_turns'] = 3
        skill['cooldown'] = 0
        skill['used'] += 1
        return True, f"{fmt_name(self.player)} 发动【灵羊出窍】，灵魂已出窍（3回合内可传送）"

    # —— 灵魂移动：在 Game.spin_wheel 后由 Game 统一调用 ——
    def move_soul(self, dice: int, game=None) -> str | None:
        """
        仅在未羊灵魂已出窍时调用，让灵魂前进 dice 步。
        返回日志字符串；无灵魂时返回 None。
        """
        skill = self.skills['羊']
        if skill['soul_pos'] is None:
            return None

        level = skill['level']
        max_dist = {SkillLevel.I: 12, SkillLevel.II: 17, SkillLevel.III: 23}[level]
        steps = min(dice, max_dist)
        board_len = 48
        old = skill['soul_pos']
        new = (old + steps) % board_len
        skill['soul_pos'] = new

        # 触发“三阳开泰”
        dist = self._yang_distance(self.player.position, new, board_len)
        reward = ""
        if random.random() < {1: 0.05, 2: 0.15, 3: 0.5}[level.value]:
            reward = self._trigger_san_yang_kai_tai(dist, game)

        msg = f"{fmt_name(self.player)} 【灵魂出窍】，灵魂移动 {steps} 格至 {new}"
        if reward:
            msg += f"；{reward}"
        return msg

    # —— 静态工具函数（无冗余）——
    @staticmethod
    def _yang_distance(a: int, b: int, total: int) -> int:
        d1 = (b - a) % total
        d2 = (a - b) % total
        return min(d1, d2)

    def _trigger_san_yang_kai_tai(self, distance: int, game) -> str:
        """
        触发三阳开泰效果
        game: Game实例，通过参数传递
        """
        if not game:
            return ""

        path = self._shortest_path(self.player.position, distance)
        for idx in path[1:]:
            tile = game.board.tiles[idx]
            if tile.owner is None and tile.price and self.player.money >= tile.price:
                tile.owner = self.player
                tile.level = BuildingLevel.HUT
                self.player.properties.append(idx)
                game.log.append(f"触发【三阳开泰】，免费获得「{tile.name}」")
                return f"免费获得「{tile.name}」"
            elif tile.owner == self.player and tile.level != BuildingLevel.PALACE:
                game.upgrade_building(self.player, tile)
                game.log.append(f"触发【三阳开泰】，免费升级「{tile.name}」")
                return f"免费升级「{tile.name}」"
        return ""

    def _shortest_path(self, start: int, dist: int) -> list[int]:
        total = 48
        forward = [(start + i) % total for i in range(dist + 1)]
        backward = [(start - i) % total for i in range(dist + 1)]
        return forward if len(forward) <= len(backward) else backward

    # ------------- 鸡 - 金鸡腾翔 ----------------
    def use_ji(self, target_list=None, option=None, game=None) -> tuple[bool, str]:
        """
        酉鸡·金鸡腾翔
        option 必须包含 {'from_idx': int, 'to_idx': int}
        game: Game实例，通过参数传递
        target_list 保持空，仅为了接口统一
        """
        skill = self.skills['鸡']
        if skill['cooldown'] > 0:
            return False, "【金鸡腾翔】冷却中"

        # 校验 option
        if not isinstance(option, dict):
            return False, "参数格式错误"
        from_idx = option.get('from_idx')
        to_idx   = option.get('to_idx')
        if from_idx is None or to_idx is None:
            return False, "缺少起飞或降落点"

        if game is None:
            return False, "需要传递游戏实例参数"

        board = game.board
        total = len(board.tiles)

        def is_public_or_special(tile):
            return (
                tile.special in ('start', 'encounter', 'hospital') or
                (tile.owner is None and game._is_property_tile(tile))
            )

        level = skill['level']
        # 规则表
        rules = {
            SkillLevel.I: {
                'allow_start': lambda t: t.owner == self.player or is_public_or_special(t),
                'allow_land' : lambda t: t.owner == self.player or is_public_or_special(t),
                'max_corners': 0
            },
            SkillLevel.II: {
                'allow_start': lambda t: t.owner == self.player or is_public_or_special(t),
                'allow_land' : lambda t: t.owner is None and self.player.game._is_property_tile(t),
                'max_corners': 1
            },
            SkillLevel.III: {
                'allow_start': lambda t: t.owner == self.player or is_public_or_special(t),
                'allow_land' : lambda t: True,
                'max_corners': 2
            }
        }
        rule = rules[level]

        # 边界与规则校验
        if not (0 <= from_idx < total and 0 <= to_idx < total):
            return False, "索引越界"
        if from_idx == to_idx:
            return False, "不能原地降落"

        start_tile = board.tiles[from_idx]
        land_tile  = board.tiles[to_idx]
        if not rule['allow_start'](start_tile):
            return False, "起飞点不符合规则"
        if not rule['allow_land'](land_tile):
            return False, "降落点不符合规则"

        corners = self._count_corners(from_idx, to_idx, total)
        if corners > rule['max_corners']:
            return False, f"跨越拐角({corners})超限"

        # 执行飞行
        self.player.position = to_idx
        skill['cooldown'] = 3
        skill['used'] += 1

        # III 级奖励
        reward = ""
        if level == SkillLevel.III and land_tile.owner == self.player:
            if self.player.game.can_upgrade(self.player, land_tile):
                self.player.game.upgrade_building(self.player, land_tile)
                reward = "并免费升级该地皮"

        msg = f"{fmt_name(self.player)} 从 {from_idx} 腾翔至 {to_idx}{reward}"
        return True, msg

    # 计算两格之间的“拐角”数
    def _count_corners(self, a: int, b: int, total: int) -> int:
        skill = self.skills['鸡']
        level = skill['level']

        if level == SkillLevel.I:
            # 一级只能顺时针前进
            cw = (b - a) % total
            return cw // 13
        else:
            # 二级和三级可以双向选择最优路径
            cw = (b - a) % total
            ccw = (a - b) % total
            corners_cw = cw // 13
            corners_ccw = ccw // 13
            return min(corners_cw, corners_ccw)

    def upgrade_ji(self):
        skill = self.skills['鸡']
        lvl, used, eng = skill['level'], skill['used'], self.player.energy
        if lvl == SkillLevel.I and used >= 3 and eng >= 200:
            skill['level'] = SkillLevel.II
            self.player.energy -= 200
            return True
        if lvl == SkillLevel.II and used >= 6 and eng >= 400:
            skill['level'] = SkillLevel.III
            self.player.energy -= 400
            return True
        return False

    def tick_cooldown(self):
        for v in self.skills.values():
            v['cooldown'] = max(0, v['cooldown'] - 1)

class Player:
    def __init__(self, name, zodiac, is_ai=False):
        self.name = name
        self.zodiac = zodiac
        self.is_ai = is_ai
        self.money = 10000
        self.position = 0
        self.score = 0
        self.properties = []
        self.status = {}
        self.cooldowns = {}
        self.split = False
        self.energy = 0
        self.skill_mgr = SkillManager(self)
        self.clockwise = True          # True=顺时针, False=逆时针
        self.can_move = True           # False 表示本轮不能转盘
        self.game: Optional["Game"] = None

    def move_step(self, steps):
        """返回最终步数（含方向）"""
        # 1. 被子鼠控制停留
        if 'shu_control' in self.status:
            ctrl = self.status['shu_control']
            if ctrl['turns'] > 0 and ctrl['direction'] == 'stay':
                ctrl['turns'] -= 1
                if ctrl['turns'] == 0:
                    del self.status['shu_control']
                self.can_move = False
                return 0

        # 2. 丑牛冲撞：提前记录路径
        if 'niu_rampage' in self.status:
            rampage_info = self.status['niu_rampage']
            rampage_info['path_tiles'] = self.record_move_path(steps, self.game)


        # 3. 卯兔加速
        if self.zodiac == '兔':
            skill = self.skill_mgr.skills['兔']
            if skill['active']:
                steps *= skill['multiplier']

        # 4. 未羊灵魂期间本体不移动
        if self.zodiac == '羊':
            skill = self.skill_mgr.skills['羊']
            if skill['soul_pos'] is not None:
                # 灵魂移动由外部调用move_soul处理
                return 0    # 本体不动，灵魂单独走

        # 5. 正常方向移动（使用玩家当前的clockwise状态）
        return steps if self.clockwise else -steps

    def record_move_path(self, steps: int, game) -> list[int]:
        """
        记录玩家本次移动将经过的所有格子索引（不含起点）。
        steps : 实际步数（带方向）
        game  : Game 实例，用于获取棋盘长度
        return: 路径格子索引列表
        """
        if steps == 0:
            return []

        current_pos = self.position
        board_len = len(game.board.tiles)
        path = []

        for i in range(1, abs(steps) + 1):
            if steps > 0:
                pos = (current_pos + i) % board_len
            else:
                pos = (current_pos - i) % board_len
            path.append(pos)

        return path
class Tile:
    def __init__(self, idx, name, element=None, price=0, special=None):
        self.idx = idx
        self.name = name
        self.element = element
        self.price = price
        self.owner = None
        self.level = BuildingLevel.EMPTY
        self.special = special  # 特殊格子类型

class GameBoard:
    def __init__(self):
        self.tiles = self._init_tiles()

    def _init_tiles(self):
        # 使用48个外圈格子，与UI外圈一致
        tiles = []
        # 元素分配：按金→木→水→火→土循环分配
        element_cycle = [Element.GOLD, Element.WOOD, Element.WATER, Element.FIRE, Element.EARTH]
        # 特殊格子：起点+若干奇遇与医院
        special_indices = {0: 'start', 6: 'encounter', 12: 'encounter', 18: 'encounter', 24: 'hospital', 30: 'encounter', 36: 'encounter', 42: 'encounter'}
        names_cycle = {
            Element.GOLD: ['鎏金坊', '琉璃阁', '金玉堂', '鎏辉苑', '镀金街', '元金台', '金阙门', '金穹庐', '金辉里'],
            Element.WOOD: ['青竹苑', '桃李斋', '沉香榭', '万木林', '翠微居', '竹影坊', '松风馆', '榕荫巷', '丹桂庭'],
            Element.WATER: ['流觞曲水', '碧波潭', '清泉居', '涵碧湾', '沧浪里', '映月池', '涟漪港', '霁水坊', '澄心堂'],
            Element.FIRE: ['赤焰楼', '丹霞阁', '炎阳宅', '离火坊', '焰影居', '炽明台', '红莲院', '火珠巷', '流火亭'],
            Element.EARTH: ['黄土高坡', '陶然居', '坤厚院', '厚土坊', '土阜里', '黄壤居', '堰田埠', '垣阙巷', '载物台'],
        }
        price_map = {
            Element.GOLD: 4000,
            Element.WOOD: 2600,
            Element.WATER: 3000,
            Element.FIRE: 2200,
            Element.EARTH: 3200,
        }

        name_counters = {e: 0 for e in element_cycle}

        for idx in range(48):
            if idx == 0:
                tiles.append(Tile(0, '乾坤起始格', special='start'))
                continue
            element = element_cycle[(idx - 1) % len(element_cycle)]
            name_list = names_cycle[element]
            name = name_list[name_counters[element] % len(name_list)]
            name_counters[element] += 1
            special = special_indices.get(idx)
            tiles.append(Tile(idx, name, element=element, price=price_map[element], special=special))
        return tiles

class Game:
    def __init__(self, player_names, zodiacs):
        self.board = GameBoard()
        self.players = [Player(name, zodiac) for name, zodiac in zip(player_names, zodiacs)]
        self.current_player_idx = 0
        self.turn = 0
        self.log = []

    def turn_start(self, player):
        # 1. 选择是否发动技能或特殊机遇
        pass  # UI层处理

    def after_move(self, player):
        # 2. 移动后是否发动技能
        pass  # UI层处理

    def after_trigger(self, player):
        # 3. 触发惩罚、奇遇、被动技能
        self.trigger_event(player)

    def turn_end(self, player):
        # 4. 是否购房、加盖
        pass  # UI层处理

    # 转动转盘
    def spin_wheel(self):
        dice = random.randint(1, 10)

        # ---- 未羊灵魂先行 ----
        for p in self.players:
            if p.zodiac == '羊':
                soul_log = p.skill_mgr.move_soul(dice, self)
                if soul_log:
                    self.log.append(soul_log)

        return dice

    # 玩家移动
    def move_player(self, player, steps):
        """改进的移动逻辑，正确处理方向和过起点"""
        if steps == 0:
            return player.position

        old_pos = player.position
        total_tiles = len(self.board.tiles)

        # 计算新位置
        new_pos = (old_pos + steps) % total_tiles
        if new_pos < 0:
            new_pos = total_tiles + new_pos
        player.position = new_pos

        # 初始化 passed_start 变量
        passed_start = False

        # 判断是否经过起点获得奖励
        if steps > 0:  # 正向移动
            # 检查是否跨越了起点：从非0位置移动后经过了0位置
            if old_pos != 0 and (old_pos + steps >= total_tiles):
                passed_start = True
        elif steps < 0:  # 反向移动
            # 检查是否跨越了起点：从非0位置移动后经过了0位置
            if old_pos != 0 and (old_pos + steps < 0):
                passed_start = True

        if passed_start:
            player.money += 5000
            self.log.append(f'{fmt_name(player)} 经过起点，获得5000金币！')

        # 处理丑牛冲撞效果
        self.handle_niu_rampage(player)

        return player.position

    def next_turn(self):
        # 清理上一位玩家的"刚购买地皮，不能够加盖"的限制
        current_player = self.players[self.current_player_idx]
        if 'just_bought' in current_player.status:
            current_player.status.pop('just_bought', None)

        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        self.turn += 1

        # 恢复所有玩家的移动能力
        for p in self.players:
            p.can_move = True
            # 处理业障状态
            if 'karma' in p.status:
                p.status['karma'] -= 1
                if p.status['karma'] <= 0:
                    del p.status['karma']
                    self.log.append(f"{fmt_name(p)} 业障消散")
            # 清除卯兔加速
            if p.zodiac == '兔':
                p.skill_mgr.skills['兔']['active'] = False
            # 未羊灵魂回合倒计时 & 强制传送
            elif p.zodiac == '羊':
                sk = p.skill_mgr.skills['羊']
                if sk['soul_pos'] is not None:
                    sk['soul_turns'] -= 1
                    max_range = {1: 12, 2: 17, 3: 23}[sk['level'].value]
                    too_far = SkillManager._yang_distance(p.position, sk['soul_pos'], 48) > max_range
                    if sk['soul_turns'] <= 0 or too_far:
                        p.position = sk['soul_pos']
                        sk['soul_pos'] = None
                        sk['cooldown'] = 5
                        reason = "灵魂出窍回合数超出最长回合数" if sk['soul_turns'] <= 0 else "灵魂出窍超出最远距离"
                        self.log.append(f"{fmt_name(p)} {reason}，强制传送到 {p.position}")

        # 为即将开始回合的玩家减少冷却
        new_current_player = self.players[self.current_player_idx]
        new_current_player.skill_mgr.tick_cooldown()

    def player_properties(self, player):
        """返回该玩家拥有的所有地皮对象"""
        return [self.board.tiles[i] for i in player.properties]

    def public_tiles(self):
        """返回所有无主且可买地皮"""
        return [t for t in self.board.tiles if self._is_property_tile(t) and t.owner is None]

    def handle_niu_rampage(self, player):
        """处理丑牛冲撞的建筑破坏效果"""
        if 'niu_rampage' not in player.status:
            return

        rampage_info = player.status['niu_rampage']
        level = rampage_info['level']
        path_tiles = rampage_info['path_tiles']
        destroyed = []

        for tile_idx in path_tiles:
            tile = self.board.tiles[tile_idx]
            if tile.owner and tile.level.value > 0:
                damage = 0
                if level == SkillLevel.I:
                    damage = 1
                elif level == SkillLevel.II:
                    damage = 1 if tile.owner != player else 0
                elif level == SkillLevel.III:
                    damage = 2 if tile.owner != player else 0

                if damage > 0:
                    old = tile.level.value
                    new = max(0, old - damage)
                    tile.level = BuildingLevel(new)
                    destroyed.append({
                        'name': tile.name,
                        'owner': tile.owner,
                        'old': old,
                        'new': new
                    })

        # 终点额外破坏（II/III级）
        if level in [SkillLevel.II, SkillLevel.III] and path_tiles:
            end_tile = self.board.tiles[path_tiles[-1]]
            if end_tile.owner and end_tile.owner != player:
                chance = 0.5 if level == SkillLevel.II else 1.0
                if random.random() < chance and end_tile.level.value > 0:
                    old = end_tile.level.value
                    end_tile.level = BuildingLevel.EMPTY
                    destroyed.append({
                        'name': end_tile.name,
                        'owner': end_tile.owner,
                        'old': old,
                        'new': 0,
                        'extra': True
                    })

        # 日志输出
        level_names = {0: '空地', 1: '茅屋', 2: '瓦房', 3: '客栈', 4: '宫殿'}
        for d in destroyed:
            owner_name = fmt_name(d['owner'])
            old_name = level_names.get(d['old'], '建筑')
            new_name = level_names.get(d['new'], '空地')
            if d.get('extra'):
                self.log.append(f"【终点冲击】{d['name']} 被完全摧毁！")
            else:
                self.log.append(f"摧毁 {owner_name} 的{d['name']}：{old_name} → {new_name}")

        del player.status['niu_rampage']

    # 预留：技能、事件、经济、建筑升级等接口
    def use_skill(self, player, skill_name):
        pass

    def trigger_event(self, player):
        # 简易奇遇系统：根据格子五行或特殊类型触发效果
        tile = self.board.tiles[player.position]
        if tile.special == 'start':
            # self.log.append(f'{fmt_name(player)} 踏上起点，精神一振，获得500金币。')
            # player.money += 500
            return
        if tile.special == 'hospital':
            self.log.append(f'{fmt_name(player)} 进入太医院，休养生息，支付800金币。')
            player.money -= 800
            player.status['skip_turns'] = max(player.status.get('skip_turns', 0), 1)
            return
        if tile.special == 'encounter':
            # 五行奇遇（简化版，从 rules.md 中摘取部分）
            e = tile.element
            if e == Element.GOLD:
                player.money += 3000
                self.log.append(f'{fmt_name(player)} 点石成金，获得3000金币！')
            elif e == Element.WOOD:
                removed = False
                if player.status:
                    player.status.clear()
                    removed = True
                self.log.append(f'{fmt_name(player)} 枯木逢春，{"解除所有负面状态" if removed else "精神焕发"}。')
            elif e == Element.WATER:
                player.position = (player.position + 3) % len(self.board.tiles)
                self.log.append(f'{fmt_name(player)} 顺水推舟，额外前进3格至 {player.position}。')
            elif e == Element.FIRE:
                player.money -= 1000
                self.log.append(f'{fmt_name(player)} 玩火自焚，损失1000金币。')
            elif e == Element.EARTH:
                player.status['shield'] = max(player.status.get('shield', 0), 2)
                self.log.append(f'{fmt_name(player)} 稳如磐石，获得2回合保护。')
            return

    # ====== 经济：购买与升级 ======
    def current_tile(self, player):
        return self.board.tiles[player.position]

    def _is_property_tile(self, tile):
        return tile.special is None and tile.element is not None and tile.price > 0

    def can_buy(self, player):
        tile = self.current_tile(player)
        return self._is_property_tile(tile) and tile.owner is None and player.money >= tile.price

    def buy_property(self, player):
        tile = self.current_tile(player)
        if not self._is_property_tile(tile):
            self.log.append('此处不可购买。')
            return False
        if tile.owner is not None:
            self.log.append('该地皮已有主人。')
            return False
        if player.money < tile.price:
            self.log.append('资金不足，无法购买。')
            return False
        player.money -= tile.price
        tile.owner = player
        tile.level = BuildingLevel.HUT
        player.properties.append(tile.idx)
        self.log.append(f'{fmt_name(player)} 购买了「{tile.name}」，建造茅屋。')
        # 标记本回合刚购买，禁止立刻加盖
        player.status['just_bought'] = 1
        return True

    def can_upgrade(self, player):
        tile = self.current_tile(player)
        return self._is_property_tile(tile) and tile.owner is player and tile.level != BuildingLevel.PALACE

    def upgrade_cost(self, tile):
        # 简化升级费用：基础价 × (当前等级+1) × 0.6
        return int(tile.price * (tile.level.value + 1) * 0.6)

    def upgrade_building(self, player, tile=None):
        tile = tile or self.current_tile(player)
        if not (self._is_property_tile(tile) and tile.owner is player):
            self.log.append('此处不可升级。')
            return False
        if player.status.get('just_bought'):
            self.log.append('刚购买本地皮，不能立即加盖。')
            return False
        if tile.level == BuildingLevel.PALACE:
            self.log.append('已是最高等级。')
            return False
        cost = self.upgrade_cost(tile)
        if player.money < cost:
            self.log.append(f'升级所需{cost}金币，资金不足。')
            return False
        player.money -= cost
        tile.level = BuildingLevel(tile.level.value + 1)
        self.log.append(f'{fmt_name(player)} 升级了「{tile.name}」至等级{tile.level.value}。')
        return True
