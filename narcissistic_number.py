import math


def judge(n: int) -> bool:
    digit = int(math.log10(n)) + 1
    if n == 1:
        return True
    elif digit < 3:
        return False
    else:
        na = str(n)
        _sum = 0
        for i in range(digit):
            _sum += int(na[i]) ** digit
        return _sum == n


def find_narcissistic_number(start: int, end: int) -> list:
    ret = []
    if end < start:
        return ret
    for i in range(start, end):
        if judge(i):
            ret.append(i)
    return ret
