import math


def find_prime(start, end):
    li = []
    if start < 1:
        start = 1
    for i in range(start, end + 1):
        x = 0
        for j in range(2, int(math.sqrt(i)) + 1):
            if i % j == 0:
                x = 1
                break
        if x == 0 and i != 1:
            li.append(i)
    return li

# print(find_prime(1, 101))
# --> return prime numbers in range [start, end]
