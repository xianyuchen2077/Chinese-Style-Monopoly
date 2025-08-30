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
    # 其余卦留空位，后续继续扩展

# ---------- 八卦灵气值事件具体实现 ----------
# ---------- 乾卦专用处理 ----------
def _handle_qian_1(game: Game, player: Player):
    """云行雨施：立刻 +500 灵气，后续 3 回合每回合 +100"""
    player.energy += 500
    game.log.append(f"{fmt_name(player)} 触发【乾·云行雨施】：立刻获得 500 灵气！")
    # 在 status 中注册后续增益
    player.status["qian_yun_buff"] = {"turns": 3, "gain": 100}
    game.log.append("后续 3 回合每回合再得 100 灵气。")

def _handle_qian_2(game: Game, player: Player):
    """天道盈虚：清零当前灵气，3 回合后返还 50%"""
    lost = player.energy
    player.energy = 0
    game.log.append(
        f"{fmt_name(player)} 触发【乾·天道盈虚】：灵气清零（损失 {lost} 点）！"
    )
    # 把损失量记到 status，回合结束时由 Game.next_turn 统一结算返还
    player.status["qian_kui_track"] = {"refund_amount": lost // 2, "turns": 3}
    game.log.append("3 回合后将返还 50% 损失灵气。")
