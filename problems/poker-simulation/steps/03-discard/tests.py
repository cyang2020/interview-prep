import random
from solution import (Card, Player, make_deck, deal, evaluate_hand, evaluate_all, pick_winners, play,
                      discard, describe_result, keep_only_pair, keep_pair_or_better)


def hand(*cards):
    # 用 "7S" "KH" "10D" 这种写法造牌
    names = {"J": 11, "Q": 12, "K": 13}
    return [Card(int(c[:-1]) if c[:-1].isdigit() else names[c[:-1]], c[-1]) for c in cards]


def score(*cards):
    return evaluate_hand(hand(*cards))[1]


def category(*cards):
    return evaluate_hand(hand(*cards))[0]


def test_deal_round_robin():
    deck = make_deck(random.Random(1))
    players = [Player("P1"), Player("P2"), Player("P3")]
    log = []
    deal(deck, players, 3, log)
    assert all(len(p.hand) == 3 for p in players)                  # 每人三张
    assert len(deck) == 48 - 9                                      # 没有 A 是 48 张，发掉九张
    assert [l.split()[3] for l in log] == ["P1", "P2", "P3"] * 3    # 轮流发：P1 P2 P3 P1 P2 P3 ...
    assert log[0].startswith("deal round 1:") and log[-1].startswith("deal round 3:")   # 轮数从 1 记到 3


def test_category_detection():
    assert category("7S", "7H", "7D") == "three_of_a_kind"         # 某点数出现 3 次
    assert category("7S", "7H", "KD") == "pair"                    # 某点数出现 2 次
    assert category("3S", "8H", "KD") == "high_card"               # 都只出现 1 次


def test_cross_category_order():
    assert score("7S", "7H", "7D") > score("7S", "7H", "KD") > score("3S", "8H", "KD")   # 三条 > 对子 > 高牌
    assert score("2S", "2H", "2D") > score("KS", "KH", "QD")       # 最小的三条也大于最大的对子
    assert score("2S", "2H", "3D") > score("KS", "QH", "JD")       # 最小的对子也大于最大的高牌


def test_within_category():
    assert score("9S", "9H", "2D") > score("5S", "5H", "KD")       # 对子先比对子的点数
    assert score("7S", "7H", "KD") > score("7S", "7H", "2D")       # 对子点数相同再比单牌
    assert score("2S", "9H", "KD") > score("3S", "8H", "KD")       # 高牌第一张相同比第二张
    assert score("9S", "9H", "9D") > score("8S", "8H", "8D")       # 三条比三条的点数


def test_order_independent():
    assert score("KS", "7H", "7D") == score("7H", "KS", "7D") == score("7D", "7H", "KS")   # 同一手牌换顺序分数相同


def test_tie_returns_all():
    p1, p2, p3 = Player("P1"), Player("P2"), Player("P3")
    p1.hand = hand("3S", "8H", "KD")
    p2.hand = hand("5C", "5D", "2S")
    p3.hand = hand("3C", "8D", "KS")                               # 和 P1 点数完全相同
    log = []
    winners = pick_winners(evaluate_all([p1, p2, p3], log))
    assert [w.name for w in winners] == ["P2"]                      # 对子赢两手高牌
    assert len(log) == 3 and all(l.startswith("evaluate:") for l in log)   # 每人一条 evaluate
    p2.hand = hand("2C", "4D", "6S")
    winners = pick_winners(evaluate_all([p1, p2, p3], []))
    assert [w.name for w in winners] == ["P1", "P3"]                # 完全相同的两手一起返回


# ---- 第二问新增：同花 ----
def test_flush_detected():
    assert category("3H", "8H", "KH") == "flush"                   # 三张同花色：第一问判高牌，现在判同花
    assert category("3H", "8H", "KD") == "high_card"               # 花色不全同：还是高牌，没被误伤


def test_flush_position():
    assert score("7S", "7H", "7D") > score("3H", "8H", "KH") > score("7S", "7H", "KD")   # 三条 > 同花 > 对子
    assert score("2H", "3H", "4H") > score("KS", "KH", "QD")       # 最小的同花也大于最大的对子
    assert score("2S", "2H", "2D") > score("JH", "QH", "KH")       # 最小的三条也大于最大的同花


def test_flush_vs_flush():
    assert score("2H", "9H", "KH") > score("3S", "8S", "KS")       # 同花比同花逐张比点数
    assert score("3H", "8H", "KH") == score("3S", "8S", "KS")      # 点数相同花色不同并列


# ---- 第三问新增：弃牌 ----
def table():
    p1, p2, p3 = Player("P1"), Player("P2"), Player("P3")
    p1.hand = hand("7S", "7H", "7D")                               # 三条
    p2.hand = hand("5S", "5H", "KD")                               # 对子
    p3.hand = hand("3S", "8H", "KD")                               # 高牌
    return [p1, p2, p3]


def run(keep_rule):
    # 同一组固定手牌，从打分开始往后跑一遍
    log = []
    scored = evaluate_all(table(), log)
    if keep_rule is not None:
        scored = discard(scored, keep_rule, log)
    winners = pick_winners(scored)
    log.append(describe_result(winners))
    return [w.name for w in winners], log


def test_no_rule_unchanged():
    winners, log = run(None)
    assert winners == ["P1"]                                        # 不弃牌：三条赢
    assert not any(l.startswith("discard") for l in log)            # 没有 discard 行


def test_keep_only_pair():
    winners, log = run(keep_only_pair)
    assert winners == ["P2"]                                        # 三条和高牌都被弃，对子赢
    assert [l for l in log if l.startswith("discard")] == [
        "discard: P1 [7S, 7H, 7D] (three_of_a_kind)",
        "discard: P3 [3S, 8H, KD] (high_card)",
    ]                                                               # 按座位顺序逐条记录


def test_keep_pair_or_better():
    winners, log = run(keep_pair_or_better)
    assert winners == ["P1"]                                        # 三条也算：三条赢
    assert [l for l in log if l.startswith("discard")] == ["discard: P3 [3S, 8H, KD] (high_card)"]


def test_log_identical_except_discard_and_result():
    _, log_a = run(None)
    _, log_b = run(keep_only_pair)
    keep = lambda log: [l for l in log if not l.startswith(("discard", "result"))]
    assert keep(log_a) == keep(log_b)                               # evaluate 行完全一样：弃牌没碰打分


def test_all_discarded():
    winners, log = run(lambda category: False)
    assert winners == []                                            # 全部被弃：没有赢家
    assert log[-1] == "result: no winner, every hand was discarded"


def test_play_with_rule():
    _, log_plain = play(num_players=3, seed=42)
    winners, log = play(num_players=3, seed=42, keep_rule=keep_only_pair)
    assert [l for l in log if l.startswith("deal")] == [l for l in log_plain if l.startswith("deal")]   # 发牌一样
    assert winners == []                                            # 种子 42 三人都是高牌，全被弃
    assert sum(l.startswith("discard") for l in log) == 3


def test_play_log_shape():
    winners, log = play(num_players=3, seed=42)
    assert len(log) == 9 + 3 + 1                                    # 九条 deal、三条 evaluate、一条 result
    assert sum(l.startswith("deal") for l in log) == 9
    assert log[-1].startswith("result:")
    assert len(winners) >= 1                                        # 不弃牌时至少一个赢家
    assert play(num_players=3, seed=42)[1] == log                   # 同一个种子结果可复现


if __name__ == "__main__":
    tests = [test_deal_round_robin, test_category_detection, test_cross_category_order,
             test_within_category, test_order_independent, test_tie_returns_all,
             test_flush_detected, test_flush_position, test_flush_vs_flush,
             test_no_rule_unchanged, test_keep_only_pair, test_keep_pair_or_better,
             test_log_identical_except_discard_and_result, test_all_discarded, test_play_with_rule,
             test_play_log_shape]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
