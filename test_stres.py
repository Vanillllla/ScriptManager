import numpy as np
from scipy import linalg
import numba
import math
import sys
import threading
import time

# Увеличиваем глубину рекурсии
sys.setrecursionlimit(1000000)


class MemoryIntensiveRecursion:
    def __init__(self):
        self.memory_chunks = []
        self.recursion_depth = 0
        self.max_depth = 10000

    # Глубокая рекурсия с накоплением данных в памяти
    def deep_recursion(self, depth, data_size=1000):
        self.recursion_depth = depth

        # Базовый случай рекурсии
        if depth >= self.max_depth:
            return depth

        # Создаем большой блок данных в памяти
        chunk = np.random.rand(data_size, data_size)
        self.memory_chunks.append(chunk)

        # Рекурсивный вызов
        return self.deep_recursion(depth + 1, data_size)

    # Рекурсия с ветвлением (создает дерево рекурсивных вызовов)
    def branching_recursion(self, depth, branch_factor=2):
        if depth >= 500:  # Меньшая глубина из-за экспоненциального роста
            return depth

        results = []
        # Создаем несколько ветвей рекурсии
        for i in range(branch_factor):
            # Большой блок данных для каждой ветви
            data = np.random.rand(500, 500)
            self.memory_chunks.append(data)

            # Рекурсивный вызов
            result = self.branching_recursion(depth + 1, branch_factor)
            results.append(result)

        return sum(results)

    # Взаимно рекурсивные функции
    def recursive_a(self, depth):
        if depth >= 2000:
            return depth

        data = np.random.rand(300, 300)
        self.memory_chunks.append(data)
        return self.recursive_b(depth + 1)

    def recursive_b(self, depth):
        if depth >= 2000:
            return depth

        data = np.random.rand(300, 300)
        self.memory_chunks.append(data)
        return self.recursive_a(depth + 1)


@numba.jit(nopython=True)
def intensive_calculation():
    total = 0
    for i in range(100000000):
        total += math.sqrt(i) * math.sin(i) * math.log(i + 1)
    return total


# Функция для создания нагрузки на память в отдельном потоке
def memory_stress_thread():
    print("Запуск глубокой рекурсии для нагрузки на память...")
    memory_killer = MemoryIntensiveRecursion()

    try:
        # Запускаем разные типы рекурсии
        print("Запуск линейной рекурсии...")
        result1 = memory_killer.deep_recursion(0, 800)
        print(f"Линейная рекурсия завершена, глубина: {result1}")

        print("Запуск ветвящейся рекурсии...")
        result2 = memory_killer.branching_recursion(0, 3)
        print(f"Ветвящаяся рекурсия завершена, результат: {result2}")

        print("Запуск взаимной рекурсии...")
        result3 = memory_killer.recursive_a(0)
        print(f"Взаимная рекурсия завершена, глубина: {result3}")

    except RecursionError as e:
        print(f"Достигнута максимальная глубина рекурсии: {e}")
    except MemoryError as e:
        print(f"Исчерпана оперативная память: {e}")

    # Удерживаем данные в памяти
    while True:
        time.sleep(1)
        # Периодически добавляем новые данные
        if len(memory_killer.memory_chunks) < 100:
            memory_killer.memory_chunks.append(np.random.rand(1000, 1000))


# Функция для создания фрагментации памяти
def memory_fragmentation():
    print("Создание фрагментации памяти...")
    fragments = []

    # Создаем массивы разных размеров для фрагментации памяти
    for i in range(10000):
        size = np.random.randint(100, 10000)
        fragment = np.random.rand(size)
        fragments.append(fragment)

        if i % 1000 == 0:
            print(f"Создано фрагментов: {i}")

    # Удаляем каждый второй фрагмент для создания "дыр" в памяти
    for i in range(0, len(fragments), 2):
        fragments[i] = None

    return fragments


def quick_cpu_stress():
    print("Быстрая максимальная нагрузка на CPU и память...")

    # Запускаем нагрузку на память в отдельном потоке
    memory_thread = threading.Thread(target=memory_stress_thread, daemon=True)
    memory_thread.start()

    # Запускаем фрагментацию памяти в другом потоке
    fragmentation_thread = threading.Thread(target=memory_fragmentation, daemon=True)
    fragmentation_thread.start()

    # 1. Большие матрицы (нагрузка на CPU и память)
    print("Создание больших матриц...")
    A = np.random.rand(2000, 2000)  # Увеличили размер для большей нагрузки на память
    matrix_results = []
    for i in range(15):  # Увеличили количество итераций
        print(f"Матричные операции, итерация {i + 1}")
        eigvals = linalg.eigvals(A)
        inv_A = linalg.inv(A)
        matrix_results.extend([eigvals, inv_A])

        # Создаем дополнительные матрицы для нагрузки на память
        if i % 3 == 0:
            extra_matrix = np.random.rand(1500, 1500)
            matrix_results.append(extra_matrix)

    # 2. Интенсивные вычисления
    print("Запуск интенсивных вычислений...")
    result = intensive_calculation()

    # 3. Многократные операции с накоплением данных в памяти
    print("Запуск многократных операций с накоплением данных...")
    all_results = []
    iteration = 0

    while True:
        try:
            iteration += 1
            print(f"Итерация {iteration}")

            # Создаем большие матрицы и выполняем операции
            B = np.random.rand(1200, 1200)
            C = linalg.expm(B)

            # Интенсивные вычисления
            calc_result = intensive_calculation()

            # Сохраняем результаты для нагрузки на память
            all_results.extend([B, C, calc_result])

            # Периодически создаем очень большие массивы
            if iteration % 5 == 0:
                huge_array = np.random.rand(5000, 5000)
                all_results.append(huge_array)
                print(f"Создан огромный массив {5000}x{5000}")

            # Очищаем часть данных каждые 10 итераций для имитации реального использования
            if iteration % 10 == 0 and len(all_results) > 20:
                # Удаляем старые данные, но не все
                all_results = all_results[-15:]

        except KeyboardInterrupt:
            print("\nОстановлено пользователем")
            break
        except MemoryError as e:
            print(f"Обнаружена нехватка памяти: {e}")
            # Пытаемся освободить память
            all_results.clear()
            import gc
            gc.collect()
            print("Память очищена, продолжаем...")


if __name__ == "__main__":
    quick_cpu_stress()