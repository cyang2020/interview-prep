# 第一问：发牌、判牌型、取赢家，三条 > 对子 > 高牌

## 这一问要做什么

- 写 play(num_players, seed)：几个人一桌，每人轮流发三张，返回赢家列表和全过程日志，每发一张、每判一手、最后的结果各记一条。
- 第一问只看点数：三张一样是三条，两张一样是对子，都不一样是高牌，三条 > 对子 > 高牌；同牌型再比点数。

## 核心思路

- 按顺序四步：deal 发牌、evaluate_all 打分、pick_winners 取最大、play 串起来并把 winners 和 log 一起返回。每步只做自己的事，后两问各加一条规则或插一步，不碰别的步骤。
- Card 两个字段 rank 和 suit。RANKS 是 2 到 13，J/Q/K 记成 11/12/13，没有 A；make_deck 生成 48 张并用传进来的 rng 洗牌，测试给固定种子就能复现同一局。
- deal 外层循环轮数、内层玩家，一轮每人一张发三轮，每发一张追加一条 "deal round 1: P1 gets 6C"。
- evaluate_hand 是纯函数（三张牌进、结果出，不改牌、不写日志）：用 Counter 数每个点数出现几次，最多出现 3 次是 three_of_a_kind，2 次是 pair，否则 high_card，返回 (牌型名, 分数)。
- 分数是元组 (CATEGORY_RANK[category], tiebreak)：第一项是牌型在 CATEGORY_ORDER 表里的位置，第二项是破平局的点数列表。两手牌比大小直接用元组的 > 和 ==，Python 逐项比，不用写比较器。
- tiebreak 一条规则几种牌型共用：出现过的点数按 (出现次数, 点数) 从大到小排。对子 7,7,K 排出 [7, 13]，高牌 3,8,K 排出 [13, 8, 3]。
- evaluate_all 每人打一次分、记一条 evaluate 日志，结果存成 (player, category, score) 的列表 scored 往后传；pick_winners 扫一遍 scored，比当前最大就换掉，相等就追加进 winners，并列全返回。
- 复杂度：每手三张打分常数时间，取最大扫一遍玩家 O(P)。不排序，不用优先队列。

## 思考与反问

- 牌堆放不放 A？我按不放做，RANKS 写 2 到 13，牌堆 48 张。面试官要加就在 RANKS 加 14、RANK_NAMES 加 "A"，别的不动；A 算 1 就加 1。
- 同牌型怎么比？对子先比对子点数再比单牌，高牌从大到小逐张比。这决定了 tiebreak 的排序键是 (出现次数, 点数) 而不是只按点数。
- 两手完全相同怎么办？我按并列做：pick_winners 里 score == best_score 的分支把人追加进 winners，describe_result 写 "tie between P1, P3"。要"先手赢"就删掉那个 elif 分支；要"都不赢"就在并列人数大于 1 时返回空列表。
- 为什么牌型等级做成 CATEGORY_ORDER 表而不在判定分支里写死数字：第二问要在 pair 和 three_of_a_kind 之间插 flush，写死的话三条的 2 要手改成 3、再给同花填 2，漏一处比较就错。
- 为什么 evaluate_hand 不写日志：测试要调它几十次，每次都追加日志就得给它造一个 log 列表；日志只在 deal、evaluate_all、play 三处写。
- 这题另一种出法只给 deal_card 和 check_result 两个方法名让你填：deal_card 就是 deal 内层循环的三行（拿一张、放进 hand、记日志），check_result 就是 evaluate_all 加 pick_winners；挂成方法，逻辑不变。

## 测试要点

- test_deal_round_robin：三人发完每人三张、deck 剩 39 张，日志里玩家顺序是 P1 P2 P3 重复三遍，轮数从 1 记到 3。
- test_category_detection：7,7,7 判 three_of_a_kind，7,7,K 判 pair，3,8,K 判 high_card。
- test_cross_category_order：三条 > 对子 > 高牌；最小的三条 2,2,2 大于最大的对子 K,K,Q，最小的对子 2,2,3 大于最大的高牌 K,Q,J。
- test_within_category：对子先比对子点数 9,9,2 > 5,5,K，再比单牌 7,7,K > 7,7,2；高牌第一张相同比第二张；三条比三条点数。
- test_order_independent：同一手牌 K,7,7 换三种顺序，分数相同。
- test_tie_returns_all：对子赢两手高牌且每人只有一条 evaluate 日志；两手点数完全相同的高牌一起返回 [P1, P3]。
- test_play_log_shape：种子 42 三人一局日志 13 条（9 条 deal、3 条 evaluate、1 条 result），最后一条以 result: 开头，同种子跑两次结果相同。

## 更多说明

### 分数元组怎么比

| 手牌 | 牌型 | 元组 | 为什么 |
|---|---|---|---|
| 7S 7H 7D | three_of_a_kind | (2, [7]) | CATEGORY_RANK 里位置 2，三条点数 7 |
| 7S 7H KD | pair | (1, [7, 13]) | 位置 1，先对子点数 7 再单牌 13 |
| 9S 9H 2D | pair | (1, [9, 2]) | 位置 1，对子点数 9 |
| 3S 8H KD | high_card | (0, [13, 8, 3]) | 位置 0，三张从大到小 |

Python 比元组是逐项比：(2, ...) 大于 (1, ...)，三条赢对子，后面不用看。两个对子第一项都是 1，比第二项的列表，[9, 2] 大于 [7, 13]，因为先比 9 和 7。列表比列表也是逐项，所以全程只用 > 和 ==。

### 种子 42 三个玩家走一遍

| 步骤 | 发生了什么 | 日志 |
|---|---|---|
| 第 1 轮 | P1 拿 6C，P2 拿 9S，P3 拿 3S | deal round 1 三条 |
| 第 2 轮 | P1 拿 7H，P2 拿 5H，P3 拿 4H | deal round 2 三条 |
| 第 3 轮 | P1 拿 10S，P2 拿 8S，P3 拿 QD | deal round 3 三条 |
| 打分 | P1 [10, 7, 6]、P2 [9, 8, 5]、P3 [12, 4, 3]，都是 high_card | evaluate 三条 |
| 取最大 | 比第一张 12 > 10 > 9，P3 赢 | result: winner P3 |

发牌日志是 P1 P2 P3 P1 P2 P3 ... 交替出现。外层改成玩家、内层改成轮数的话，日志会先出现 P1 的三张，和题面"轮流发"对不上。
