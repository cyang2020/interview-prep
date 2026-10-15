"""第一问：每人三张牌，不看花色，三条 > 对子 > 高牌。

按顺序执行的几步，每步只做自己的事：
  1. 牌和牌堆        Card 带花色，第一问不看，第二问要用
  2. 发牌            轮流发，一轮每人一张，发三轮
  3. 打分            纯函数：三张牌进，(牌型名, 分数) 出，不改牌、不写日志
  4. 取最大          扫一遍 scored，并列的全留
日志是按时间顺序追加的字符串列表，和赢家一起返回。
"""
import random
from collections import Counter

# ---------- 1. 牌和牌堆 ----------

SUITS = ["S", "H", "D", "C"]            # 黑桃 红心 方块 梅花
RANKS = list(range(2, 14))              # 2..13，J/Q/K = 11/12/13。A 题目没提，先不放
RANK_NAMES = {11: "J", 12: "Q", 13: "K"}


class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"{RANK_NAMES.get(self.rank, self.rank)}{self.suit}"


def make_deck(rng):
    deck = [Card(rank, suit) for suit in SUITS for rank in RANKS]
    rng.shuffle(deck)                   # 用传进来的 rng，测试给固定种子就能复现
    return deck


class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []


# ---------- 2. 发牌 ----------

def deal(deck, players, cards_per_player, log):
    # 外层轮数、内层玩家，才是题面要求的"轮流发"
    for round_no in range(1, cards_per_player + 1):
        for player in players:
            card = deck.pop()
            player.hand.append(card)
            log.append(f"deal round {round_no}: {player.name} gets {card}")


# ---------- 3. 打分 ----------

# 牌型从小到大。分数的第一项查这张表，后面插新牌型只改这里和判定分支
CATEGORY_ORDER = ["high_card", "pair", "three_of_a_kind"]
CATEGORY_RANK = {name: i for i, name in enumerate(CATEGORY_ORDER)}


def evaluate_hand(cards):
    """返回 (牌型名, 分数)。分数是元组，直接用 > 和 == 比：
    第一项是牌型等级，第二项是破平局的点数列表。"""
    counts = Counter(card.rank for card in cards)
    most = max(counts.values())
    # 判定按等级从高到低走
    if most == 3:
        category = "three_of_a_kind"
    elif most == 2:
        category = "pair"
    else:
        category = "high_card"
    # 破平局：先按出现次数、再按点数，都从大到小。
    # 对子 7,7,K -> [7, 13]；高牌 3,8,K -> [13, 8, 3]。几种牌型共用这一条规则
    tiebreak = sorted(counts, key=lambda r: (counts[r], r), reverse=True)
    return category, (CATEGORY_RANK[category], tiebreak)


def evaluate_all(players, log):
    """每人打一次分，结果带着玩家往后传，后面的步骤不再重新打分。"""
    scored = []
    for player in players:
        category, score = evaluate_hand(player.hand)
        log.append(f"evaluate: {player.name} {player.hand} -> {category}")
        scored.append((player, category, score))
    return scored


# ---------- 4. 取最大 ----------

def pick_winners(scored):
    """并列策略：分数完全相同的一起返回。"""
    best_score = None
    winners = []
    for player, category, score in scored:
        if best_score is None or score > best_score:
            best_score, winners = score, [player]
        elif score == best_score:
            winners.append(player)
    return winners


def describe_result(winners):
    names = ", ".join(w.name for w in winners)
    return f"result: winner {names}" if len(winners) == 1 else f"result: tie between {names}"


# ---------- 串起来 ----------

def play(num_players=3, seed=None):
    rng = random.Random(seed)
    deck = make_deck(rng)
    players = [Player(f"P{i}") for i in range(1, num_players + 1)]
    log = []
    deal(deck, players, 3, log)
    scored = evaluate_all(players, log)
    winners = pick_winners(scored)
    log.append(describe_result(winners))
    return winners, log


if __name__ == "__main__":
    _, log = play(num_players=3, seed=42)
    print("\n".join(log))
