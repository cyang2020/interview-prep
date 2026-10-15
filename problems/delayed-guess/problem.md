# 题面

## 原题要点

> A server holds a secret integer between 1 and upperBound, inclusive. You are given upperBound and a GuessServer, but you cannot read the secret directly. Submit an integer guess by calling String check(int guess).
> Feedback is delayed by one call. The first call returns "PENDING". Every later call returns feedback about the previous guess: "TOO_LOW" if that guess was less than the secret, "TOO_HIGH" if that guess was greater than the secret, "CORRECT" if that guess matched the secret. The guess submitted in the current call becomes the new pending guess.
> Implement findNumber(int upperBound, GuessServer server) to return the secret. Every submitted guess must be within the allowed range and distinct from all earlier guesses.
> You may return a value as soon as the available information uniquely identifies it, even if the latest pending guess has not received feedback. You should use as few check() calls as possible. Constraints: 1 ≤ upperBound ≤ 10^9.
> Example 1: upperBound = 10, secret = 6. One valid sequence submits 5, 8, 6, and 7: the first response is "PENDING"; the second says 5 was too low, the third says 8 was too high, and the fourth confirms 6 was correct. The response to the fourth call does not describe the newly submitted guess (7). Example 2: upperBound = 50, secret = 17. Example 3: upperBound = 31, secret = 25.

Follow-up 原文：

> Extend the previous question to multiple independent games running in parallel. You are given an integer array upperBounds, where game i has its own hidden secret in [1, upperBounds[i]]. Instead of submitting one guess at a time, submit one guess for every unfinished game using String[] checkBatch(int[] guesses).
> Each guesses array must have the same length as upperBounds. While game i is unfinished, guesses[i] must be a new integer in [1, upperBounds[i]]. You cannot skip an unfinished game. Guess uniqueness is tracked per game. Different games may submit the same integer. Once game i is resolved, you must submit -1 for guesses[i] in every later batch. -1 does not count as a guess.
> As in the previous question, feedback is delayed by one call. feedback[i] is "PENDING" when no previous guess exists for that game, including when the previous batch used -1 at index i. Every value other than -1 in the current batch counts as an individual guess, even if the returned feedback from the previous batch is enough to determine that game's secret.
> Implement int[] findNumbers(int[] upperBounds, BatchGuessServer server) and return the hidden secrets in game-index order. You may stop submitting guesses for a game as soon as its secret is uniquely determined, and you may return once all games are resolved without requesting feedback for the final pending batch. You should use as few checkBatch() calls as possible. Constraints: 1 ≤ upperBounds.length ≤ 1000, 1 ≤ upperBounds[i] ≤ 10^9.
> Example 1: upperBounds = [4, 3], secrets = [3, 1]. checkBatch([2, 2]) returns ["PENDING", "PENDING"]. checkBatch([3, 1]) returns ["TOO_LOW", "TOO_HIGH"] for [2, 2], showing that game 0's secret is greater than 2 and game 1's secret is 1. checkBatch([4, -1]) returns ["CORRECT", "CORRECT"] for [3, 1], confirming game 0's secret is 3. The -1 skips the already completed game 1. Example 2: upperBounds = [10, 50, 8], secrets = [6, 17, 4]. Example 3: upperBounds = [20, 20, 20, 20], secrets = [2, 13, 8, 17].

题面给的是 Java 签名，没有附代码：

```
String   check(int guess)                                   // GuessServer
int      findNumber(int upperBound, GuessServer server)

String[] checkBatch(int[] guesses)                          // BatchGuessServer，follow-up
int[]    findNumbers(int[] upperBounds, BatchGuessServer server)
```

## 这题要你写的东西是什么

猜数字，但反馈慢一拍。正常的猜数字是：猜一个，立刻知道大了还是小了，根据结果猜下一个。这题把"立刻知道"改成"要等到下一次调用才知道"：你每次调 check 交一个数，拿回来的却是上一次交的那个数的结果。于是你被迫在还不知道上一次结果的情况下，就得决定这次交什么。

用例 1 走一遍，upperBound = 10，secret = 6，按 5、8、6、7 的顺序交：

| 第几次调用 | 交 | 返回 | 这个返回在说谁 |
|---|---|---|---|
| 1 | 5 | PENDING | 没有上一次 |
| 2 | 8 | TOO_LOW | 5 偏小 |
| 3 | 6 | TOO_HIGH | 8 偏大 |
| 4 | 7 | CORRECT | 6 对了，返回 6 |

两处要看懂。第 3 次交 6 的时候只知道 5 偏小，不知道 8 的结果；如果 8 的结果是 TOO_LOW，6 这一手就落在已经排除的区间里，白花。第 4 次交的 7 是被规则逼着交的：想知道 6 对不对必须再调一次，而 check 必须带一个新数，"只取结果不交数"这种操作不存在。

## 每个方法分别是什么意思

- check(guess)：你调服务器。它把 guess 收下，作为新的"在等结果的数"，同时返回上一个在等结果的数的结果。第一次没有上一个，返回 PENDING。
- findNumber(upperBound, server)：你要写的。里面是一个循环，不断调 check，直到现有信息能唯一确定答案，然后返回。整个程序只有你调服务器，没有服务器回调你。
- checkBatch(guesses)：follow-up 的批量版。guesses 长度等于局数，第 i 位是给第 i 局交的数，已完成的局填 -1。返回数组的第 i 位是第 i 局上一批交的数的结果；上一批该位是 -1 或没有上一批，返回 PENDING。
- findNumbers(upperBounds, server)：批量版要写的函数，按局的顺序返回每局的答案。

## 题目分几问

1. 单局，先写出一个一定正确、完全合规的解法：每次交的数在范围内、和之前所有交过的数都不同、一定能收敛。
2. 单局，把最坏情况下 check 的次数压到最少。题面原话是 as few check() calls as possible，这一问是整道题的核心。
3. 多局并行：每一批必须给所有未完成的局各交一个新数，完成的局填 -1，成本按 checkBatch 的次数算。

## 题面故意没说清楚的地方

- "最少次数"按最坏情况还是平均情况。面试默认最坏情况，和二分法讲 log n 是同一个口径。
- 第三问的成本到底按批次数算，还是批次数和猜测总数都要管。题面一句说"每个非 -1 的值都算一次猜测"，最后一句又说"尽量少调 checkBatch"。
- "这局已完成"是指我自己推断出来了，还是服务器回了 CORRECT。例 1 里局 1 是从 TOO_HIGH 推出来的，服务器没说 CORRECT 就填了 -1，所以应该是前者。
- upperBound = 1 的局答案不用猜就知道，能不能一次 check 都不调直接返回；多局版里能不能第一批就填 -1。
- 所有局都是 upperBound = 1 时，是不是 checkBatch 一次都不用调。

## 面试形式

主题加一个 follow-up，题面没给时长。主题的正确版很快能写出来，面试官会接着问"最坏多少次，能不能更少"，这一步才是区分度所在。Follow-up 考的是把单局的循环改成多局并排推进时，接口和记账怎么改，难点不在算法。
