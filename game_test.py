# game_test.py
# 所有测试用例集中管理

from game_core import Game, Player, BuildingLevel, Element, fmt_name

def trigger_test_encounter(game, player, tile):
    """
    测试模式下的奇遇触发逻辑，专门用于模拟各种奇遇效果。
    """
    e = tile.element
    if e == Element.WATER:
        # 模拟洪水奇遇，逐级降建筑但不摧毁地皮
        if tile.level.value > 0:
            tile.level = BuildingLevel(tile.level.value - 1)
            game.log.append(f"【测试-洪水】摧毁 {fmt_name(tile.owner)} 的「{tile.name}」，建筑降为 {tile.level.name}")
        else:
            game.log.append(f"【测试-洪水】无效果：「{tile.name}」已是空地")
    elif e == Element.FIRE:
        # 模拟火灾奇遇，完全摧毁建筑且使地皮无主
        if tile.level.value > 0:
            # 记录当前建筑等级用于日志
            old_level = tile.level.name
            tile.level = BuildingLevel.EMPTY
            tile.owner = None
            game.log.append(f"【测试-火灾】摧毁 {fmt_name(player)} 的「{tile.name}」，建筑彻底摧毁，地皮无主")
        else:
            game.log.append(f"【测试-火灾】无效果：「{tile.name}」已是空地")
    elif e == Element.EARTH:
        # 模拟地震奇遇，直接摧毁所有建筑至空地
        if tile.level.value > 0:
            # 记录当前建筑等级用于日志
            old_level = tile.level.name
            tile.level = BuildingLevel.EMPTY
            game.log.append(f"【测试-地震】摧毁 {fmt_name(tile.owner)} 的「{tile.name}」，建筑直接摧毁至空地")
        else:
            game.log.append(f"【测试-地震】无效果：「{tile.name}」已是空地")

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

    # 清空旧日志
    ui_instance.log.clear()

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

def run_upgrade_test_case(case_id: int, ui_instance):
    """
    场景测试：case_id 1~4
    1. 不是自己的地皮不能加盖
    2. 正常加盖（一回合一次，走到地皮→购买→每回合停留加盖）
    3. 余额不足不能加盖
    4. 地皮遭到破坏（触发奇遇）
    """
    # 清空旧日志
    ui_instance.log.clear()

    if case_id == 1:
        # —— 1. 不是自己的地皮不能加盖 ——
        game = Game(["测试玩家", "占位玩家"], ["鼠", "牛"])
        player = game.players[0]
        player.money = 10000
        player.position = 0

        idx = 1
        tile = game.board.tiles[idx]
        tile.price = 3000
        tile.owner = game.players[1]  # 属于占位玩家
        tile.special = None
        tile.owner.properties.append(idx)
        tile.level = BuildingLevel.HUT

        ui_instance.test_mode = True
        ui_instance.test_dice = 1
        ui_instance.game = game
        ui_instance.player_sprites = ui_instance._load_player_sprites()

        ui_instance.log.append("=== 地皮加盖测试场景 1：不是自己的地皮 ===")
        ui_instance.log.append("期望：提示“他人财产不可升级”")
        ui_instance._scroll_to_bottom()

        # 模拟走到该地皮
        game.move_player(player, 1)
        # 尝试加盖（UI 手动点击“加盖”按钮即可触发）
        while game.log:
            ui_instance.log.append(game.log.pop(0))
        ui_instance._scroll_to_bottom()

    elif case_id == 2:
        # —— 2. 正常加盖（一回合一次）——
        game = Game(["测试玩家"], ["鼠"])
        player = game.players[0]
        player.money = 999999
        player.position = 0

        idx = 2
        tile = game.board.tiles[idx]
        tile.price = 2000
        tile.owner = None
        tile.special = None

        ui_instance.test_mode = True
        ui_instance.test_dice = 2
        ui_instance.game = game
        ui_instance.player_sprites = ui_instance._load_player_sprites()

        ui_instance.log.append("=== 地皮加盖测试场景 2：正常加盖 ===")
        ui_instance.log.append("第一次移动到2号地皮并购买，后续每回合停留并加盖一次")
        ui_instance._scroll_to_bottom()

        # 第一次移动并自动购买
        game.move_player(player, 2)
        game.buy_property(player)

        # 同步日志
        while game.log:
            ui_instance.log.append(game.log.pop(0))
        ui_instance._scroll_to_bottom()

        # 后续回合：玩家每次点击“加盖”即可加盖一次
        # UI 层负责回合结束按钮，无需额外代码

    elif case_id == 3:
        # —— 3. 余额不足不能加盖 ——
        game = Game(["测试玩家"], ["鼠"])
        player = game.players[0]
        player.money = 0  # 余额不足
        player.position = 0

        idx = 3
        tile = game.board.tiles[idx]
        tile.price = 4000
        tile.owner = player  # 属于测试玩家
        tile.special = None
        player.properties.append(idx)
        tile.level = BuildingLevel.HUT  # 初始为茅屋

        ui_instance.test_mode = True
        ui_instance.test_dice = 3
        ui_instance.game = game
        ui_instance.player_sprites = ui_instance._load_player_sprites()

        ui_instance.log.append("=== 地皮加盖测试场景 3：余额不足 ===")
        ui_instance.log.append("期望：提示“资金不足，不可加盖”")
        ui_instance._scroll_to_bottom()

        # 移动到地皮
        game.move_player(player, 3)
        # 玩家手动点击“加盖”按钮即可看到提示
        while game.log:
            ui_instance.log.append(game.log.pop(0))
        ui_instance._scroll_to_bottom()

    elif case_id == 4:
        # —— 4. 地皮遭到破坏（触发奇遇）——
        game = Game(["测试玩家"], ["鼠"])
        player = game.players[0]
        player.money = 10000
        player.position = 0

        idx = 4
        tile = game.board.tiles[idx]
        tile.price = 5000
        tile.owner = player
        tile.special = None
        player.properties.append(idx)
        tile.level = BuildingLevel.PALACE  # 初始为宫殿
        tile.element = Element.WATER  # 水属性，触发洪水

        ui_instance.test_mode = True
        ui_instance.test_dice = 4
        ui_instance.game = game
        ui_instance.player_sprites = ui_instance._load_player_sprites()

        ui_instance.log.append("=== 地皮加盖测试场景 4：地皮遭到破坏 ===")
        ui_instance.log.append("期望：触发水属性奇遇，宫殿降级为瓦房")
        ui_instance._scroll_to_bottom()

        # 移动到地皮并触发奇遇
        game.move_player(player, 4)
        trigger_test_encounter(game, player, tile)

        # 同步日志
        while game.log:
            ui_instance.log.append(game.log.pop(0))
        ui_instance._scroll_to_bottom()

    else:
        ui_instance.log.append("测试场景不存在")
        ui_instance._scroll_to_bottom()
