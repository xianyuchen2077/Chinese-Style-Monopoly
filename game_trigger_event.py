# game_tigger_event.py
# 奇遇事件专用逻辑

import random
from typing import Dict, List
from game_core import fmt_name, Game, Player, Tile, Negative, SKILL_NAMES, BuildingLevel
from game_character_skill import SkillLevel
from enum import Enum

# 八卦枚举
class Bagua(Enum):
    QIAN = "乾"
    KUN  = "坤"
    ZHEN = "震"
    XUN  = "巽"
    KAN  = "坎"
    LI   = "离"
    GEN  = "艮"
    DUI  = "兑"

# 八卦灵气值事件表
# 文件：game_trigger_event.py
BAGUA_LINGQI_EVENTS: Dict[Bagua, List[dict]] = {
    Bagua.QIAN: [
        {"name": "云行雨施",   "desc": "品物流形",               "type": "positive"},
        {"name": "天道盈虚",   "desc": "亢龙有悔之象",           "type": "negative"},
        {"name": "飞龙在天",   "desc": "立刻获得5000金币，且下3回合移动步数+2",          "type": "positive"},
        {"name": "亢龙有悔",   "desc": "接下来3回合内，你的所有技能冷却时间减少1回合（最低为1），但每次使用技能需额外支付1000金币", "type": "negative"},
    ],
    Bagua.KUN: [
        {"name": "地载万物",   "desc": "万物资生",               "type": "positive"},
        {"name": "坤德含章",   "desc": "无成有终",               "type": "mixed"},
        {"name": "厚德载物",   "desc": "立刻修复自身所有被摧毁的建筑，每修复一个建筑获得1000金币", "type": "positive"},
        {"name": "含弘光大",   "desc": "立刻使你所有的地皮获得“孕育”状态，持续5回合。期间，这些地皮每次被收取租金时，其建筑等级有10%几率自动提升1级（最高至宫殿）", "type": "mixed"},
    ],
    Bagua.ZHEN: [
        {"name": "雷出地奋",   "desc": "豫卦之象",               "type": "positive"},
        {"name": "震惧致福",   "desc": "恐惧修省",               "type": "negative"},
        {"name": "雷霆万钧",   "desc": "所有其他玩家立刻损失1000金币",                     "type": "neutral"},
        {"name": "惊雷破茅",   "desc": "立刻使棋盘上所有建筑等级为1的房屋（茅屋）被震塌（等级降为空地）。你是此效果的源头，不受影响", "type": "neutral"},
    ],
    Bagua.XUN: [
        {"name": "随风赋灵",   "desc": "君子以申命行事",         "type": "positive"},
        {"name": "风行灵散",   "desc": "无所不入亦无所守",       "type": "negative"},
        {"name": "随风巽",     "desc": "立刻与移动方向前方最近的玩家交换位置",               "type": "positive"},
        {"name": "无孔不入",   "desc": "立刻获得一枚“风行”标记。在接下来的3回合内，你可以无视任何玩家的技能效果（包括控制、破坏、负面状态）一次", "type": "positive"},
    ],
    Bagua.KAN: [
        {"name": "坎渊悟道",   "desc": "维心亨行有尚",           "type": "positive"},
        {"name": "水流灵逝",   "desc": "习坎失道",               "type": "negative"},
        {"name": "坎陷重重",   "desc": "位于你后方3格内的所有其他玩家停止一回合",             "type": "negative"},
        {"name": "水洊至习坎", "desc": "立刻在你的当前位置召唤一个持续2回合的“险陷”区域。其他玩家移动进入或经过此区域时，有50%几率被困原地1回合", "type": "negative"},
    ],
    Bagua.LI: [
        {"name": "离明顿悟",   "desc": "大人以继明照于四方",     "type": "positive"},
        {"name": "火焚灵耗",   "desc": "突如其来如焚如",         "type": "negative"},
        {"name": "离明火光",   "desc": "立刻随机升级自身2块地皮的建筑1个等级",               "type": "positive"},
        {"name": "突如其来", "desc": "立刻随机选择一名其他玩家，其所有地皮上的建筑等级临时-1（持续3回合），且这些地皮在此期间产生的租金将支付给你", "type": "negative"},
    ],
    Bagua.GEN: [
        {"name": "艮止凝元",   "desc": "君子以思不出其位",       "type": "positive"},
        {"name": "山止灵滞",   "desc": "时止则止时行则行",       "type": "negative"},
        {"name": "艮止如山",   "desc": "接下来3次受到的租金或伤害减半",                       "type": "positive"},
        {"name": "时行则行",   "desc": "立刻进入“蛰伏”状态，持续2回合。期间你无法移动，但免疫所有伤害和负面效果，且每回合自动恢复1000金币和300点灵气值", "type": "positive"},
    ],
    Bagua.DUI: [
        {"name": "兑言纳灵",   "desc": "君子以朋友讲习",         "type": "positive"},
        {"name": "泽涸灵枯",   "desc": "孚于剥位正当也",         "type": "negative"},
        {"name": "兑言喜悦",   "desc": "你下一个完成的任务，额外获得2点任务分数",               "type": "positive"},
        {"name": "朋友讲习",   "desc": "立刻选择一名其他玩家，与其结为“盟友”，持续5回合。期间，你们双方共享任务进度（一方完成任务，另一方也视为完成），但任务奖励各自获得一份", "type": "positive"},
    ],
}

# ---------- 八卦灵气事件对外接口 ----------
def trigger_bagua_encounter(game: Game, player: Player, tile: Tile):
    """踩到八卦格时调用"""
    if tile.bagua is None:
        return

    bagua = tile.bagua
    roll = random.random()
    # 25% 概率四选一
    if bagua.value == "乾":
        if roll < 0.25:
            _handle_qian_1(game, player)
        elif roll < 0.5:
            _handle_qian_2(game, player)
        elif roll < 0.75:
            _handle_qian_3(game, player)
        else:
            _handle_qian_4(game, player)
    elif bagua.value == "坤":
        if roll < 0.25:
            _handle_kun_1(game, player)
        elif roll < 0.5:
            _handle_kun_2(game, player)
        elif roll < 0.75:
            _handle_kun_3(game, player)
        else:
            _handle_kun_4(game, player)
    elif bagua.value == "震":
        if roll < 0.25:
            _handle_zhen_1(game, player)
        elif roll < 0.5:
            _handle_zhen_2(game, player)
        elif roll < 0.75:
            _handle_zhen_3(game, player)
        else:
            _handle_zhen_4(game, player)
    elif bagua.value == "巽":
        if roll < 0.25:
            _handle_xun_1(game, player)
        elif roll < 0.5:
            _handle_xun_2(game, player)
        elif roll < 0.75:
            _handle_xun_3(game, player)
        else:
            _handle_xun_4(game, player)
    elif bagua.value == "坎":
        if roll < 0.25:
            _handle_kan_1(game, player)
        elif roll < 0.5:
            _handle_kan_2(game, player)
        elif roll < 0.75:
            _handle_kan_3(game, player)
        else:
            _handle_kan_4(game, player)
    elif bagua.value == "离":
        if roll < 0.25:
            _handle_li_1(game, player)
        elif roll < 0.5:
            _handle_li_2(game, player)
        elif roll < 0.75:
            _handle_li_3(game, player)
        else:
            _handle_li_4(game, player)
    elif bagua.value == "艮":
        if roll < 0.25:
            _handle_gen_1(game, player)
        elif roll < 0.5:
            _handle_gen_2(game, player)
        elif roll < 0.75:
            _handle_gen_3(game, player)
        else:
            _handle_gen_4(game, player)
    elif bagua.value == "兑":
        if roll < 0.25:
            _handle_dui_1(game, player)
        elif roll < 0.5:
            _handle_dui_2(game, player)
        elif roll < 0.75:
            _handle_dui_3(game, player)
        else:
            _handle_dui_4(game, player)

# ---------- 八卦灵气值事件具体实现 ----------
# ---------- 乾卦专用处理 ----------
def _handle_qian_1(game: Game, player: Player):
    """云行雨施：立刻 +500 灵气，后续 3 回合每回合 +100"""
    gain = player.add_energy(500)
    game.log.append(f"{fmt_name(player)} 触发【乾·云行雨施】：立刻获得 {gain} 灵气！")
    # 后续 3 回合
    for i in range(1, 4):
        player.status.setdefault("energy_events", []).append((i , "energy", 100, "乾·云行雨施"))
    game.log.append(f"后续 3 回合每回合返还 100 灵气")

def _handle_qian_2(game: Game, player: Player):
    """天道盈虚：清零当前灵气，3 回合后返还 50%"""
    lost = player.energy
    lost = -player.add_energy(-lost)
    game.log.append(f"{fmt_name(player)} 触发【乾·天道盈虚】：灵气清零（损失 {lost} 点）！")
    # 3 回合后返还 50%
    refund = lost // 2
    player.status.setdefault("energy_events", []).append((3, "energy", refund, "乾·天道盈虚"))
    game.log.append(f"3 个回合后将返还 {refund} 灵气")

def _handle_qian_3(game: Game, player: Player):
    """飞龙在天：立刻获得5000金币，且下3回合移动步数+2"""
    gain = player.add_money(5000)
    game.log.append(f"{fmt_name(player)} 触发【乾·飞龙在天】：立刻获得 {gain} 金币！")
    # 后续 3 回合移动额外 +2
    for i in range(1, 4):
        player.status.setdefault("energy_events", []).append((i, "move", 2, "乾·飞龙在天"))
    game.log.append(f"后续 3 回合移动步数 +2")

def _handle_qian_4(game: Game, player: Player):
    """亢龙有悔：接下来3回合内，所有技能冷却-1（最低1），但每次使用技能额外支付1000金币"""
    # 后续 3 回合技能冷却 -1 但使用技能时需要额外支付 1000
    for i in range(1, 4):
        player.status.setdefault("energy_events", []).append((i, "skill", "", 1000, "乾·亢龙有悔"))
    game.log.append(f"{fmt_name(player)} 触发【乾·亢龙有悔】：")
    game.log.append(f"接下来 3 回合内，所有技能冷却-1（最低1），但每次使用技能需额外支付 1000 金币！")

# ---------- 坤卦专用处理 ----------
def _handle_kun_1(game: Game, player: Player):
    """地载万物：立刻获得 (地皮数量 × 50) 灵气"""
    tiles_owned = len(player.properties)
    gain = tiles_owned * 50
    gain = player.add_energy(gain)
    game.log.append(f"{fmt_name(player)} 触发【坤·地载万物】：拥有 {tiles_owned} 块地皮，获得 {gain} 灵气！")

def _handle_kun_2(game: Game, player: Player):
    """坤德含章：将当前金币的5%转化为灵气"""
    convert = int(player.money * 0.05)
    gain = player.add_energy(convert)
    player.add_money(-convert)
    player.status["no_money_this_turn"] = 1
    player.status.setdefault("energy_events", []).append((1, "money", 1, "坤·坤德含章"))    # 标记下回合无法获得金币
    game.log.append(f"{fmt_name(player)} 触发【坤·坤德含章】：消耗 {gain} 金币，转化为 {gain} 灵气！")

def _handle_kun_3(game: Game, player: Player):
    """厚德载物：立刻修复自身所有被摧毁（曾经有过房子而如今变成空地）的建筑，每修复一个建筑获得1000金币"""
    to_fix = list(player.destroyed_tiles)   # 先拷贝1，避免在遍历集合的同时又修改集合
    repaired = 0

    for idx in player.properties and to_fix:
        tile = game.board.tiles[idx]
        if tile.level == BuildingLevel.EMPTY and tile.owner == player:
            tile.level = BuildingLevel.HUT
            player.destroyed_tiles.discard(idx)  # 移出“被破坏”集合
            repaired += 1
            game.log.append(f"{fmt_name(player)} 触发【坤·厚德载物】：修复【{tile.name}】至茅屋")

    if repaired:
        gain = repaired * 1000
        gain = player.add_money(gain)
        game.log.append(f"{fmt_name(player)} 因修复 {repaired} 个建筑，获得 {gain} 金币！")
    else:
        game.log.append(f"{fmt_name(player)} 触发【坤·厚德载物】：无建筑需要修复")

def _handle_kun_4(game: Game, player: Player):
    """含弘光大：使所有地皮进入孕育状态，持续5回合，期间被收租时10%概率升1级"""
    player.status["kun_pregnancy"] = 5  # 立即生效，持续5个大回合
    game.log.append(f"{fmt_name(player)} 触发【坤·含弘光大】：")
    game.log.append(f"所有地皮进入孕育状态，持续5个大回合，被收租时10%几率升级！")

# ---------- 震卦专用处理 ----------
def _handle_zhen_1(game: Game, player: Player):
    """雷出地奋：立刻获得400点灵气值，并随机震慑一名其他玩家，使其下次获得的灵气值减半。"""
    player.add_energy(400)

    # 随机选择一个其他玩家
    target = game.choose_target_player(player)
    if target:
        target.status["zhen_shocked"] = 1
        game.log.append(f"{fmt_name(player)} 触发【震·雷出地奋】：获得 400 灵气，")
        game.log.append(f"并震慑 {fmt_name(target)}，其下次灵气收益减半！")
    else:
        game.log.append(f"{fmt_name(player)} 触发【震·雷出地奋】：获得 400 灵气，")
        game.log.append(f"但无其他玩家可震慑...")

def _handle_zhen_2(game: Game, player: Player):
    """震惧致福：立刻损失250点灵气值(清零为止)，
    但接下来2回合内，每次受到伤害或负面效果时，获得50点灵气值。"""
    lost = min(250, player.energy)
    player.add_energy(-lost)

    for i in range(1, 3):
        player.status.setdefault("energy_events", []).append((i, "energy", 50, "震·震惧致福"))
    game.log.append(f"{fmt_name(player)} 触发【震·震惧致福】：损失 {lost} 灵气，")
    game.log.append(f"未来 2 回合内每次受负面效果将补偿 50 灵气！")

def _handle_zhen_3(game: Game, player: Player):
    """雷霆万钧：所有其他玩家立刻损失1000金币"""
    for p in game.players:
        if p is player:
            game.log.append(f"{fmt_name(player)} 触发【震·雷霆万钧】：使所有其他玩家立刻损失1000金币")
            continue
        lost = min(1000, p.money)
        lost = p.add_money(-lost)
        game.log.append(f"{fmt_name(player)} 遭受【震·雷霆万钧】：{fmt_name(p)} 损失 {lost} 金币！")
    game.log.append("【雷霆万钧】效果结束。")

def _handle_zhen_4(game: Game, player: Player):
    """惊雷破茅：所有建筑等级为1（茅屋）的房屋被震塌"""
    destroyed = 0
    for tile in game.board.tiles:
        if tile.level == BuildingLevel.HUT:
            tile.level = BuildingLevel.EMPTY
            if tile.owner is not None:
                tile.owner.destroyed_tiles.add(tile.idx)
            destroyed += 1
            game.log.append(f"{fmt_name(player)} 触发【震·惊雷破茅】：{fmt_name(tile.owner)} 的「{tile.name}」被震塌！")
    if destroyed == 0:
        game.log.append("【惊雷破茅】触发，但当前没有茅屋可震塌。")

# ---------- 巽卦专用处理 ----------
def _handle_xun_1(game: Game, player: Player):
    """巽·随风赋灵：复制灵气值最高的其他玩家的 20% 的灵气值"""
    # 找灵气最高的其他玩家
    candidates = [p for p in game.players if p != player and p.energy > 0]
    if not candidates:
        game.log.append(f"{fmt_name(player)} 触发【巽·随风赋灵】：无其他玩家可汲取灵气。")
        return
    richest = max(candidates, key=lambda p: p.energy)
    gain = richest.energy // 5
    gain = player.add_energy(gain)
    game.log.append(f"{fmt_name(player)} 触发【巽·随风赋灵】：复制 {fmt_name(richest)} 20% 灵气，获得 {gain}！")

def _handle_xun_2(game: Game, player: Player):
    """巽·风行灵散：立刻损失当前灵气值的 25%（向下取整），但下次移动步数+3"""
    lost = player.energy // 4
    lost = -player.add_energy(-lost)
    game.log.append(f"{fmt_name(player)} 触发【巽·风行灵散巽·风行灵散】：损失 {lost} 灵气，")
    player.status.setdefault("energy_events", []).append((1, "move", 3, "巽·风行灵散")) # 仅影响下回合
    game.log.append(f"但下次移动额外 +3 步！")

def _handle_xun_3(game: Game, player: Player):
    """随风巽：立刻与移动方向前方最近的玩家交换位置"""
    board_len = len(game.board.tiles)
    step = 1 if player.clockwise else -1
    current = player.position

    # 向前搜索最近的其他玩家
    for offset in range(1, board_len):
        idx = (current + offset * step) % board_len
        target = next((p for p in game.players if p.position == idx), None)
        if target is not None and target is not player:
            # 交换位置
            player.position, target.position = target.position, player.position
            game.log.append(f"{fmt_name(player)} 触发【巽·随风巽】：与前方最近的玩家 {fmt_name(target)} 交换位置！")
            return

    game.log.append(f"{fmt_name(player)} 触发【巽·随风巽】：前方没有其他玩家，位置不变。")

def _handle_xun_4(game: Game, player: Player):
    """无孔不入：立刻获得一枚“风行”标记，3 回合内可无视一次任何玩家技能效果"""
    player.status["defence_skill_once"] = 3      # 持续 3 大回合
    for i in range(1, 3):   # 从这个回合就开始，所以需要 -1
        player.status.setdefault("energy_events", []).append((i, "defence", 1, "巽·无孔不入"))
    game.log.append(f"{fmt_name(player)} 触发【巽·无孔不入】：获得“风行”标记，")
    game.log.append(f"未来 3 回合内可无视一次任何玩家技能效果！")

# ---------- 坎卦专用处理 ----------
def _handle_kan_1(game: Game, player: Player):
    """坎渊悟道：已陷入负面状态数量 × 200 灵气"""
    negative_count = len([k for k in player.status.keys() if k in Negative])
    gain = negative_count * 200
    gain = player.add_energy(gain)
    game.log.append(f"{fmt_name(player)} 触发【坎·坎渊悟道】：身陷 {negative_count} 种负面状态，获得 {gain} 灵气！")

def _handle_kan_2(game: Game, player: Player):
    """水流灵逝：损失 300 灵气并被额外禁锢1回合"""
    lost = min(300, player.energy)
    lost = -player.add_energy(-lost)
    player.status["skip_turns"] = player.status.get("skip_turns", 0) + 1
    game.log.append(f"{fmt_name(player)} 触发【坎·水流灵逝】：损失 {lost} 灵气并被额外禁锢 1 回合！")

def _handle_kan_3(game: Game, player: Player):
    """坎陷重重：位于玩家后方12格内的所有其他玩家停止一回合"""
    board_len = len(game.board.tiles)
    step = -1 if player.clockwise else 1  # 与玩家当前方向相反 = 后方
    trapped = []

    for p in game.players:
        if p == player:
            continue
        # 计算“后方 12 格”
        for offset in range(1, 13):
            idx = (player.position + offset * step) % board_len
            if p.position == idx:
                p.status["skip_turns"] = max(p.status.get("skip_turns", 0), 1)
                trapped.append(fmt_name(p))
                break

    if trapped:
        names = ",".join(trapped)
        game.log.append(f"{fmt_name(player)} 触发【坎·坎陷重重】：{names} 被迫停止一回合！")
    else:
        game.log.append(f"{fmt_name(player)} 触发【坎·坎陷重重】：后方 12 格内无其他玩家。")

def _handle_kan_4(game: Game, player: Player):
    """水洊至习坎：在当前格子召唤“险陷”区域，持续2回合"""
    tile = game.board.tiles[player.position]
    tile.special = "negative"
    tile.status["cracked"] = 2 * len(game.players)   # 2 个大回合
    game.log.append(f"{fmt_name(player)} 触发【坎·水洊至习坎】：格子 {player.position} 出现险陷区域,")
    game.log.append(f"有 50 %概率塌陷，让玩家滞留 1 回合")
    game.log.append(f"该效果持续 2 回合！")

# ---------- 离卦专用处理 ----------
def _handle_li_1(game: Game, player: Player):
    """离明顿悟：最高建筑等级 × 250 灵气"""
    max_level = max((game.board.tiles[i].level.value for i in player.properties), default=0)
    gain = max_level * 250
    player.add_energy(gain)
    game.log.append(f"{fmt_name(player)} 触发【离·离明顿悟】：最高建筑等级 {max_level}，")
    game.log.append(f"获得 {gain} 灵气！")

def _handle_li_2(game: Game, player: Player):
    """火焚灵耗：损失 350 灵气，随机技能-1级,3回合后恢复"""
    lost = min(350, player.energy)
    player.add_energy(-lost)

    # 只拿当前玩家真正学过的技能（已解锁且等级 > 1）
    mgr = player.skill_mgr
    zodiac = player.zodiac
    skill = mgr.skills.get(zodiac)
    if skill is None or skill['level'].value <= 1:
        game.log.append(f"{fmt_name(player)} 触发【离·火焚灵耗】：损失 350 灵气，")
        game.log.append(f"无技能可被降级！")
        return

    original_level = skill['level']
    skill['level'] = SkillLevel(original_level.value - 1)
    game.log.append(f"{fmt_name(player)} 触发【离·火焚灵耗】：损失 350 灵气，")
    game.log.append(f"技能【{SKILL_NAMES[zodiac]}】等级暂时降至 {skill['level'].name}，")
    game.log.append(f"该效果持续 3 回合！")

    # 登记 3 回合后恢复（延迟队列）
    player.status.setdefault("energy_events", []).append((3 , "skill", zodiac, original_level, "离·火焚灵耗"))  # 从当前回合开始算起

def _handle_li_3(game: Game, player: Player):
    """离明火光：立刻随机升级自身 2 块地皮的建筑 1 个等级"""
    candidates = [idx for idx in player.properties if game.board.tiles[idx].level != BuildingLevel.PALACE]
    if not candidates:
        game.log.append(f"{fmt_name(player)} 触发【离·离明火光】：无可升级地皮")
        return

    chosen = random.sample(candidates, min(2, len(candidates)))
    for idx in chosen:
        tile = game.board.tiles[idx]
        old = tile.level
        tile.level = BuildingLevel(old.value + 1)
        game.log.append(f"{fmt_name(player)} 触发【离·离明火光】：升级「{tile.name}」")
        game.log.append(f" {old.name} → {tile.level.name}")

def _handle_li_4(game: Game, player: Player):
    """突如其来如：随机一名其他玩家所有建筑-1 级 3 回合，期间租金归触发者"""
    targets = [p for p in game.players if p != player and p.properties]
    if not targets:
        game.log.append(f"{fmt_name(player)} 触发【离·突如其来】：无其他玩家可选")
        return

    victim = random.choice(targets)

    # 立即降级并记录租金归属
    downgraded = []
    for idx in victim.properties:
        tile = game.board.tiles[idx]
        if tile.level.value > 0:             # 不降至空地以下
            tile.level = BuildingLevel(tile.level.value - 1)
            tile.special = "negative"
            tile.status["stolen_rent"] = 3 * len(game.players)   # 3 个大回合
            tile.status["stolen_rent_thief"] = player
            downgraded.append(idx)

    if not downgraded:
        game.log.append(f"{fmt_name(player)} 触发【离·突如其来】：{fmt_name(victim)} 无可降级建筑")
        return

    game.log.append(f"{fmt_name(player)} 触发【离·突如其来】：")
    game.log.append(f"{fmt_name(victim)} 的 {len(downgraded)} 块地皮等级-1，")
    game.log.append(f"持续 3 回合，期间租金归 {fmt_name(player)}")

# ---------- 艮卦专用处理 ----------
def _handle_gen_1(game: Game, player: Player):
    """艮止凝元：回合数 × 30 灵气，上限600"""
    gain = min(game.game_turn * 30, 600)
    gain = player.add_energy(gain)
    game.log.append(f"{fmt_name(player)} 触发【艮·艮止凝元】：回合沉淀，获得 {gain} 灵气！")

def _handle_gen_2(game: Game, player: Player):
    """山止灵滞：2 回合无法获得灵气，但租金 -30%"""
    player.status["gen_rent_discount"] = 0.7        # 支付 70 %
    player.status["no_energy_this_turn"] = 2        # 两个回合
    player.status["rent_discount"] = 2
    player.status.setdefault("energy_events", []).append((1, "energy", 2, "艮·山止灵滞"))    # 标记下两回合无法获得灵气
    game.log.append(f"{fmt_name(player)} 触发【艮·山止灵滞】：2 回合内无法获得灵气，但期间租金减免 30%！")

def _handle_gen_3(game: Game, player: Player):
    """艮止如山：接下来 3 次的金币或灵气减少的效果减半"""
    player.status["gen_reduce_damage"] = 3      # 剩余次数
    player.status["gen_damage_discount"] = 0.5
    game.log.append(f"{fmt_name(player)} 触发【艮·艮止如山】：")
    game.log.append(f"接下来 3 次的金币或灵气减少时效果减半！")

def _handle_gen_4(game: Game, player: Player):
    """时行则行：蛰伏 2 回合，免伤免负面，每回合 + 1000 金 + 100 灵气"""
    player.status["hibernate"] = 3   # 2 大回合
    for i in range(1,3):
        player.status.setdefault("energy_events", []).append((i, "defence", 1000, "艮·时行则行"))
    game.log.append(f"{fmt_name(player)} 触发【艮·时行则行】：")
    game.log.append(f"进入蛰伏状态 2 回合，期间免伤免负面，每回合恢复 1000 金币 100 灵气！")

    # 从当前回合算起
    game.log.append(f"{fmt_name(player)} 本回合处于【蛰伏】状态")
    game.log.append(f"每回合获得 1000 金币和 100 灵气")
    gain_1 = player.add_money(1000)
    gain_2 = player.add_energy(100)
    game.log.append(f"{fmt_name(player)} 本回合获得 {gain_1} 金币和 {gain_2} 灵气")

# ---------- 兑卦专用处理 ----------
def _handle_dui_1(game: Game, player: Player):
    """兑言纳灵：玩家总数 × 150 灵气"""
    gain = len(game.players) * 150
    gain = player.add_energy(gain)
    game.log.append(f"{fmt_name(player)} 触发【兑·兑言纳灵】：众友讲习，获得 {gain} 灵气！")

def _handle_dui_2(game: Game, player: Player):
    """泽涸灵枯：-30% 灵气且下回合无法使用技能"""
    lost = player.energy * 3 // 10
    lost = -player.add_energy(-lost)
    player.status.setdefault("energy_events", []).append((1, "skill", "", 0, "兑·泽涸灵枯"))    # 下个大回合
    game.log.append(f"{fmt_name(player)} 触发【兑·泽涸灵枯】：流失 {lost} 灵气，下回合无法使用技能！")

def _handle_dui_3(game: Game, player: Player):
    """欣悦交融：立刻与一名随机的其他玩家进行一项“公平交易”：交换各自当前灵气值总量的75%（向下取整）"""
    candidates = [p for p in game.players if p != player]
    if not candidates:
        game.log.append(f"{fmt_name(player)} 触发【兑·欣悦交融】：无其他玩家可交易。")
        return

    target = random.choice(candidates)
    give_amount = player.energy * 3// 4
    receive_amount = target.energy * 3 // 4

    # 实际交换
    give_amount_1 = -player.add_energy(-give_amount)
    give_amount_2 = -target.add_energy(-receive_amount)
    receive_amount_1 = player.add_energy(receive_amount)
    receive_amount_2 = target.add_energy(give_amount)

    game.log.append(f"{fmt_name(player)} 触发【兑·欣悦交融】：")
    game.log.append(f"与 {fmt_name(target)} 进行灵气交易：")
    game.log.append(f"【{player.name}】送出 {give_amount_1} 灵气，获得 {receive_amount_1} 灵气")
    game.log.append(f"【{target.name}】送出 {give_amount_2} 灵气，获得 {receive_amount_2} 灵气")

def _handle_dui_4(game: Game, player: Player):
    """言泉流金：立刻免费升级你的一块地皮建筑1个等级（最高至宫殿），并支付该地皮基础地价的金币"""
    candidates = [idx for idx in player.properties if game.board.tiles[idx].level != BuildingLevel.PALACE]
    if not candidates:
        game.log.append(f"{fmt_name(player)} 触发【兑·言泉流金】：无可升级地皮")
        return

    idx = random.choice(candidates)
    tile = game.board.tiles[idx]
    cost = tile.price  # 基础地价作为代价

    if player.money < cost:
        game.log.append(f"{fmt_name(player)} 触发【兑·言泉流金】：资金不足，无法支付 {cost} 金币升级【{tile.name}】")
        return

    old_level = tile.level
    tile.level = BuildingLevel(old_level.value + 1)
    cost = -player.add_money(-cost)

    game.log.append(f"{fmt_name(player)} 触发【兑·言泉流金】：")
    game.log.append(f"支付 {cost} 金币，将【{tile.name}】从 {old_level.name} 升级至 {tile.level.name}")
