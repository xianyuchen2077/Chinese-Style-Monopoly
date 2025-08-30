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

# # ---------- 八卦灵气事件对外接口 ----------
# def trigger_bagua_lingqi_encounter(game: "Game", player: "Player", tile: "Tile"):
#     bagua = tile.bagua
#     events = BAGUA_LINGQI_EVENTS[bagua]
#     event = random.choice(events)

#     game.log.append(f"{fmt_name(player)} 触发【{bagua.value[0]}为{bagua.value[1]}】奇遇")
#     game.log.append(f"「{event['name']}」- {event['desc']}")

#     handler_name = f"_handle_{bagua.name.lower()}_{event['name']}"
#     globals()[handler_name](game, player, event)

# # ---------- 各事件实现 ----------
# def _handle_qian_云行雨施(game: "Game", player: "Player", event: dict):
#     player.add_lingqi(500, source=event['name'])
#     player.lingqi_buffs.append({"type": "gain", "value": 100, "turns": 3, "source": event['name']})

# def _handle_qian_天道盈虚(game: "Game", player: "Player", event: dict):
#     lost = player.lose_lingqi(player.lingqi, source=event['name'])
#     player.lingqi_buffs.append({"type": "gain", "value": lost // 2, "turns": 3, "source": "天道盈虚返还"})

# def _handle_kun_地载万物(game: "Game", player: "Player", event: dict):
#     gain = len(player.properties) * 50
#     player.add_lingqi(gain, source=event['name'])

# def _handle_kun_坤德含章(game: "Game", player: "Player", event: dict):
#     convert = int(player.money * 0.1)
#     player.money -= convert
#     player.add_lingqi(convert, source=event['name'])
#     player.add_status_effect("无法获得金币", 1)

# # —— 其余 6 卦 12 个事件，可按同样格式继续补全 ——
