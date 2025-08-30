# game_tigger_event.py
# 奇遇事件专用逻辑

import random
from typing import Dict, List
from game_core import fmt_name, Game, Player, Tile
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

    # 其余卦留空位，后续继续扩展

# ---------- 八卦灵气值事件具体实现 ----------
# ---------- 乾卦专用处理 ----------
def _handle_qian_1(game: Game, player: Player):
    """云行雨施：立刻 +500 灵气，后续 3 回合每回合 +100"""
    player.energy += 500
    game.log.append(f"{fmt_name(player)} 触发【乾·云行雨施】：立刻获得 500 灵气！")
    # 后续 3 回合
    for i in range(1, 4):
        player.status["energy_events"].append((i, 100, "乾·云行雨施"))

def _handle_qian_2(game: Game, player: Player):
    """天道盈虚：清零当前灵气，3 回合后返还 50%"""
    lost = player.energy
    player.energy = 0
    game.log.append(
        f"{fmt_name(player)} 触发【乾·天道盈虚】：灵气清零（损失 {lost} 点）！"
    )
    # 3 回合后返还 50%
    refund = lost // 2
    player.status["energy_events"].append((4, -refund, "乾·天道盈虚 返还"))     # 这里是4，因为在这个回合还会-1
    game.log.append(f"3 回合后将返还 {refund} 灵气。")

# ---------- 坤卦专用处理 ----------
def _handle_kun_1(game: Game, player: Player):
    """地载万物：立刻获得 (地皮数量 × 50) 灵气"""
    tiles_owned = len(player.properties)
    gain = tiles_owned * 50
    player.energy += gain
    game.log.append(f"{fmt_name(player)} 触发【坤·地载万物】：拥有 {tiles_owned} 块地皮，获得 {gain} 灵气！")

def _handle_kun_2(game: Game, player: Player):
    """坤德含章：将当前金币的10%转化为灵气，本回合无法获得金币"""
    convert = int(player.money * 0.1)
    player.energy += convert
    player.money -= convert
    player.status["kun_no_money_gain"] = 1  # 标记本回合无法获得金币
    game.log.append(
        f"{fmt_name(player)} 触发【坤·坤德含章】：消耗 {convert} 金币，转化为 {convert} 灵气！"
    )

# ---------- 震卦专用处理 ----------
def _handle_zhen_1(game: Game, player: Player):
    player.energy += 400
    # 随机选择一个其他玩家
    candidates = [p for p in game.players if p != player]
    if not candidates:
        game.log.append(f"{fmt_name(player)} 触发【震·雷出地奋】：获得 400 灵气，但无其他玩家可震慑。")
        return
    target = random.choice(candidates)
    target.status["zhen_shocked"] = 1
    game.log.append(f"{fmt_name(player)} 触发【震·雷出地奋】：获得 400 灵气，并震慑 {fmt_name(target)}，其下回合灵气收益减半！")

def _handle_zhen_2(game: Game, player: Player):
    lost = min(250, player.energy)
    player.energy -= lost
    player.status["zhen_retribution"] = 2   # 持续 2 回合
    game.log.append(f"{fmt_name(player)} 触发【震·震惧致福】：损失 {lost} 灵气，但未来 2 回合内每次受负面效果将补偿 50 灵气！")

# ---------- 巽卦专用处理 ----------
def _handle_xun_1(game: Game, player: Player):
    # 找灵气最高的玩家
    candidates = [p for p in game.players if p != player and p.energy > 0]
    if not candidates:
        game.log.append(f"{fmt_name(player)} 触发【巽·随风赋灵】：无其他玩家可汲取灵气。")
        return
    richest = max(candidates, key=lambda p: p.energy)
    gain = richest.energy // 5
    player.energy += gain
    game.log.append(f"{fmt_name(player)} 触发【巽·随风赋灵】：复制 {fmt_name(richest)} 20% 灵气，获得 {gain}！")

def _handle_xun_2(game: Game, player: Player):
    lost = player.energy // 4
    player.energy -= lost
    player.status["xun_speed"] = 1   # 仅影响下回合
    game.log.append(f"{fmt_name(player)} 触发【巽·风行灵散】：损失 {lost} 灵气，下回合移动额外 +3 步！")
