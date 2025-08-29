# game_test.py
# 所有测试用例集中管理

from game_core import Game, Player, BuildingLevel

def run_buy_test_case(case_id: int, ui_instance):
    """
    场景测试：case_id 1~4
    1 空地可买
    2 空地钱不够
    3 已被别人占据
    4 特殊格子不能买
    触发后：
        – 场景布场
        – 打开 TEST MODE
        – 固定骰点 = 到达目标格所需步数
    """
    # 场景表：(目标格子, 价格, 主人, 特殊, 玩家金币, 所需骰点, 期望关键字)
    scenes = [
        None,   # 占位，让索引从1开始
        (1,   3000, None, None, 10000, 1, "空地可买"),
        (2, 999999, None, None, 10000, 2, "空地钱不够"),
        (3,   4000, Player("占位玩家","牛",is_ai=True), None, 10000, 3, "已被别人占据"),
        (6,   2000, None, "encounter", 10000, 6, "特殊格子不能买"),
    ]
    idx, price, owner, special, money, need_dice, desc = scenes[case_id]

    # 1) 新建单玩家游戏
    game = Game(["测试玩家"], ["鼠"])
    player = game.players[0]
    player.game = game
    player.money = money
    player.position = 0      # 统一从 0 出发

    # 2) 布场
    tile = game.board.tiles[idx]
    tile.price = price
    tile.owner = owner
    tile.special = special
    if owner:
        owner.properties.append(idx)
        tile.level = BuildingLevel.HUT if not special else BuildingLevel.EMPTY

    # 3) 打开 TEST MODE 并设定固定骰点
    ui_instance.test_mode = True
    ui_instance.test_dice = need_dice            # 正好一步走到目标格

    # 4) 把新游戏挂到 UI
    ui_instance.game = game
    ui_instance.player_sprites = ui_instance._load_player_sprites()

    # 5) 日志提示
    ui_instance.log.append("=== 场景测试 {} ===".format(case_id))
    ui_instance.log.append(desc)
    ui_instance.log.append("目标格子 {}，固定骰点 {}".format(idx, need_dice))
    ui_instance._scroll_to_bottom()
