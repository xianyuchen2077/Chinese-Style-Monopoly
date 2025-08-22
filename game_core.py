# game_core.py
# 游戏核心逻辑模块

import random
from enum import Enum

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
def fmt_name(player):
    """返回统一格式：[玩家名]角色名"""
    return f"[{player.name}]{EARTHLY_NAMES[player.zodiac]}"

class SkillManager:
    """每个玩家自带一个实例，负责冷却、升级与触发"""
    def __init__(self, player):
        self.player = player
        self.skills = {
            '鼠': {
                'level': SkillLevel.I,
                'cooldown': 0,
                'used': 0
            }
        }

    # ------------- 鼠 - 灵鼠窃运 ----------------
    def use_shu(self, target_player, direction):
        """
        direction: 'backward' | 'stay'
        """
        skill = self.skills['鼠']
        if skill['cooldown'] > 0:
            return False, "技能冷却中"

        level = skill['level']
        turns = 2 if level == SkillLevel.III else 1
        lock_skill = level != SkillLevel.I  # II 以上封锁技能

        target_player.status['shu_control'] = {
            'turns': turns,
            'direction': direction,
            'lock_skill': lock_skill
        }

        # 冷却
        skill['cooldown'] = 4 if level == SkillLevel.III else 3
        skill['used'] += 1
        return True, f"{self.player.name} 对 {target_player.name} 发动【灵鼠窃运】"

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

    def move_step(self, steps):
        """被控制时的特殊移动"""
        if 'shu_control' in self.status:
            ctrl = self.status['shu_control']
            if ctrl['turns'] <= 0:
                self.status.pop('shu_control', None)
                return steps

            # 执行控制
            cmd = ctrl['direction']
            if cmd == 'stay':
                steps = 0
            elif cmd == 'backward':
                steps = -steps
            # forward 不动
            ctrl['turns'] -= 1
            if ctrl['turns'] == 0:
                self.status.pop('shu_control', None)
        return steps


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

    def spin_wheel(self):
        return random.randint(1, 10)

    def move_player(self, player, steps):
        old_pos = player.position
        total_tiles = len(self.board.tiles)
        player.position = (player.position + steps) % total_tiles
        # 过起点奖励
        if player.position < old_pos:
            player.money += 5000
        return player.position

    def next_turn(self):
        # 清理上一位玩家的“刚购买”限制
        if self.players:
            prev = self.players[self.current_player_idx]
            if 'just_bought' in prev.status:
                prev.status.pop('just_bought', None)
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        self.turn += 1

        # 每回合结束自动减冷却
        for p in self.players:
            p.skill_mgr.tick_cooldown()


    # 预留：技能、事件、经济、建筑升级等接口
    def use_skill(self, player, skill_name):
        pass

    def trigger_event(self, player):
        # 简易奇遇系统：根据格子五行或特殊类型触发效果
        tile = self.board.tiles[player.position]
        if tile.special == 'start':
            self.log.append(f'{fmt_name(player)} 踏上起点，精神一振，获得500金币。')
            player.money += 500
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

    # 预留更多接口供UI调用
