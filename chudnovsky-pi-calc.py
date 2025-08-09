import decimal
from decimal import Decimal, getcontext
import psutil
import time
import platform
import subprocess
import sys
import os

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
    return sample_size / elapsed

def open_with_default_editor(filepath):
    try:
        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":
            subprocess.run(["open", filepath])
        else:
            subprocess.run(["xdg-open", filepath])
    except Exception as e:
        print(f"Failed to open the file automatically: {e}")

def chudnovsky_pi_live_optimized(ratio=0.1, delay=0.1, block_size=10, max_limit=20000, live_preview=True):
    total_ram, digits = max_digits_from_ram(ratio)
    digits = min(digits, max_limit)
    speed = measure_cpu_speed()
    est_cpu_time = digits / speed
    est_total_time = est_cpu_time + digits * delay

    print(f"Total RAM detected: {total_ram / (1024**3):.2f} GB")
    print(f"RAM usage ratio: {ratio*100:.1f}%")
    print(f"Calculated digits (limited by max {max_limit}): {digits}")
    print(f"CPU speed estimate: {speed:.2f} iterations/sec")
    print(f"Estimated CPU-only runtime: {est_cpu_time/60:.2f} minutes")
    print(f"Estimated total runtime with delay: {est_total_time/60:.2f} minutes\n")
    print("Starting Pi calculation...\n")

    getcontext().prec = digits + 5
    C = 426880 * Decimal(10005).sqrt()
    M = 1
    L = 13591409
    X = 1
    K = 6
    S = L

    pi_str = "3."
    if live_preview:
        print(pi_str, end="", flush=True)

    start_time = time.time()
    cpu_freqs = []
    cpu_percentages = []
    mem_usages = []

    pi_full_str = str(C / S)

    for i in range(1, digits):
        M = (M * (K ** 3 - 16 * K)) // (i ** 3)
        L += 545140134
        X *= -262537412640768000
        S += Decimal(M * L) / X
        K += 12

        if i % (block_size * 10) == 0 or i == digits - 1:
            pi_full_str = str(C / S)

        if i % block_size == 0:
            new_digits = pi_full_str[len(pi_str):len(pi_str)+block_size]
            pi_str += new_digits
            if live_preview:
                print("\r" + pi_str, end="", flush=True)
                time.sleep(delay)

            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                cpu_freqs.append(cpu_freq.current)
            cpu_percentages.append(psutil.cpu_percent(interval=None))
            mem_usages.append(psutil.virtual_memory().used / (1024**3))

    end_time = time.time()
    total_time = end_time - start_time

    avg_cpu_freq = sum(cpu_freqs)/len(cpu_freqs) if cpu_freqs else 0
    avg_cpu_percent = sum(cpu_percentages)/len(cpu_percentages) if cpu_percentages else 0
    avg_mem_usage = sum(mem_usages)/len(mem_usages) if mem_usages else 0

    if live_preview:
        print("\n\nCalculation finished.")
    else:
        print("Calculation finished.\n")
        print(pi_str)

    print(f"Total digits calculated: {digits}")
    print(f"Total calculation time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"Average CPU frequency: {avg_cpu_freq:.2f} MHz")
    print(f"Average CPU utilization: {avg_cpu_percent:.2f} %")
    print(f"Average RAM usage during calculation: {avg_mem_usage:.2f} GB")
    print(f"System: {platform.system()} {platform.release()}")
    print("\nNote: Power consumption measurement is not supported in this script.")

    save_choice = input("\nSave result to a file? (y/n): ").strip().lower()
    if save_choice == 'y':
        filename = f"pi_{digits}_digits.txt"
        with open(filename, "w") as f:
            f.write(pi_str + "\n\n")
            f.write(f"Total digits calculated: {digits}\n")
            f.write(f"Total calculation time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)\n")
            f.write(f"Average CPU frequency: {avg_cpu_freq:.2f} MHz\n")
            f.write(f"Average CPU utilization: {avg_cpu_percent:.2f} %\n")
            f.write(f"Average RAM usage during calculation: {avg_mem_usage:.2f} GB\n")
            f.write(f"System: {platform.system()} {platform.release()}\n")
            f.write("Note: Power consumption measurement is not supported in this script.\n")
        print(f"Result saved to {filename}")

        open_choice = input("Open the file with default text editor? (y/n): ").strip().lower()
        if open_choice == 'y':
            open_with_default_editor(filename)

def main():
    default_ratio = 0.1
    total_ram_gb = psutil.virtual_memory().total / (1024**3)
    print(f"Detected RAM: {total_ram_gb:.2f} GB")
    print(f"Recommended RAM usage ratio: {default_ratio*100:.0f}%")
    choice = input("Change RAM usage ratio? (y/n): ").strip().lower()
    if choice == 'y':
        try:
            ratio = float(input("Enter RAM usage ratio (0.01 for 1%): ").strip())
            if ratio <= 0 or ratio > 1:
                print("Invalid ratio, using default.")
                ratio = default_ratio
        except:
            print("Invalid input, using default.")
            ratio = default_ratio
    else:
        ratio = default_ratio

    delay_input = input("Enter delay between updates in seconds (default 0.1): ").strip()
    try:
        delay = float(delay_input) if delay_input else 0.1
    except:
        delay = 0.1

    block_input = input("Enter number of digits per block (default 10): ").strip()
    try:
        block_size = int(block_input) if block_input else 10
        if block_size <= 0:
            print("Invalid block size, using default 10.")
            block_size = 10
    except:
        block_size = 10

    live_preview_choice = input("Live preview? (y/n): ").strip().lower()
    live_preview = live_preview_choice == 'y'

    chudnovsky_pi_live_optimized(ratio=ratio, delay=delay, block_size=block_size, live_preview=live_preview)

if __name__ == "__main__":
    main()
