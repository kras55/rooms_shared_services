class NoItemFound(ValueError):
    def __init__(self, *args: object) -> None:  # noqa: D107
        msg = "No items found in dynamodb table: {}".format(args[0])
        args = args[1:]
        super().__init__(msg, *args)


class MoreThanOneItemFound(ValueError):
    def __init__(self, *args: object) -> None:  # noqa: D107
        msg = "More than one item found in dynamodb table: {}".format(args[0])
        args = args[1:]
        super().__init__(msg, *args)
