✅ 给技能系统预留的钩子
如果某个角色技能触发“额外回合”，只需在技能逻辑里
self.has_rolled = False   # 允许再转一次
即可实现额外回合。

未羊的灵魂跨越起点的时候不会触发奖励

_render_shu_skill_modal这个可不可以简化

未羊的三阳开泰可能有问题
    def _trigger_san_yang_kai_tai(self, distance: int) -> str:
        board = self.player.game.board
        path = self._shortest_path(self.player.position, distance)
        for idx in path[1:]:
            tile = board.tiles[idx]
            if tile.owner is None and tile.price and self.player.money >= tile.price:
                tile.owner = self.player
参考：
def _trigger_san_yang_kai_tai(self, distance: int) -> str:
    # 修改这一行
    game = self.player.game  # 获取游戏实例引用
    if not game:
        return ""

    path = self._shortest_path(self.player.position, distance)
    for idx in path[1:]:
        tile = game.board.tiles[idx]  # 使用 game.board
        # ... 其他代码保持不变 ...