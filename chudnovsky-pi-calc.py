import decimal
from decimal import Decimal, getcontext
import psutil
import time

def max_digits_from_ram(ratio):
    total_ram = psutil.virtual_memory().total
    usable_ram = total_ram * ratio
    return total_ram, int(usable_ram // 4)

def measure_cpu_speed(sample_size=500):
    getcontext().prec = sample_size + 5
    C = 426880 * Decimal(10005).sqrt()
    M = 1
    L = 13591409
    X = 1
    K = 6
    S = L
    start = time.time()
    for i in range(1, sample_size):
        M = (M * (K ** 3 - 16 * K)) // (i ** 3)
        L += 545140134
        X *= -262537412640768000
        S += Decimal(M * L) / X
        K += 12
    elapsed = time.time() - start
    return sample_size / elapsed  # iterations per second

def chudnovsky_pi_progressive(ratio=0.1, delay=0.05):
    total_ram, digits = max_digits_from_ram(ratio)
    speed = measure_cpu_speed()
    cpu_time_est = digits / speed
    total_time_est = cpu_time_est + (digits * delay)
    getcontext().prec = digits + 5
    print(f"Total RAM: {total_ram / (1024**3):.2f} GB")
    print(f"RAM usage ratio: {ratio*100:.0f}%")
    print(f"Estimated max digits: {digits}")
    print(f"CPU-only estimated runtime: {cpu_time_est/60:.2f} minutes")
    print(f"With delay included: {total_time_est/60:.2f} minutes\n")
    C = 426880 * Decimal(10005).sqrt()
    M = 1
    L = 13591409
    X = 1
    K = 6
    S = L
    for i in range(1, digits):
        M = (M * (K ** 3 - 16 * K)) // (i ** 3)
        L += 545140134
        X *= -262537412640768000
        S += Decimal(M * L) / X
        K += 12
        pi_str = str(C / S)[:i+2]
        print(pi_str, end="\r", flush=True)
        time.sleep(delay)
    print()

def main():
    default_ratio = 0.1
    total_ram_gb = psutil.virtual_memory().total / (1024**3)
    print(f"Detected RAM: {total_ram_gb:.2f} GB")
    print(f"Recommended RAM usage ratio: {default_ratio*100:.0f}%")
    choice = input("Do you want to change it? (y/n): ").strip().lower()
    if choice == 'y':
        try:
            ratio = float(input("Enter RAM usage ratio (0.01 for 1%): ").strip())
        except ValueError:
            print("Invalid input, using default.")
            ratio = default_ratio
    else:
        ratio = default_ratio
    delay = input("Enter delay between updates in seconds (default 0.05): ").strip()
    try:
        delay = float(delay) if delay else 0.05
    except ValueError:
        delay = 0.05
    chudnovsky_pi_progressive(ratio, delay)

if __name__ == "__main__":
    main()
