// GamesAI Extra - 假人自动索敌/保护脚本
// 用法:
//   索敌模式: script load bot_combat global <bot_name> <radius> <interval>
//   保护模式: script load bot_combat global protect <bot_name> <player_name> <radius> <interval>
//   - bot_name:    假人名字
//   - player_name: 被保护的玩家名（仅保护模式）
//   - radius:      索敌半径（格），默认 16
//   - interval:    扫描间隔（游戏刻），默认 10
// 停止: script unload bot_combat  （配合 bot_stop_combat 工具使用）

__config() -> (
    {'stay_loaded': true}
);

// 在 center 周围 radius 内寻找最近的存活敌对生物（monster 分类）
nearest_hostile(center, radius) -> (
    best = null;
    min_d = radius + 1;
    for (m : entity_list('monster', center, radius),
        if (query(m, 'is_alive'),
            d = distance(center, pos(m));
            if (d < min_d,
                min_d = d;
                best = m
            )
        )
    );
    best
);

// 索敌模式：扫描假人周围半径内最近的怪物，转向并攻击
bot_combat(bot_name, radius, interval) -> (
    loop = (
        bot = player(bot_name);
        if (bot != null,
            target = nearest_hostile(pos(bot), radius);
            if (target != null,
                tp = pos(target);
                run('player ' + bot_name + ' look at ' + tp:0 + ' ' + tp:1 + ' ' + tp:2);
                run('player ' + bot_name + ' attack')
            )
        );
        schedule(loop, interval)
    );
    loop()
);

// 保护模式：跟随被保护玩家，自动攻击该玩家周围半径内最近的怪物
// 无怪物时传送到玩家身后 2 格跟随；有怪物时优先攻击怪物
bot_protect(bot_name, target_name, radius, interval) -> (
    loop = (
        bot = player(bot_name);
        human = player(target_name);
        if (bot != null && human != null,
            mob = nearest_hostile(pos(human), radius);
            if (mob != null,
                mp = pos(mob);
                run('player ' + bot_name + ' look at ' + mp:0 + ' ' + mp:1 + ' ' + mp:2);
                run('player ' + bot_name + ' attack')
            ,
                // 无怪物：跟随到玩家身后 2 格（按玩家朝向计算）
                hp = pos(human);
                yaw = query(human, 'yaw') * 3.141592653589793 / 180;
                follow = [hp:0 - sin(yaw) * 2, hp:1, hp:2 + cos(yaw) * 2];
                run('tp ' + bot_name + ' ' + follow:0 + ' ' + follow:1 + ' ' + follow:2)
            )
        );
        schedule(loop, interval)
    );
    loop()
);

// 从 script load 参数启动：protect 为保护模式，否则为索敌模式
if (args,
    if (args:0 == 'protect',
        bot_protect(args:1, args:2, to_int(args:3), to_int(args:4))
    ,
        bot_combat(args:0, to_int(args:1), to_int(args:2))
    )
);
