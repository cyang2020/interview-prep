# 第二问：插入同花，三条 > 同花 > 对子 > 高牌

## 这一问要做什么

- 加一种牌型：三张花色全相同叫同花（flush），排在三条和对子之间，变成三条 > 同花 > 对子 > 高牌。
- 发牌、日志、play 的参数和返回值都和第一问一样。

## 核心思路

- 接口不变，play 的参数不变。只改打分这一步的两处：CATEGORY_ORDER 表和 evaluate_hand 的判定分支。
- CATEGORY_ORDER 变成 ["high_card", "pair", "flush", "three_of_a_kind"]，flush 插在 pair 和 three_of_a_kind 之间。CATEGORY_RANK 从表生成，three_of_a_kind 的位置号自动从 2 变 3，所有比较跟着用新顺序，没有手改任何数字。
- evaluate_hand 多算一个 is_flush：三张的 suit 去重后只剩一种。判定分支在 most == 3 之后、most == 2 之前加 elif is_flush。
- 破平局不改：同花三张点数必然不同，tiebreak 按出现次数再按点数排出来就是从大到小三张，3H 8H KH 排出 [13, 8, 3]，和高牌走同一条规则。
- deal、evaluate_all、pick_winners、play、日志一行不改。
- 复杂度不变，is_flush 多一次对三张牌花色去重，常数时间。

## 思考与反问

- 同花内部怎么比？按三张从大到小逐张比，花色不参与；3H 8H KH 和 3S 8S KS 点数相同花色不同算并列。这由 tiebreak 只看 rank 不看 suit 决定。
- 同花会不会和对子、三条撞上？一副牌同一点数四张花色各不同，三张同花色点数必然不同，所以同花只会和高牌撞，撞上时判 flush。
- 为什么 is_flush 分支放在 most == 3 之后：一副牌里三条不可能同花，放前面也不出错；但两副牌混用时 7H 7H 7H 既是三条又是同花，放前面会判成 flush，比三条低了。判定分支按等级从高到低排，多副牌也对。
- 第一问的检查一条不删直接再跑，全过说明加同花没改坏原来任何比较。题面备注说这一问比较逻辑的 bug 吃掉时间，检查先写好再改代码。
- 追问"要花色也分高下"：在 tiebreak 后面追加一个花色序号，是和面试官另约的口径，题面没要求。

## 测试要点

- test_flush_detected：3H 8H KH 三张同花色判 flush（第一问判 high_card）；3H 8H KD 花色不全同仍判 high_card，没被误伤。
- test_flush_position：三条 > 同花 > 对子；最小的同花 2H 3H 4H 大于最大的对子 K,K,Q，最小的三条 2,2,2 大于最大的同花 JH QH KH。
- test_flush_vs_flush：同花比同花逐张比点数，2H 9H KH 赢 3S 8S KS；3H 8H KH 和 3S 8S KS 分数相等。
- test_cross_category_order 和第一问其余 6 个测试原样沿用全过：三条、对子、高牌之间和内部的比较都没被插入 flush 改坏。

## 更多说明

### 三手牌第一问和第二问各判成什么

| 手牌 | 第一问判成 | 第二问判成 | 第二问元组 |
|---|---|---|---|
| 3H 8H KH | high_card | flush | (2, [13, 8, 3]) |
| 3H 8H KD | high_card | high_card | (0, [13, 8, 3]) |
| 5S 5H KD | pair | pair | (1, [5, 13]) |
| 7S 7H 7D | three_of_a_kind | three_of_a_kind | (3, [7]) |

第一手三张都是红心，第一项从 0 变 2，压过对子。第二手第三张是方块，还是高牌。三条的第一项从 2 变 3，是 CATEGORY_RANK 跟着表自动变的。

### 判定分支走一遍

7S 7H 7D 走到 most == 3 停，three_of_a_kind。3H 8H KH 过不了 most == 3，到 is_flush 停，flush。5S 5H KD 前两个都过不了，到 most == 2 停，pair。3S 8H KD 三个都过不了，high_card。一手牌从上往下走，第一个满足的分支就是它的牌型，所以分支顺序就是牌型等级从高到低的顺序。
