✅ 给技能系统预留的钩子
如果某个角色技能触发“额外回合”，只需在技能逻辑里
self.has_rolled = False   # 允许再转一次
即可实现额外回合。

技能是有错误的
那个判定用的是self.has_rolled