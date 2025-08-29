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
    2. 正常加盖（一级一级地加盖，一回合一次）
    3. 余额不足不能加盖
    4. 奇遇摧毁满级地皮
    """
    # 定义场景
    scenes = [
        None,  # 占位，让索引从1开始
        # case_id 1: 不是自己的地皮不能加盖
        {
            "player_idx": 1,
            "money": 10000,
            "tile_idx": 1,
            "tile_price": 3000,
            "tile_owner": Player("占位玩家", "牛", is_ai=True),
            "tile_special": None,
            "test_dice": 1,
            "expect": "该地皮已有主人"
        },
        # case_id 2: 正常加盖（一回合一次）
        {
            "player_idx": 2,
            "money": 999999,
            "tile_idx": 2,
            "tile_price": 2000,
            "tile_owner": None,
            "tile_special": None,
            "test_dice": 2,
            "expect": "依次正常加盖，建筑从空地→茅屋→瓦房→客栈→宫殿"
        },
        # case_id 3: 余额不足不能加盖
        {
            "player_idx": 3,
            "money": 0,
            "tile_idx": 3,
            "tile_price": 4000,
            "tile_owner": None,
            "tile_special": None,
            "test_dice": 3,
            "expect": "资金不足，不可加盖"
        },
        # case_id 4: 奇遇摧毁满级地皮
        {
            "player_idx": 4,
            "money": 10000,
            "tile_idx": 4,
            "tile_price": 5000,
            "tile_owner": None,  # 属于玩家自己，初始化时填充
            "tile_special": None,
            "test_dice": 4,
            "expect": "触发奇遇后，建筑从宫殿→瓦房"
        },
    ]
    scene = scenes[case_id]
    if not scene:
        ui_instance.log.append("测试场景不存在")
        return

    # 初始化游戏
    if case_id == 1:
        game = Game(["玩家一", "占位玩家"], ["鼠", "牛"])
        player = game.players[0]
    else:
        game = Game(["测试玩家"], ["鼠"])
        player = game.players[0]
    player.money = scene["money"]
    player.position = 0

    # 布场：设置地皮状态
    idx = scene["tile_idx"]
    tile = game.board.tiles[idx]
    tile.price = scene["tile_price"]
    tile.owner = scene["tile_owner"] if case_id != 4 else player  # case4时属于测试玩家
    tile.special = scene["tile_special"]
    if tile.owner:
        tile.owner.properties.append(idx)
        tile.level = (
            BuildingLevel.PALACE if case_id == 4 else BuildingLevel.HUT
        )  # case4是满级宫殿

    # 开启测试模式：固定骰点，确保玩家准确走到目标格
    ui_instance.test_mode = True
    ui_instance.game.test_mode = True
    ui_instance.test_dice = scene["test_dice"]
    ui_instance.game = game
    ui_instance.player_sprites = ui_instance._load_player_sprites()

    # 日志记录测试情景
    ui_instance.log.append("=== 地皮加盖测试场景 {} ===".format(case_id))
    ui_instance.log.append(scene["expect"])
    ui_instance.log.append("测试中：目标格 {}, 骰点固定为 {}".format(idx, scene["test_dice"]))
    ui_instance._scroll_to_bottom()

    # 特殊处理 case4：模拟奇遇摧毁逻辑
    if case_id == 4:
        # 强制触发毁灭性奇遇（以水属性为例）
        tile.element = Element.WATER
        game.trigger_event(player)
        ui_instance.log.append("模拟触发【洪水】奇遇，宫殿降级")
        ui_instance._scroll_to_bottom()
