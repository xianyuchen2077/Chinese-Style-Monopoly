# game_character_skill.py
# 游戏角色技能模块

import random
from enum import Enum

def fmt_name(player, tag: str = "") -> str:
    """
    返回统一格式：[玩家名]角色名
    寅虎分身回合时追加【阴】【阳】
    """
    from game_core import EARTHLY_NAMES
    base = f"[{player.name}]{EARTHLY_NAMES[player.zodiac]}"
    if player.zodiac == '虎' and tag:          # 仅在分身回合
        mark = '阳' if tag == 'main' else '阴'
        return f"{base}【{mark}】"
    return base

# 技能等级
class SkillLevel(Enum):
    I = 1
    II = 2
    III = 3

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

# ===== 寅虎技能数据结构 =====
SKILL_HU = {
    'level': SkillLevel.I,
    'cooldown': 0,
    'used': 0,
    'split_turns': 0,       # 分身剩余回合数
    'clone_position': None, # 分身位置
    'can_merge': False      # 是否可以主动合体
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
        self.can_use_skill = True
        self.cooldown_buff = 0
        self.skills = {
            '鼠': SKILL_SHU.copy(),
            '牛': SKILL_NIU.copy(),
            '虎': SKILL_HU.copy(),
            '兔': SKILL_RABBIT.copy(),
            '羊': SKILL_YANG.copy(),
            '鸡': SKILL_JI.copy()
        }

    def can_use_active_skill(self):
        if not self.can_use_skill:
            return False
        z = self.player.zodiac
        if z in self.skills:
            return self.skills[z]['cooldown'] == 0
        return False

    def set_skill_cooldown(self):
        z = self.player.zodiac
        skill = self.skills[z]
        level = skill['level']
        if z == '鼠':
            skill['cooldown'] = 4 if level == SkillLevel.III else 3
        elif z == '牛':
            skill['cooldown'] = 3
        elif z == '虎':
            skill['cooldown'] = 4 if level == SkillLevel.III else 3
        elif z == '兔':
            skill['cooldown'] = 3
        elif z == '龙':
            pass
        elif z == '蛇':
            pass
        elif z == '马':
            pass                        # 被动技能，无冷却
        elif z == '羊':
            skill['cooldown'] = 5
        elif z == '猴':
            pass
        elif z == '鸡':
            skill['cooldown'] = 3
        elif z == '狗':
            pass                        # 被动技能，无冷却
        elif z == '猪':
            skill['cooldown'] = 2

        # 考虑cooldown_buff的增、减益效果
        skill['cooldown'] += self.cooldown_buff

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
        elif z == '虎':
            return self.use_hu(target_list, option, game)
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
        子鼠技能——灵鼠窃运：指定一名其他玩家，控制其下一回合的移动方向（可强制其向反方向移动或原地停留），高级技能可以进行除移动外的其他操作
        """
        from game_core import Player

        if not target_list:
            return False, "未选择目标"

        skill = self.skills['鼠']
        if skill['cooldown'] > 0:
            return False, "【灵鼠窃运】技能冷却中"

        level = skill['level']
        if level != SkillLevel.III and len(target_list) != 1:          # 等级 I和II 仅允许 1 个目标
            return False, "等级 I / II：必须且只能指定一名目标玩家"
        elif level == SkillLevel.III and len(target_list) != 2:
            return False, "等级 III：必须且只能指定两名目标玩家"
        turns = 2 if level == SkillLevel.III else 1 # 只有III级可以操控两个回合
        lock_skill = (level == SkillLevel.II)         # 技能等级II级能够封锁技能
        skip_turn = (level == SkillLevel.III)         # 技能等级III级能够跳过回合

        names = ",".join(fmt_name(p) for p in target_list)

        # 支持多目标
        for target in target_list:
            assert isinstance(target, Player)
            if not target.can_be_skill_targeted():
                return False, f"{self.player.name} 无法对 [{names}] 发动【灵鼠窃运】"
            if direction == 'backward':     # 反向
                target.status['puppet'] = {
                    'turns': turns,
                    'direction': 'backward',
                    'lock_skill': lock_skill,
                    'skip_turn': skip_turn
                }
            elif direction == 'stay':       # 原地停留
                target.status['puppet'] = {
                    'turns': turns,
                    'direction': 'stay',
                    'lock_skill': lock_skill,
                    'skip_turn': skip_turn
                }
                target.can_move = False

        # 技能冷却
        self.set_skill_cooldown()
        skill['used'] += 1

        return True, f"{self.player.name} 对 [{names}] 发动【灵鼠窃运】"

    def upgrade_shu(self):
        skill = self.skills['鼠']
        lvl, used, eng = skill['level'], skill['used'], self.player.energy

        # 升级 I→II
        if lvl == SkillLevel.I and used >= 3 and eng >= 100:
            skill['level'] = SkillLevel.II
            self.player.energy -= 100
            return True

        # 升级 II→III
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

        self.set_skill_cooldown()
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

    # ------------- 虎 - 猛虎分身 ----------------
    def use_hu(self, target_list=None, option=None, game=None) -> tuple[bool, str]:
        """
        寅虎·猛虎分身
        option 可包含 {'action': 'split'/'merge', 'merge_to': 'main'/'clone'}
        game   : Game 实例
        """
        if game is None:
            return False, "需要传递游戏实例参数"

        skill = self.skills['虎']
        level = skill['level']

    # Ⅲ 级手动合体（队列外触发）
        if option and option.get('action') == 'merge':
            if level == SkillLevel.III:
                merge_target = option.get('merge_to', 'main')
                return self._merge_clones(merge_target)
            return False, "当前等级不支持主动合体"

        # 技能冷却
        if skill['cooldown'] > 0:
            return False, "【猛虎分身】冷却中"

        # 生成两个独立子回合
        game.tiger_sub_turns = [(self.player, "clone")]
        self.set_skill_cooldown()
        skill['split_turns'] = 2 if level == SkillLevel.I else 3
        skill['used'] += 1
        skill['clone_position'] = self.player.position
        self.player.clone_idx = self.player.position   # 分身出生位置

        # 状态
        self.player.status['tiger_split'] = {
            'level': level,
            'damage_reduction': {SkillLevel.I: 0.0, SkillLevel.II: 0.5, SkillLevel.III: 0.8}[level],
            'reward_multiplier': {SkillLevel.I: 0.5, SkillLevel.II: 1.0, SkillLevel.III: 1.5}[level],
            'can_merge': (level == SkillLevel.III)
        }

        return True, f"{fmt_name(self.player)} 发动【猛虎分身】，即将进入双身循环"

    def _merge_clones(self, merge_to: str) -> tuple[bool, str]:
        """
        合体逻辑：
        merge_to='main' → 合体到主体【阳】所在格子
        merge_to='clone'→ 合体到分身【阴】所在格子
        """
        skill = self.skills['虎']
        skill_level = skill['level']

        # 计算最终落点
        if merge_to == 'clone' and skill['clone_position'] is not None:
            final_pos = skill['clone_position']
            mark = '阴'
        else:                       # 默认合体到主体（阳）
            final_pos = self.player.position
            mark = '阳'

        # 更新玩家位置
        self.player.position = final_pos

        # 统一清理
        skill['split_turns'] = 0
        skill['clone_position'] = None
        self.player.clone_idx = None          # 合体后消失
        skill['can_merge'] = False
        self.player.status.pop('tiger_split', None)

        return True, f"{fmt_name(self.player)} 合体到【{mark}】位置 {final_pos}"

    def upgrade_hu(self) -> bool:
        skill = self.skills['虎']
        lvl, used, eng = skill['level'], skill['used'], self.player.energy
        if lvl == SkillLevel.I and used >= 2 and eng >= 200:
            skill['level'] = SkillLevel.II
            self.player.energy -= 200
            return True
        if lvl == SkillLevel.II and used >= 4 and eng >= 400:
            skill['level'] = SkillLevel.III
            self.player.energy -= 400
            return True
        return False

    # ------------- 兔 - 玉兔疾行 ----------------
    def use_tu(self, target_list=None, option=None):
        skill = self.skills['兔']
        if skill['cooldown'] > 0:
            return False, "【玉兔疾行】冷却中"
        skill['active'] = True
        skill['used'] += 1
        self.set_skill_cooldown()
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
            self.set_skill_cooldown()
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
        from game_core import BuildingLevel

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
        self.set_skill_cooldown()
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