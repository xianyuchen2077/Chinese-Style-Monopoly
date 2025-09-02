1.  如果有关于房屋被破坏的情况，记得添加到Player.destroyed_tiles
2.  检查所有的add_money和add_energy，记得加if gain:判断
3.  及时把游戏日志同步到 UI 日志
    while self.game.log:
        self.log.append(self.game.log.pop(0))
4.  生肖技能在使用其他玩家作为目标的时候，注意一下can_be_skill_targeted()的使用，参见use_shu，主要是 鼠（已完成）、牛、龙、猴、猪
5.  draw_info里面涉及玩家状态设置
    if hasattr(player, 'status'):
        if 'shield' in player.status: positive_states.append('护盾')
        if 'tiger_split' in player.status: positive_states.append('分身')
        if 'skip_turns' in player.status: negative_states.append('休息')
        if 'karma' in player.status: negative_states.append('业障')
        if 'shu_control' in player.status: negative_states.append('被控')
6.  如果玩家被控制在原地，为了避免重复触发停留格效果，需要 player.remain_in_the_same_position = True
7.  tile的special处理逻辑有错误，一个状态消失了，这个special就变成None了