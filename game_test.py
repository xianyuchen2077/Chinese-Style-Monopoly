# game_test.py
# 所有测试用例集中管理

from game_core import Game, Player, BuildingLevel

def run_buy_test_case(case_id: int, ui_instance):
    """
    一键初始化棋盘并执行购买测试
    参数：
        case_id: 0~3 分别对应 4 个用例
        ui_instance: GameUI 实例，用于刷新日志与界面
    """
    # 1) 单玩家新游戏
    game = Game(["测试玩家"], ["鼠"])
    game.players[0].game = game
    ui_instance.game = game
    ui_instance.player_sprites = ui_instance._load_player_sprites()

    # 2) 用例数据
    case_map = {
        0: (5,  None, None, 0),               # 空地 0 元
        1: (10, None, None, 99999999),        # 空地 99999999 元
        2: (15, None, "占位玩家", 3000),       # 已被别人买走
        3: (20, "start", None, 0),            # 特殊格子不可买
    }
    idx, special, owner_name, new_price = case_map[case_id]

    tile = game.board.tiles[idx]
    tile.special = special
    if new_price is not None:
        tile.price = new_price
    if owner_name:
        tile.owner = Player(owner_name, "牛", is_ai=True)
        tile.owner.properties.append(idx)

    player = game.players[0]
    player.position = idx

    # 3) 执行购买
    ok, reason = game.can_buy(player)
    if ok:
        game.buy_property(player)
        ui_instance.log.append(f"[用例{case_id+1}] 购买成功")
    else:
        ui_instance.log.append(f"[用例{case_id+1}] 购买失败：{reason}")

    # 4) 刷新 UI
    ui_instance.active_modal = None
    ui_instance._scroll_to_bottom()
