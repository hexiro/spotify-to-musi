import asyncio


def remove_parens(title: str) -> str:
    bracket_groups = (
        ("[", "]"),
        ("(", ")"),
        ("{", "}"),
    )
    for left, right in bracket_groups:
        while left in title and right in title:
            left_index = title.index(left)
            right_index = title.index(right, left_index)

            title = title[:left_index] + title[right_index + 1 :]

    return title


def remove_features_from_title(title: str) -> str:
    ft_index = title.find("ft")
    feat_index = title.find("feat")

    featuring_index = ft_index if ft_index != -1 else feat_index

    if featuring_index != -1:
        title = title[:featuring_index]

    return title


# reference: https://stackoverflow.com/a/61478547/10830115
async def gather_with_concurrency(n: int, *coros):
    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(sem_coro(c) for c in coros))