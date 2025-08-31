# game_tigger_event.py
# 奇遇事件专用逻辑

import random
from typing import Dict, List
from game_core import fmt_name, Game, Player, Tile, SkillLevel
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
BAGUA_LINGQI_EVENTS: Dict[Bagua, List[dict]] = {
    Bagua.QIAN: [
        {"name": "云行雨施", "desc": "品物流形", "type": "positive"},
        {"name": "天道盈虚", "desc": "亢龙有悔之象", "type": "negative"},
    ],
    Bagua.KUN: [
        {"name": "地载万物", "desc": "万物资生", "type": "positive"},
        {"name": "坤德含章", "desc": "无成有终", "type": "mixed"},
    ],
    Bagua.ZHEN: [
        {"name": "雷出地奋", "desc": "豫卦之象", "type": "positive"},
        {"name": "震惧致福", "desc": "恐惧修省", "type": "negative"},
    ],
    Bagua.XUN: [
        {"name": "随风赋灵", "desc": "君子以申命行事", "type": "positive"},
        {"name": "风行灵散", "desc": "无所不入亦无所守", "type": "negative"},
    ],
    Bagua.KAN: [
        {"name": "坎渊悟道", "desc": "维心亨行有尚", "type": "positive"},
        {"name": "水流灵逝", "desc": "习坎失道", "type": "negative"},
    ],
    Bagua.LI: [
        {"name": "离明顿悟", "desc": "大人以继明照于四方", "type": "positive"},
        {"name": "火焚灵耗", "desc": "突如其来如焚如", "type": "negative"},
    ],
    Bagua.GEN: [
        {"name": "艮止凝元", "desc": "君子以思不出其位", "type": "positive"},
        {"name": "山止灵滞", "desc": "时止则止时行则行", "type": "negative"},
    ],
    Bagua.DUI: [
        {"name": "兑言纳灵", "desc": "君子以朋友讲习", "type": "positive"},
        {"name": "泽涸灵枯", "desc": "孚于剥位正当也", "type": "negative"},
    ],
}

# ---------- 八卦灵气事件对外接口 ----------
def trigger_bagua_lingqi_encounter(game: Game, player: Player, tile: Tile):
    """踩到八卦格时调用"""
    if tile.bagua is None:
        return

    bagua = tile.bagua
    # 50% 概率二选一
    if bagua.value == "乾":
        if random.random() < 0.5:
            _handle_qian_1(game, player)
        else:
            _handle_qian_2(game, player)
    elif bagua.value == "坤":
        if random.random() < 0.5:
            _handle_kun_1(game, player)
        else:
            _handle_kun_2(game, player)
    elif bagua.value == "震":
        if random.random() < 0.5:
            _handle_zhen_1(game, player)
        else:
            _handle_zhen_2(game, player)
    elif bagua.value == "巽":
        if random.random() < 0.5:
            _handle_xun_1(game, player)
        else:
            _handle_xun_2(game, player)
    elif bagua.value == "坎":
        if random.random() < 0.5:
            _handle_kan_1(game, player)
        else:
            _handle_kan_2(game, player)
    elif bagua.value == "离":
        if random.random() < 0.5:
            _handle_li_1(game, player)
        else:
            _handle_li_2(game, player)
    elif bagua.value == "艮":
        if random.random() < 0.5:
            _handle_gen_1(game, player)
        else:
            _handle_gen_2(game, player)
    elif bagua.value == "兑":
        if random.random() < 0.5:
            _handle_dui_1(game, player)
        else:
            _handle_dui_2(game, player)

# ---------- 八卦灵气值事件具体实现 ----------
# ---------- 乾卦专用处理 ----------
def _handle_qian_1(game: Game, player: Player):
    """云行雨施：立刻 +500 灵气，后续 3 回合每回合 +100"""
    gain = player.add_energy(500)
    game.log.append(f"{fmt_name(player)} 触发【乾·云行雨施】：立刻获得 {gain} 灵气！")
    # 后续 3 回合
    for i in range(2, 5):   # 在这个回合就会先-1
        player.status.setdefault("energy_events", []).append((i * len(game.players), 100, "乾·云行雨施"))
    game.log.append(f"后续 3 回合每回合返还 100 灵气")

def _handle_qian_2(game: Game, player: Player):
    """天道盈虚：清零当前灵气，3 回合后返还 50%"""
    lost = player.energy
    lost = -player.add_energy(-lost)
    game.log.append(f"{fmt_name(player)} 触发【乾·天道盈虚】：灵气清零（损失 {lost} 点）！")
    # 3 回合后返还 50%
    refund = lost // 2
    player.status.setdefault("energy_events", []).append((4, refund, "乾·天道盈虚"))     # 这里是4，因为在这个回合还会-1
    game.log.append(f"3 个回合后将返还 {refund} 灵气")

# ---------- 坤卦专用处理 ----------
def _handle_kun_1(game: Game, player: Player):
    """地载万物：立刻获得 (地皮数量 × 50) 灵气"""
    tiles_owned = len(player.properties)
    gain = tiles_owned * 50
    player.add_energy(gain)
    game.log.append(f"{fmt_name(player)} 触发【坤·地载万物】：拥有 {tiles_owned} 块地皮，获得 {gain} 灵气！")

def _handle_kun_2(game: Game, player: Player):
    """坤德含章：将当前金币的10%转化为灵气"""
    convert = int(player.money * 0.1)
    player.add_energy(convert)
    player.money -= convert
    player.status["kun_no_money_gain"] = 1  # 标记本回合无法获得金币
    game.log.append(f"{fmt_name(player)} 触发【坤·坤德含章】：消耗 {convert} 金币，转化为 {convert} 灵气！")

# ---------- 震卦专用处理 ----------
def _handle_zhen_1(game: Game, player: Player):
    """雷出地奋：立刻获得400点灵气值，并随机震慑一名其他玩家，使其下次获得的灵气值减半。"""
    player.add_energy(400)

    # 随机选择一个其他玩家
    target = game.choose_target_player(player)
    if target:
        target.status["zhen_shocked"] = 1
        game.log.append(
            f"{fmt_name(player)} 触发【震·雷出地奋】：获得 400 灵气，"
            f"并震慑 {fmt_name(target)}，其下次灵气收益减半！"
        )
    else:
        game.log.append(
            f"{fmt_name(player)} 触发【震·雷出地奋】：获得 400 灵气，"
            f"但无其他玩家可震慑..."
        )

def _handle_zhen_2(game: Game, player: Player):
    """震惧致福：立刻损失250点灵气值(清零为止)，
    但接下来2回合内，每次受到伤害或负面效果时，获得50点灵气值。"""
    lost = min(250, player.energy)
    player.add_energy(-lost)

    for i in range(1, 3):   # 在这个回合就会先-1
        player.status.setdefault("energy_events", []).append((i * len(game.players), 50, "震·震惧致福"))
    game.log.append(
        f"{fmt_name(player)} 触发【震·震惧致福】：损失 {lost} 灵气，"
        f"未来 2 回合内每次受负面效果将补偿 50 灵气！"
    )

# ---------- 巽卦专用处理 ----------
def _handle_xun_1(game: Game, player: Player):
    # 找灵气最高的玩家
    candidates = [p for p in game.players if p != player and p.energy > 0]
    if not candidates:
        game.log.append(f"{fmt_name(player)} 触发【巽·随风赋灵】：无其他玩家可汲取灵气。")
        return
    richest = max(candidates, key=lambda p: p.energy)
    gain = richest.energy // 5
    player.add_energy(gain)
    game.log.append(f"{fmt_name(player)} 触发【巽·随风赋灵】：复制 {fmt_name(richest)} 20% 灵气，获得 {gain}！")

def _handle_xun_2(game: Game, player: Player):
    lost = player.energy // 4
    player.add_energy(-lost)
    player.status["xun_speed"] = 1   # 仅影响下回合
    game.log.append(f"{fmt_name(player)} 触发【巽·风行灵散】：损失 {lost} 灵气，下回合移动额外 +3 步！")

# ---------- 坎卦专用处理 ----------
def _handle_kan_1(game: Game, player: Player):
    """坎渊悟道：已陷入负面状态数量 × 200 灵气"""
    negative_count = len([
        k for k in player.status.keys()
        if k in {"skip_turns", "karma", "shu_control", "fire_debuff", "zhen_shocked"}
    ])
    gain = negative_count * 200
    player.add_energy(gain)
    game.log.append(f"{fmt_name(player)} 触发【坎·坎渊悟道】：身陷 {negative_count} 种负面状态，获得 {gain} 灵气！")

def _handle_kan_2(game: Game, player: Player):
    """水流灵逝：损失 300 灵气并禁锢1回合"""
    lost = min(300, player.energy)
    player.add_energy(-lost)
    player.status["skip_turns"] = max(player.status.get("skip_turns", 0), 1)
    game.log.append(f"{fmt_name(player)} 触发【坎·水流灵逝】：损失 300 灵气并被禁锢 1 回合！")

# ---------- 离卦专用处理 ----------
def _handle_li_1(game: Game, player: Player):
    """离明顿悟：最高建筑等级 × 250 灵气"""
    max_level = max((game.board.tiles[i].level.value for i in player.properties), default=0)
    gain = max_level * 250
    player.add_energy(gain)
    game.log.append(f"{fmt_name(player)} 触发【离·离明顿悟】：最高建筑等级 {max_level}，获得 {gain} 灵气！")

def _handle_li_2(game: Game, player: Player):
    """火焚灵耗：损失 350 灵气，随机技能-1级3回合"""
    lost = min(350, player.energy)
    player.add_energy(-lost)
    # 找到已学会的最高级技能
    skills = player.skill_mgr.skills
    candidates = [s for s in skills.values() if s['level'].value > 1]
    if candidates:
        skill = random.choice(candidates)
        original = skill['level']
        skill['level'] = SkillLevel(skill['level'].value - 1)
        skill["li_debuff_end_turn"] = game.turn + 3
        game.log.append(f"{fmt_name(player)} 触发【离·火焚灵耗】：{skill} 等级暂时降至 {skill['level'].name}，持续 3 回合！")
    else:
        game.log.append(f"{fmt_name(player)} 触发【离·火焚灵耗】：损失 350 灵气，无技能可被降级！")

# ---------- 艮卦专用处理 ----------
def _handle_gen_1(game: Game, player: Player):
    """艮止凝元：回合数 × 30 灵气，上限600"""
    gain = min(game.turn * 30, 600)
    player.add_energy(gain)
    game.log.append(f"{fmt_name(player)} 触发【艮·艮止凝元】：回合沉淀，获得 {gain} 灵气！")

def _handle_gen_2(game: Game, player: Player):
    """山止灵滞：2 回合无法获得灵气，租金-30%"""
    player.status["gen_no_energy_gain"] = 2
    player.status["gen_rent_discount"] = 0.7  # 支付 70 %
    game.log.append(f"{fmt_name(player)} 触发【艮·山止灵滞】：2 回合内无法获得灵气，租金减免 30%！")

# ---------- 兑卦专用处理 ----------
def _handle_dui_1(game: Game, player: Player):
    """兑言纳灵：玩家总数 × 150 灵气"""
    gain = len(game.players) * 150
    player.add_energy(gain)
    game.log.append(f"{fmt_name(player)} 触发【兑·兑言纳灵】：众友讲习，获得 {gain} 灵气！")

def _handle_dui_2(game: Game, player: Player):
    """泽涸灵枯：-30% 灵气且下回合无法使用技能"""
    lost = player.energy * 3 // 10
    player.add_energy(-lost)
    player.status["dui_skill_lock"] = 1
    game.log.append(f"{fmt_name(player)} 触发【兑·泽涸灵枯】：流失 {lost} 灵气，下回合无法使用技能！")