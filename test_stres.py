import numpy as np
from scipy import linalg, integrate, fft
import numba
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import math
import random


class CPUKiller:
    def __init__(self):
        self.matrix_size = 2000
        self.fft_size = 2 ** 20
        self.integration_limits = 10
        self.optimization_dimensions = 100

    # 1. Интенсивные матричные операции
    def matrix_operations(self):
        print("Запуск матричных операций...")
        A = np.random.rand(self.matrix_size, self.matrix_size) + 1j * np.random.rand(self.matrix_size, self.matrix_size)
        B = np.random.rand(self.matrix_size, self.matrix_size) + 1j * np.random.rand(self.matrix_size, self.matrix_size)

        # Самые ресурсоемкие матричные операции
        results = []
        for _ in range(5):
            try:
                # Матричная экспонента - очень дорогая операция
                exp_A = linalg.expm(A)
                # Сингулярное разложение
                U, s, Vh = linalg.svd(A)
                # Определитель большой матрицы
                det_A = linalg.det(A)
                # Обратная матрица
                inv_A = linalg.inv(A)
                # Собственные значения
                eig_vals = linalg.eigvals(A)
                # Произведение матриц
                C = A @ B

                results.extend([exp_A, det_A, inv_A, eig_vals, C])
            except:
                continue

        return results

    # 2. Многократное FFT
    @numba.jit(nopython=True)
    def intensive_fft_operations(self, data):
        for i in range(100):
            spectrum = fft.fft(data)
            data = fft.ifft(spectrum)
        return np.abs(data)

    def fft_load(self):
        print("Запуск FFT операций...")
        real_data = np.random.rand(self.fft_size)
        complex_data = np.random.rand(self.fft_size) + 1j * np.random.rand(self.fft_size)

        results = []
        for _ in range(10):
            result1 = self.intensive_fft_operations(real_data)
            result2 = self.intensive_fft_operations(complex_data)
            results.extend([result1, result2])

        return results

    # 3. Многомерное интегрирование
    def complex_multidimensional_integration(self):
        print("Запуск многомерного интегрирования...")

        # 4-мерное интегрирование
        def integrand4d(x, y, z, w):
            return (math.sin(x * y * z * w) * math.exp(-x ** 2 - y ** 2 - z ** 2 - w ** 2) *
                    math.log(1 + abs(x * y * z * w)))

        # 3-мерное интегрирование
        def integrand3d(x, y, z):
            return (math.cos(x * y * z) * math.exp(-abs(x * y * z)) *
                    (x ** 2 + y ** 2 + z ** 2) ** 0.5)

        results = []
        limits = [-self.integration_limits, self.integration_limits]

        for _ in range(3):
            try:
                result4d, error4d = integrate.nquad(
                    integrand4d,
                    [limits, limits, limits, limits],
                    opts={'limit': 50}
                )

                result3d, error3d = integrate.nquad(
                    integrand3d,
                    [limits, limits, limits],
                    opts={'limit': 100}
                )

                results.extend([result4d, result3d])
            except:
                continue

        return results

    # 4. Вычисление специальных функций
    def special_functions_calculation(self):
        print("Запуск вычисления специальных функций...")
        x = np.linspace(0.1, 100, 100000)

        results = []
        # Ресурсоемкие специальные функции
        for _ in range(5):
            try:
                gamma_vals = np.array([math.gamma(val) for val in x])
                zeta_vals = np.array([math.gamma(val) * math.sin(val) for val in x])  # аппроксимация
                erf_vals = np.array([math.erf(val) for val in x])
                bessel_vals = np.array([math.gamma(val) * math.cos(val) for val in x])  # аппроксимация

                results.extend([gamma_vals, zeta_vals, erf_vals, bessel_vals])
            except:
                continue

        return results

    # 5. Генерация простых чисел (очень ресурсоемко)
    @numba.jit(nopython=True)
    def is_prime(self, n):
        if n < 2:
            return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return False
        return True

    def prime_number_generation(self, limit=1000000):
        print("Запуск генерации простых чисел...")
        primes = []
        count = 0
        n = 2

        while count < limit:
            if self.is_prime(n):
                primes.append(n)
                count += 1
            n += 1

        return primes

    # 6. Фрактальные вычисления (Множество Мандельброта)
    @numba.jit(nopython=True)
    def mandelbrot(self, width=1000, height=1000, max_iter=1000):
        result = np.zeros((height, width))
        for x in range(width):
            for y in range(height):
                zx, zy = 0, 0
                cx = (x - width / 2) * 4 / width
                cy = (y - height / 2) * 4 / height
                i = 0
                while zx * zx + zy * zy < 4 and i < max_iter:
                    zx, zy = zx * zx - zy * zy + cx, 2 * zx * zy + cy
                    i += 1
                result[y, x] = i
        return result

    def fractal_calculations(self):
        print("Запуск фрактальных вычислений...")
        results = []
        for _ in range(3):
            mandel = self.mandelbrot(800, 800, 500)
            results.append(mandel)
        return results

    # 7. Монте-Карло интегрирование
    @numba.jit(nopython=True)
    def monte_carlo_integration(self, samples=10000000):
        count_inside = 0
        for _ in range(samples):
            x, y = random.random(), random.random()
            if x * x + y * y <= 1:
                count_inside += 1
        return 4 * count_inside / samples

    def intensive_monte_carlo(self):
        print("Запуск Monte-Carlo вычислений...")
        results = []
        for _ in range(10):
            pi_approx = self.monte_carlo_integration()
            results.append(pi_approx)
        return results

    # 8. Параллельные вычисления
    def parallel_computations(self):
        print("Запуск параллельных вычислений...")

        def worker(task_id):
            if task_id % 4 == 0:
                # Матричные операции в потоке
                A = np.random.rand(500, 500)
                return linalg.eigvals(A)
            elif task_id % 4 == 1:
                # FFT в потоке
                data = np.random.rand(2 ** 18)
                return np.max(np.abs(fft.fft(data)))
            elif task_id % 4 == 2:
                # Генерация простых чисел
                primes = []
                for i in range(100000):
                    if self.is_prime(i):
                        primes.append(i)
                return len(primes)
            else:
                # Интегрирование
                result, _ = integrate.quad(lambda x: math.exp(-x ** 2) * math.sin(x ** 3), -10, 10)
                return result

        # Запуск в нескольких процессах
        with ProcessPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(worker, range(32)))

        return results

    # Главный метод - запуск всего сразу
    def maximum_cpu_load(self, duration_seconds=60):
        import time
        start_time = time.time()
        all_results = []

        print(f"НАЧАЛО МАКСИМАЛЬНОЙ НАГРУЗКИ НА CPU НА {duration_seconds} СЕКУНД")
        print("=" * 60)

        while time.time() - start_time < duration_seconds:
            try:
                # Запуск всех методов по очереди
                all_results.extend(self.matrix_operations())
                all_results.extend(self.fft_load())
                all_results.extend(self.complex_multidimensional_integration())
                all_results.extend(self.special_functions_calculation())
                all_results.extend([self.prime_number_generation(10000)])
                all_results.extend(self.fractal_calculations())
                all_results.extend(self.intensive_monte_carlo())
                all_results.extend(self.parallel_computations())

                print(f"Выполнено итераций: {len(all_results)}")

            except Exception as e:
                print(f"Ошибка: {e}")
                continue

        print("=" * 60)
        print("НАГРУЗКА ЗАВЕРШЕНА")
        return all_results


# Дополнительная функция для постоянной нагрузки
def continuous_cpu_stress():
    """Бесконечная нагрузка на CPU"""
    killer = CPUKiller()
    print("БЕСКОНЕЧНАЯ НАГРУЗКА НА CPU... (Ctrl+C для остановки)")

    iteration = 0
    while True:
        try:
            iteration += 1
            print(f"Итерация {iteration}")
            killer.maximum_cpu_load(10)  # 10 секунд на итерацию
        except KeyboardInterrupt:
            print("\nОстановлено пользователем")
            break
        except Exception as e:
            print(f"Ошибка: {e}")
            continue


# Запуск программыx
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Максимальная нагрузка на CPU')
    parser.add_argument('--duration', type=int, default=60, help='Длительность в секундах')
    parser.add_argument('--continuous', action='store_true', help='Бесконечная нагрузка')

    args = parser.parse_args()

    killer = CPUKiller()

    if args.continuous:
        continuous_cpu_stress()
    else:
        results = killer.maximum_cpu_load(args.duration)
        print(f"Выполнено операций: {len(results)}")