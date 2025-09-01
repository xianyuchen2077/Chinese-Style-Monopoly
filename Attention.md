1. 如果有关于房屋被破坏的情况，记得添加到Player.destroyed_tiles
2. 检查所有的add_money和add_energy，记得加if gain:判断
3. 及时把游戏日志同步到 UI 日志
    while self.game.log:
        self.log.append(self.game.log.pop(0))
4. 生肖技能在使用其他玩家作为目标的时候，注意一下can_be_skill_targeted()的使用，参见use_shu，主要是 鼠（已完成）、牛、龙、猴、猪