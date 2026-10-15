# 第三问：弃牌步骤，规则做成传进来的函数

## 这一问要做什么

- play 多收一个 keep_rule：判完牌型后按这条规则弃掉一部分手牌，被弃的人不参与比大小，日志里每弃一手记一条 discard。
- 规则例子是"不是对子的全弃"。不传 keep_rule 就和第二问一样。

## 核心思路

- play 多收一个可选参数 keep_rule，默认 None 不弃牌，行为和前两问一样；传了就在 evaluate_all 和 pick_winners 之间插一步 discard。
- discard 收 scored、keep_rule、log：对每条 (player, category, score)，keep_rule(category) 为真留进 survivors，否则追加一条 "discard: P1 [7S, 7H, 7D] (three_of_a_kind)"。只看牌型名，不碰手牌、不碰分数、不重新打分。
- keep_rule 是函数：牌型名进、布尔值出。写了两个：keep_only_pair 只留 pair；keep_pair_or_better 留 pair 和 three_of_a_kind。换规则换函数，discard 不改。
- pick_winners 不改，收到空列表自然返回空 winners；describe_result 加一个分支，winners 为空时写 "result: no winner, every hand was discarded"。
- 第一问把 evaluate_all 和 pick_winners 拆开在这里兑现：弃牌看 category，取最大看 score，两者都在 scored 里，打分只做一次，日志里每人只有一条 evaluate。
- 复杂度：discard 扫一遍 scored O(P)，总体不变。

## 思考与反问

- "不是对子就弃"三条要不要留？按字面读三条也不是对子，我先按字面做用 keep_only_pair；面试官说三条当然算，换成 keep_pair_or_better，改的是 play 的一个参数。
- 被弃的人出局还是补牌？我按出局做，discard 只从列表里把人去掉，不碰 deck。要补牌是新加一步 redeal，不是改 discard。
- 所有人都被弃了返回什么？我返回空的 winners 并在日志写明。不加这个分支，describe_result 会拼出 "result: tie between " 后面没名字。种子 42 那局三人都是 high_card，套上 keep_only_pair 正好全被弃。
- 为什么 keep_rule 是函数不是字符串：在 discard 里写 if category == "pair"，换规则要改 discard 内部，过滤逻辑和日志逻辑搅在一起，改错了日志也跟着错。
- 为什么弃牌不放进 evaluate_hand：打分是三张牌进分数出，不知道有几个玩家也不知道规则；塞进去的话几十条打分测试全要多传一个规则，补牌时还要动 deck。
- 追问"规则要看点数，比如点数小于 10 的对子也弃"：keep_rule 的参数从 category 改成整条 (player, category, score)，现有两个规则函数多忽略两个值。

## 测试要点

- test_no_rule_unchanged：固定三手牌 P1 三条、P2 对子、P3 高牌，不传规则 P1 赢，日志里没有 discard 行。
- test_keep_only_pair：keep_only_pair 弃掉 P1 三条和 P3 高牌，P2 对子赢；两条 discard 日志按座位顺序，带手牌和牌型名。
- test_keep_pair_or_better：keep_pair_or_better 只弃 P3 高牌，P1 三条赢。
- test_log_identical_except_discard_and_result：同一组手牌不弃牌和 keep_only_pair 跑两遍，去掉 discard 和 result 行后日志完全一样，证明弃牌没碰打分。
- test_all_discarded：规则对谁都返回 False，winners 为空，最后一条日志是 "result: no winner, every hand was discarded"。
- test_play_with_rule：种子 42 带 keep_only_pair 跑，deal 行和不带规则时完全一样，三条 discard，没有赢家。

## 更多说明

### 同一桌三手牌跑四遍

P1 三条 7S 7H 7D，P2 对子 5S 5H KD，P3 高牌 3S 8H KD。

| keep_rule | 被弃 | 赢家 | 比不弃牌多出的日志行 |
|---|---|---|---|
| None | 无 | P1 | 无 |
| keep_only_pair | P1、P3 | P2 | discard: P1 ...、discard: P3 ... |
| keep_pair_or_better | P3 | P1 | discard: P3 ... |
| 全弃 | P1、P2、P3 | 无 | 三条 discard，result 写 no winner |

四遍的 evaluate 行完全相同，只有 discard 行和 result 行不同。面试时跑给面试官看，这就是"弃牌没碰发牌和打分"的证据。

### 被弃的人要补牌怎么加

| 步骤 | 输入 | 做什么 |
|---|---|---|
| evaluate_all | players | 打分，得到 scored |
| discard | scored、keep_rule | 分成留下的和被弃的 |
| redeal（新加） | 被弃的玩家、deck | 清空 hand，各发三张，记 deal 日志 |
| evaluate_all | 补牌的玩家 | 再打分，记 evaluate 日志 |
| pick_winners | 留下的加补牌后的 | 取最大 |

discard 现在只返回 survivors，要补牌就让它也返回被弃的那部分。要不要再弃一轮、最多补几次，是新口径，要再问。
