# 第一问：enqueue / reserve / pass / fail 基础版

## 面试官给的骨架

题面没有附真正的代码，只给了五个方法的签名。面试官一般是把签名写成下面这个空壳让你填，timeout 和 max_retry 参数从一开始就在，第一问先收下不用。

```python
class WorkQueue:
    def enqueue(self, job_id, timeout, max_retry):
        pass

    def reserve(self, job_id):
        pass

    def pass_(self, job_id):      # 口头叫 pass，Python 里 pass 是保留字
        pass

    def fail(self, job_id):
        pass

    def get_dlq(self):
        pass
```

## 思路

**开口先定两件事。** 一是 pass_ 的意思是"做成了"。二是 reserve(job_id) 是指名领某个任务；另一个版本是 reserve() 不指名、按入队顺序发下一个。我的实现两种都支持，job_id 传 None 就走第二种。如果面试官的版本只有指名领取，ready 这个队列整个可以不要。

**每个 job 一条记录。** 字段：job_id、state、attempts（被领走过几次）、timeout 和 max_retry（第二问才用）。状态三个：ready、reserved、completed。

**四个方法就是四条转移，每条先核对当前状态，状态不对就拒绝，返回 False 或 None。**

- enqueue：job_id 已存在就拒绝；否则新建记录，state 置 ready，job_id 放进 ready 队列尾部。
- reserve：记录必须处于 ready，改成 reserved，attempts 加 1。不处于 ready 的，不管是已被别人领走还是已完成，都领不到。
- pass_：记录必须处于 reserved，改成 completed。
- fail：记录必须处于 reserved，改回 ready，job_id 放回队列尾部。第一问没有次数限制。

**为什么每条都先核对状态。** 不核对的话，一个还没被领走的 job 收到一次误发的 pass 就直接 completed 了，没有任何 worker 跑过它；或者一个已经 completed 的 job 收到一次迟到的 fail 又回到队列重跑一遍。状态机的意义就是只允许表里列出的那几条转移，其余调用全部拒绝并返回失败。

**两个数据结构。** 一个 map 按 job_id 存记录，一个双端队列存可领取的 job_id 顺序。全部操作 O(1)。

**一个要主动讲出来的细节。** 队列和 map 会不一致：reserve("B") 指名领走了排在中间的 B，B 的 job_id 还留在队列里。所以 reserve() 不指名领取时，从队列头弹出一个 job_id 要对照 map 确认它仍是 ready，不是就丢掉继续弹。原则是队列只是索引，map 里的记录才算数。第二问的到期堆用的是同一个原则。

## 常见疑问

### reserve 和 pass 是干嘛的

**先把三个角色分开。** 这套代码里有三方：往队列里放任务的（网站）、队列本身（我们写的 WorkQueue）、干活的 worker（比如 10 台转码机）。队列自己不转码，它只做记账：哪个任务没人做、哪个任务谁在做、哪个任务做完了。

**用视频 123 走一遍，四个方法分别是谁在什么时候调的。**

1. 网站调 enqueue("123")：告诉队列"有个任务 123 要做"。队列记一条：123，状态 ready，意思是没人做、可以领。
2. 转码机 1 调 reserve("123")：转码机 1 说"123 我来做"。队列查记录，123 是 ready，就把状态改成 reserved，回答"行，归你了"。从这一刻起转码机 1 才开始真正转码，这个过程可能要 5 分钟，队列不参与。
3. 这 5 分钟里转码机 2 也调 reserve("123")：队列查记录，123 已经是 reserved，回答"不行，有人在做"。这就是 reserve 存在的意义：一个任务同一时间只能有一台机器在做。
4. 转码机 1 转完了，调 pass_("123")：告诉队列"123 做成了"。队列把状态改成 completed。以后谁再来 reserve("123") 都领不到，这个任务结束了。
5. 另一种结局：转码机 1 转到一半磁盘满了，调 fail("123")：告诉队列"123 我做砸了"。队列把状态改回 ready，这样转码机 2 再来 reserve("123") 就能领到，换一台机器重做。

一句话：reserve 是"我领走了，别人别碰"，pass 是"我做完了，这事结了"，fail 是"我没做成，放回去让别人领"。为什么领任务和报结果要分成两步而不是一步：因为干活要花时间，还可能失败，队列必须在这中间那 5 分钟知道"123 正在被谁做"，才能挡住第二台机器，也才能在失败时安排重做。

### 为什么要两个数据结构

两个结构回答两个不同的问题。

- jobs 这个 map 回答"任务 123 现在是什么状态"。pass_("123")、fail("123")、reserve("123") 来的时候都带着 job_id，要直接找到 123 这条记录看状态、改状态。map 按 job_id 查是 O(1)。
- ready 这个队列回答"下一个该发谁"。只有不指名的 reserve() 才用得到：worker 说"随便给我一个"，队列要按先来后到发。map 没有顺序，要在 map 里找下一个 ready 的得把所有记录扫一遍，O(n)。

**为什么不能只用队列。** 任务被 reserve 之后就不在"可领取"的队列里了，但它的记录必须还在某个地方：第二台机器来领时要能查到"已经被领走"而拒绝，5 分钟后转码机 1 的 pass_ 来时要能找到它改成 completed。队列里放不下 reserved 和 completed 这两种状态的任务，所以必须有 map。

**为什么不能只用 map。** 如果面试官的接口只有指名的 reserve(job_id)，确实只用 map 就够了。队列只是为了支持 reserve() 不指名、按顺序发的那个版本。

**两个结构在每一步长什么样**，用 A、B、C 三个任务走一遍：

| 操作 | jobs 里的状态 | ready 队列 |
|---|---|---|
| enqueue A、B、C | A ready，B ready，C ready | [A, B, C] |
| reserve("B") 指名 | B 变 reserved | [A, B, C]，B 还留在里面 |
| reserve() 不指名 | 弹出 A，A 是 ready，发出去，A 变 reserved | [B, C] |
| reserve() 不指名 | 弹出 B，查 map 是 reserved，丢掉；再弹出 C，是 ready，发出去 | [] |
| pass_("B") | B 变 completed | [] |
| fail("A") | A 变 ready，放回队列 | [A] |

第四行就是"队列只是索引，map 才算数"的意思：队列里的 B 已经过时了，弹出来要对照 map 才知道该不该发。
