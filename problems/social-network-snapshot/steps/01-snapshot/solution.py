class SocialNetwork:
    def __init__(self):
        # 用户 -> 他关注的人的集合。
        # 用 set 是因为"是否已关注"要常数时间判断，而且往 set 里加已有元素不会变，
        # "重复关注不做任何事"这条规则就不用额外写判断。
        self._following = {}

    def add_user(self, user_id: str) -> None:
        if user_id in self._following:
            raise ValueError(f"user already exists: {user_id}")
        self._following[user_id] = set()

    def follow(self, follower: str, followee: str) -> None:
        # 用户不存在是调用方的错误，报错而不是吞掉，否则数据会悄悄变脏。
        if follower not in self._following:
            raise ValueError(f"unknown user: {follower}")
        if followee not in self._following:
            raise ValueError(f"unknown user: {followee}")
        if follower == followee:
            return  # 自己关注自己无害，不记录也不报错
        self._following[follower].add(followee)

    def create_snapshot(self) -> "Snapshot":
        return Snapshot(self._following)


class Snapshot:
    def __init__(self, following):
        # 每个用户的集合都用 frozenset 新建一份，而不是引用主表里的那个 set。
        # 只复制外层表的话，内层集合和主表共用同一个对象，之后 follow 往主表加人，快照也跟着变。
        # frozenset 同时保证快照自己也改不了。
        self._following = {user: frozenset(f) for user, f in following.items()}

    def is_following(self, follower: str, followee: str) -> bool:
        # 快照里没有这个用户（快照之后才加的）当作没关注任何人，返回 False 不报错。
        return followee in self._following.get(follower, frozenset())
