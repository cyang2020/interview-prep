import random
from solution import Card, Player, make_deck, deal, evaluate_hand, evaluate_all, pick_winners, play


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


def test_play_log_shape():
    winners, log = play(num_players=3, seed=42)
    assert len(log) == 9 + 3 + 1                                    # 九条 deal、三条 evaluate、一条 result
    assert sum(l.startswith("deal") for l in log) == 9
    assert log[-1].startswith("result:")
    assert len(winners) >= 1                                        # 不弃牌时至少一个赢家
    assert play(num_players=3, seed=42)[1] == log                   # 同一个种子结果可复现


if __name__ == "__main__":
    tests = [test_deal_round_robin, test_category_detection, test_cross_category_order,
             test_within_category, test_order_independent, test_tie_returns_all, test_play_log_shape]
    for t in tests:
        t()
    print(f"all {len(tests)} passed")
