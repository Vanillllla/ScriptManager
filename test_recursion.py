import os
import numpy as np
from scipy import linalg
from sys import setrecursionlimit

setrecursionlimit(50*(10**6))

import numpy as np
from scipy import linalg, integrate, optimize
import concurrent.futures


def comprehensive_stress_test():
    def worker(thread_id):
        # Каждый поток выполняет разные ресурсоемкие операции
        if thread_id % 4 == 0:
            # Матричные операции
            A = np.random.rand(500, 500)
            return linalg.eigvals(A)
        elif thread_id % 4 == 1:
            # Интегрирование
            result, _ = integrate.quad(lambda x: np.exp(-x ** 2) * np.sin(x ** 3), -100, 100)
            return result
        elif thread_id % 4 == 2:
            # Оптимизация
            result = optimize.minimize(
                lambda x: np.sum(x ** 4 - 16 * x ** 2 + 5 * x),
                np.random.rand(100),
                method='BFGS'
            )
            return result.fun
        else:
            # FFT
            data = np.random.random(100000)
            return np.max(np.abs(np.fft.fft(data)))

    # Многопоточное выполнение
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(worker, range(32)))

    return results


def rec(f, i):
    # print(i)
    i += 1
    f = f * 453879583485739857475
    f = f / 11271287352783548725

    return rec(f, i)

while True:
    try:
        comprehensive_stress_test()
        print(1)
        rec(1, 0)
    except Exception as e :
        print(f"+ забагованая рекурсия, ошибка : {e}")
    else:
        print("бля реально посчитал")
    finally:
        print("Давай по новой миша")