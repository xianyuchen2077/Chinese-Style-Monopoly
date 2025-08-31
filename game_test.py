# game_test.py
# 所有测试用例集中管理

from game_core import Game, Player, BuildingLevel, Element, fmt_name, SkillLevel
from game_trigger_event import Bagua

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
    ui_instance.game.test_mode = True
    ui_instance.player_sprites = ui_instance._load_player_sprites()

    # 5) 日志提示
    ui_instance.log.append("=== 场景测试 {} ===".format(case_id))
    ui_instance.log.append(desc)
    ui_instance.log.append("目标格子 {}，固定骰点 {}".format(idx, need_dice))
    ui_instance._scroll_to_bottom()

def run_upgrade_test_case(case_id: int, ui_instance):
    """
    场景测试：case_id 1~4，全部通过“转动轮盘”触发
    1 他人地皮（骰点=1，走到1号位）
    2 正常加盖（骰点=0，每回合原地加盖）
    3 余额不足（骰点=3，走到3号位）
    4 地皮遭破坏（骰点=4，走到4号位后触发地震奇遇）
    """
    # 清空旧日志
    ui_instance.log.clear()

    # 公共准备
    game = Game(["测试玩家"], ["鼠"])
    player = game.players[0]
    player.game = game
    player.position = 0        # 统一从起点出发

    if case_id == 1:
        # —— 场景1：他人地皮 ——
        idx = 1
        tile = game.board.tiles[idx]
        tile.price = 3000
        tile.owner = Player("占位玩家", "牛", is_ai=True)
        tile.special = None
        tile.level = BuildingLevel.HUT
        tile.owner.properties.append(idx)

        ui_instance.test_mode = True
        ui_instance.test_dice = 1          # 一步走到1号
        ui_instance.game = game
        ui_instance.game.test_mode = True
        ui_instance.player_sprites = ui_instance._load_player_sprites()

        ui_instance.log.append("=== 场景测试 1：不是自己的地皮 ===")
        ui_instance.log.append("期望：提示“公共/他人财产不可升级”")
        ui_instance._scroll_to_bottom()

    elif case_id == 2:
        # —— 场景2：原地加盖 ——
        idx = 2
        tile = game.board.tiles[idx]
        tile.price = 2000
        tile.owner = player
        tile.special = None
        player.properties.append(idx)
        tile.level = BuildingLevel.EMPTY   # 初始空地
        player.position = 2

        ui_instance.test_mode = True
        ui_instance.test_dice = 0          # 每次轮盘=0，不动
        ui_instance.game = game
        ui_instance.game.test_mode = True
        ui_instance.player_sprites = ui_instance._load_player_sprites()

        ui_instance.log.append("=== 场景测试 2：原地加盖 ===")
        ui_instance.log.append("骰点=0，每回合结束即可加盖一次")
        ui_instance._scroll_to_bottom()

    elif case_id == 3:
        # —— 场景3：余额不足 ——
        idx = 3
        tile = game.board.tiles[idx]
        tile.price = 4000
        tile.owner = player
        tile.special = None
        player.properties.append(idx)
        tile.level = BuildingLevel.HUT
        player.money = 0                   # 余额不足

        ui_instance.test_mode = True
        ui_instance.test_dice = 3          # 走到3号
        ui_instance.game = game
        ui_instance.game.test_mode = True
        ui_instance.player_sprites = ui_instance._load_player_sprites()

        ui_instance.log.append("=== 场景测试 3：余额不足 ===")
        ui_instance.log.append("期望：提示“资金不足，不可加盖”")
        ui_instance._scroll_to_bottom()

    elif case_id == 4:
        # —— 场景4：地皮遭受破坏 ——
        idx = 4
        tile = game.board.tiles[idx]
        tile.price = 5000
        tile.owner = player
        tile.special = None
        player.properties.append(idx)
        tile.level = BuildingLevel.PALACE    # 初始最高级
        tile.element = Element.EARTH         # 触发“地震”

        ui_instance.test_mode = True
        ui_instance.test_dice = 4            # 走到4号
        ui_instance.game = game
        ui_instance.game.test_mode = True
        ui_instance.player_sprites = ui_instance._load_player_sprites()

        ui_instance.log.append("=== 场景测试 4：地皮遭到破坏 ===")
        ui_instance.log.append("期望：触发地震奇遇，宫殿被摧毁至空地")
        ui_instance._scroll_to_bottom()
        # 把测试用例信息写回 Game，供 next_turn() 判断
        game._test_l2_key  = 'upgrade'
        game._test_l3_case = 4

    else:
        ui_instance.log.append("测试场景不存在")
        ui_instance._scroll_to_bottom()

    # 统一把底层日志同步到 UI
    while game.log:
        ui_instance.log.append(game.log.pop(0))
    ui_instance._scroll_to_bottom()

def run_bagua_test_case(bagua_char: str, ui_instance):
    """
    测试指定八卦的奇遇
    bagua_char 只能是 "乾" 等 8 个单字
    """
    ui_instance.log.clear()
    ui_instance.test_mode = True

    # 1) 新建单玩家游戏
    game = Game(["测试玩家", "NPC"], ["鼠", "牛"])
    player = game.players[0]
    player.game = game
    player.position = 0
    # 把 25、26、27 号地皮直接设为玩家财产
    for idx in (25, 26, 27):
        tile = game.board.tiles[idx]
        tile.owner = player
        tile.level = BuildingLevel.HUT        # 先统一设成茅屋，也可根据需要改
        player.properties.append(idx)

    if bagua_char == "坎":
        # 给主角加两个负面效果，方便测试
        player.status["skip_turns"] = 2          # 禁足 2 回合
        player.status["karma"] = 2               # 业障 2 回合
        game.log.append("【测试】已为测试玩家添加 skip_turns、karma 两种负面状态")
    elif bagua_char == "离":
        # 把所有可升级技能升到 III 级
        for sk in player.skill_mgr.skills.values():
            if "level" in sk and sk["level"].value < 3:
                sk["level"] = SkillLevel.III
        game.log.append("【测试】已将该玩家所有技能等级升至最高级（III）")
        game.board.tiles[26].level = BuildingLevel.PALACE
        game.log.append("【测试】已将26号地皮等级升至最高级（PALACE）")

    player_npc = game.players[1]
    player_npc.game = game
    player_npc.position = 34
    player_npc.energy = 200

    # 2) 把 1 号格固定为指定八卦
    target_idx = 1
    tile = game.board.tiles[target_idx]
    tile.bagua = Bagua(bagua_char)
    tile.special = "buff_bagua"
    game.board.bagua_tiles[target_idx] = Bagua(bagua_char)  # 同步到 board.bagua_tiles，让 UI 能渲染
    tile.element = Element.GOLD  # 随意给一个五行，不影响测试
    tile.price = 1000

    tile_2 = game.board.tiles[35]
    tile_2.bagua = Bagua("乾")
    tile_2.special = "buff_bagua"
    game.board.bagua_tiles[35] = Bagua("乾")  # 同步到 board.bagua_tiles，让 UI 能渲染
    tile_2.element = Element.GOLD  # 随意给一个五行，不影响测试
    tile_2.price = 1000

    # 3) 固定骰点 1 → 正好走到 1 号格
    ui_instance.test_dice = 1
    game.test_mode = True

    # 4) 挂到 UI
    ui_instance.game = game
    ui_instance.player_sprites = ui_instance._load_player_sprites()

    # 5) 日志提示
    ui_instance.log.append("=== 八卦灵气奇遇测试 ===")
    ui_instance.log.append(f"八卦：{bagua_char}，目标格：{target_idx}，骰点：{ui_instance.test_dice}")
    ui_instance._scroll_to_bottom()
