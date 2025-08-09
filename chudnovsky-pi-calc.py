import decimal
from decimal import Decimal, getcontext
import psutil
import time
import platform
import subprocess
import os
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import math
import gc

def get_hardware_info():
    """Get detailed hardware information for optimization"""
    info = {
        'total_ram_gb': psutil.virtual_memory().total / (1024**3),
        'available_ram_gb': psutil.virtual_memory().available / (1024**3),
        'cpu_physical_cores': psutil.cpu_count(logical=False),
        'cpu_logical_cores': psutil.cpu_count(logical=True),
        'platform': platform.system(),
        'architecture': platform.machine(),
        'cpu_freq': None,
        'cache_info': {}
    }

    # CPU frequency detection
    try:
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            info['cpu_freq'] = {
                'current': cpu_freq.current,
                'min': cpu_freq.min,
                'max': cpu_freq.max
            }
    except:
        pass

    # Cache size detection (Linux)
    if platform.system() == "Linux":
        try:
            for cache_level in [1, 2, 3]:
                cache_path = f"/sys/devices/system/cpu/cpu0/cache/index{cache_level}/size"
                if os.path.exists(cache_path):
                    with open(cache_path, 'r') as f:
                        cache_size = f.read().strip()
                        info['cache_info'][f'L{cache_level}'] = cache_size
        except:
            pass

    return info

def recommend_optimal_settings(digits, hardware_info):
    """Recommend optimal settings based on hardware"""
    recommendations = {
        'ram_ratio': 0.1,
        'cores_to_use': hardware_info['cpu_logical_cores'],
        'chunk_size': 1000,
        'method': 1,
        'precision_buffer': 200
    }

    # RAM-based recommendations
    available_gb = hardware_info['available_ram_gb']
    if available_gb > 8:
        recommendations['ram_ratio'] = 0.3  # Use more RAM if available
    elif available_gb > 16:
        recommendations['ram_ratio'] = 0.5
    elif available_gb < 4:
        recommendations['ram_ratio'] = 0.05  # Conservative for low RAM

    # CPU-based recommendations
    physical_cores = hardware_info['cpu_physical_cores']
    logical_cores = hardware_info['cpu_logical_cores']

    # If hyperthreading is available and digits are large, use it
    if digits > 50000 and logical_cores > physical_cores:
        recommendations['cores_to_use'] = logical_cores
        recommendations['method'] = 2  # Parallel method for large calculations
    elif digits > 10000:
        recommendations['cores_to_use'] = min(physical_cores, 8)  # Don't overuse cores
        recommendations['method'] = 2
    else:
        recommendations['cores_to_use'] = min(physical_cores, 4)
        recommendations['method'] = 1  # Single-core for small calculations

    # Chunk size optimization based on cache and digits
    if digits > 100000:
        recommendations['chunk_size'] = max(5000, digits // (recommendations['cores_to_use'] * 2))
    elif digits > 10000:
        recommendations['chunk_size'] = max(1000, digits // (recommendations['cores_to_use'] * 4))
    else:
        recommendations['chunk_size'] = max(100, digits // max(1, recommendations['cores_to_use']))

    # Precision buffer based on digits
    if digits > 100000:
        recommendations['precision_buffer'] = 500
    elif digits > 10000:
        recommendations['precision_buffer'] = 300

    return recommendations

def display_hardware_info(hardware_info):
    """Display detected hardware information"""
    print("=== Hardware Detection ===")
    print(f"RAM: {hardware_info['total_ram_gb']:.1f} GB total, {hardware_info['available_ram_gb']:.1f} GB available")
    print(f"CPU: {hardware_info['cpu_physical_cores']} physical cores, {hardware_info['cpu_logical_cores']} logical cores")

    if hardware_info['cpu_freq']:
        freq = hardware_info['cpu_freq']
        print(f"CPU Frequency: {freq['current']:.0f} MHz (max: {freq['max']:.0f} MHz)")

    if hardware_info['cache_info']:
        cache_str = ", ".join([f"{level}: {size}" for level, size in hardware_info['cache_info'].items()])
        print(f"CPU Cache: {cache_str}")

    print(f"Platform: {hardware_info['platform']} ({hardware_info['architecture']})")
    print()

def max_digits_from_ram(ratio):
    total_ram = psutil.virtual_memory().total
    usable_ram = total_ram * ratio
    max_digits = int(usable_ram // 4)
    return total_ram, max_digits

def get_max_digits_by_cpu():
    return 10**7

def ask_user_for_digits(max_digits):
    while True:
        val = input(f"Enter number of digits to calculate (max {max_digits}): ").strip()
        if val == '':
            return max_digits
        try:
            num = int(val)
            if 1 <= num <= max_digits:
                return num
            print(f"Please enter a number between 1 and {max_digits}.")
        except:
            print("Invalid input, please enter a valid integer.")

def open_with_default_editor(filepath):
    try:
        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":
            subprocess.run(["open", filepath])
        else:
            subprocess.run(["xdg-open", filepath])
    except Exception as e:
        print(f"Failed to open file: {e}")

def measure_cpu_speed(sample_size=500):
    getcontext().prec = sample_size + 50
    C = 426880 * Decimal(10005).sqrt()
    M = Decimal(1)
    L = Decimal(13591409)
    X = Decimal(1)
    K = 6
    S = Decimal(L)
    start = time.time()
    for i in range(1, sample_size):
        K_cubed = Decimal(K) * Decimal(K) * Decimal(K)
        numerator = K_cubed - Decimal(16) * Decimal(K)
        denominator = Decimal(i) * Decimal(i) * Decimal(i)
        M = M * numerator / denominator
        L += Decimal(545140134)
        X *= Decimal(-262537412640768000)
        S += (M * L) / X
        K += 12
    elapsed = time.time() - start
    return sample_size / elapsed

def chudnovsky_term_optimized(i):
    """Optimized single term calculation with memory management"""
    M = Decimal(1)
    L = Decimal(13591409)
    X = Decimal(1)
    K = 6

    for j in range(1, i+1):
        # Use in-place operations where possible
        K_cubed = K ** 3
        M *= (K_cubed - 16 * K)
        M //= (j ** 3)
        L += 545140134
        X *= -262537412640768000
        K += 12

    result = (M * L) / X
    # Clear intermediate variables
    del M, L, X
    return result

def run_simple_method_optimized(ratio, digits, delay, block_size, live_preview):
    total_ram, max_digits_by_ram = max_digits_from_ram(ratio)
    max_digits_by_cpu = get_max_digits_by_cpu()
    max_digits_possible = min(max_digits_by_ram, max_digits_by_cpu)
    if digits > max_digits_possible:
        print(f"Reducing digits from {digits} to max allowed {max_digits_possible}")
        digits = max_digits_possible

    speed = measure_cpu_speed()
    est_cpu_time = digits / speed
    est_total_time = est_cpu_time + digits * delay

    print(f"Total RAM: {total_ram / (1024**3):.2f} GB")
    print(f"RAM usage ratio: {ratio*100:.1f}%")
    print(f"Digits: {digits}")
    print(f"CPU speed estimate: {speed:.2f} iters/sec")
    print(f"Estimated CPU-only runtime: {est_cpu_time/60:.2f} minutes")
    print(f"Estimated total runtime with delay: {est_total_time/60:.2f} minutes\n")
    print("Starting optimized Pi calculation...\n")

    # Set very high precision for intermediate calculations
    getcontext().prec = digits + 200
    C = 426880 * Decimal(10005).sqrt()

    M = Decimal(1)
    L = Decimal(13591409)
    X = Decimal(1)
    K = 6
    S = Decimal(L)

    start_time = time.time()
    last_printed_len = 0
    gc_counter = 0

    for i in range(1, digits):
        # Use Decimal types explicitly and regular division
        K_cubed = Decimal(K) * Decimal(K) * Decimal(K)
        numerator = K_cubed - Decimal(16) * Decimal(K)
        denominator = Decimal(i) * Decimal(i) * Decimal(i)

        # Use regular division instead of floor division
        M = M * numerator / denominator
        L += Decimal(545140134)
        X *= Decimal(-262537412640768000)

        # Add term to sum
        term = (M * L) / X
        S += term
        K += 12

        # Periodic garbage collection to prevent memory buildup
        gc_counter += 1
        if gc_counter % 1000 == 0:
            gc.collect()

        if live_preview and i % block_size == 0:
            pi_val = C / S
            # Limit string conversion to needed digits only
            pi_str = str(pi_val)[:min(i+2, digits+2)]
            print("\r" + pi_str.ljust(last_printed_len), end="", flush=True)
            last_printed_len = max(last_printed_len, len(pi_str))
            time.sleep(delay)

    pi_val = C / S
    print("\nCalculation finished.\n")
    print(str(pi_val)[:digits+2])
    total_time = time.time() - start_time

    print(f"\nTotal calculation time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")

def chunked_terms_optimized(start, end, digits):
    """Optimized chunked calculation with better memory management"""
    # Set high precision for this process
    chunk_prec = max(digits + 200, 2000)
    getcontext().prec = chunk_prec

    # Initialize variables with proper Decimal types
    M = Decimal(1)
    L = Decimal(13591409)
    X = Decimal(1)
    K = 6

    # Calculate M, L, X, K for start position using more stable method
    if start > 0:
        # Use regular division instead of floor division for better numerical stability
        for j in range(1, start + 1):
            K_cubed = Decimal(K) * Decimal(K) * Decimal(K)
            numerator = K_cubed - Decimal(16) * Decimal(K)
            denominator = Decimal(j) * Decimal(j) * Decimal(j)

            # Use regular division and then convert to integer if needed
            M = M * numerator / denominator
            L += Decimal(545140134)
            X *= Decimal(-262537412640768000)
            K += 12

    S = Decimal(0)

    # Calculate chunk terms
    for i in range(start, end):
        if i == 0:
            # First term: L / X
            term = L / X
        else:
            # Update values for current iteration
            if i > start or start == 0:
                K_cubed = Decimal(K) * Decimal(K) * Decimal(K)
                numerator = K_cubed - Decimal(16) * Decimal(K)
                denominator = Decimal(i) * Decimal(i) * Decimal(i)

                # Use regular division for better stability
                M = M * numerator / denominator
                L += Decimal(545140134)
                X *= Decimal(-262537412640768000)
                K += 12

            # Calculate term: (M * L) / X
            term = (M * L) / X

        S += term

        # Periodic cleanup for long chunks
        if (i - start + 1) % 1000 == 0:
            gc.collect()

    return S

def run_parallel_chunked_method_optimized(ratio, digits, delay, block_size, live_preview, recommended_cores=None):
    total_ram, max_digits_by_ram = max_digits_from_ram(ratio)
    max_digits_by_cpu = get_max_digits_by_cpu()
    max_digits_possible = min(max_digits_by_ram, max_digits_by_cpu)
    if digits > max_digits_possible:
        print(f"Reducing digits from {digits} to max allowed {max_digits_possible}")
        digits = max_digits_possible

    cpu_count = psutil.cpu_count(logical=True)
    print(f"Detected {cpu_count} logical CPU cores.")

    if recommended_cores:
        print(f"Hardware-optimized recommendation: {recommended_cores} cores")
        cores_input = input(f"How many CPU cores to use? (recommended {recommended_cores}, max {cpu_count}, default {recommended_cores}): ").strip()
        use_cores = recommended_cores
    else:
        cores_input = input(f"How many CPU cores to use? (max {cpu_count}, default {cpu_count}): ").strip()
        use_cores = cpu_count

    if cores_input:
        try:
            cores_val = int(cores_input)
            if 1 <= cores_val <= cpu_count:
                use_cores = cores_val
        except:
            pass

    speed = measure_cpu_speed()
    est_cpu_time = digits / speed
    est_total_time = est_cpu_time + digits * delay

    print(f"Total RAM: {total_ram / (1024**3):.2f} GB")
    print(f"RAM usage ratio: {ratio*100:.1f}%")
    print(f"Digits: {digits}")
    print(f"CPU speed estimate (single-core): {speed:.2f} iters/sec")
    print(f"Estimated CPU-only runtime: {est_cpu_time/60:.2f} minutes")
    print(f"Estimated total runtime with delay: {est_total_time/60:.2f} minutes")
    print(f"Using {use_cores} CPU cores.")
    print("Starting optimized parallel Pi calculation...\n")

    # Set very high precision to avoid numerical issues
    getcontext().prec = digits + 200
    C = 426880 * Decimal(10005).sqrt()

    # Hardware-optimized chunk size
    if recommended_cores:
        optimal_chunk_size = max(500, min(50000, digits // max(1, use_cores)))
    else:
        optimal_chunk_size = max(500, min(50000, digits // max(1, use_cores)))

    ranges = []
    start_i = 0
    while start_i < digits:
        end_i = min(digits, start_i + optimal_chunk_size)
        ranges.append((start_i, end_i))
        start_i = end_i

    print(f"Using {len(ranges)} chunks of ~{optimal_chunk_size} terms each")

    start_time = time.time()
    chunk_results = [None] * len(ranges)  # Preserve order

    try:
        with ProcessPoolExecutor(max_workers=use_cores) as executor:
            # Submit jobs with index to maintain order
            future_to_index = {
                executor.submit(chunked_terms_optimized, r[0], r[1], digits): i
                for i, r in enumerate(ranges)
            }

            completed_chunks = 0
            total_chunks = len(ranges)

            for future in as_completed(future_to_index):
                try:
                    index = future_to_index[future]
                    chunk_results[index] = future.result()
                    completed_chunks += 1

                    progress = completed_chunks / total_chunks
                    elapsed = time.time() - start_time

                    if progress > 0:
                        remaining = elapsed * (1 - progress) / progress
                    else:
                        remaining = est_total_time

                    elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
                    remaining_str = time.strftime("%H:%M:%S", time.gmtime(remaining))

                    print(f"\rElapsed: {elapsed_str} | Progress: {progress*100:.1f}% | Est. remaining: {remaining_str} | Chunk {completed_chunks}/{total_chunks}",
                          end="", flush=True)

                    # Force garbage collection after each chunk
                    gc.collect()

                except Exception as e:
                    print(f"\nError processing chunk: {e}")
                    print("Falling back to single-threaded calculation...")
                    return run_simple_method_optimized(ratio, digits, delay, block_size, live_preview)

    except Exception as e:
        print(f"\nParallel processing failed: {e}")
        print("Falling back to single-threaded calculation...")
        return run_simple_method_optimized(ratio, digits, delay, block_size, live_preview)

    # Tree sum for numerical stability
    print("\nSumming results...")
    S_total = tree_sum_optimized(chunk_results)

    pi_val = C / S_total
    print("\nCalculation finished.\n")
    print(str(pi_val)[:digits+2])
    total_time = time.time() - start_time
    print(f"\nTotal calculation time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")

def tree_sum_optimized(lst):
    """Optimized tree sum with memory management"""
    working_list = lst[:]  # Create a copy

    while len(working_list) > 1:
        new_lst = []
        for i in range(0, len(working_list), 2):
            if i + 1 < len(working_list):
                result = working_list[i] + working_list[i+1]
                new_lst.append(result)
                # Clear processed items
                working_list[i] = None
                working_list[i+1] = None
            else:
                new_lst.append(working_list[i])
                working_list[i] = None

        # Force garbage collection
        gc.collect()
        working_list = new_lst

    return working_list[0]

def choose_method():
    print("Choose calculation method:")
    print("1) Optimized Simple (Single-core with memory management)")
    print("2) Optimized Parallel Chunked (Multi-core with optimized chunking)")
    while True:
        choice = input("Enter method number (1/2): ").strip()
        if choice in ('1', '2'):
            return int(choice)
        print("Invalid choice, please enter 1 or 2.")

def main():
    # Get hardware information
    hardware_info = get_hardware_info()
    display_hardware_info(hardware_info)

    # Get desired digits first to make better recommendations
    digits = ask_user_for_digits(10**7)

    # Get optimal settings recommendation
    recommendations = recommend_optimal_settings(digits, hardware_info)

    print("=== Optimized Settings Recommendation ===")
    print(f"Recommended RAM usage: {recommendations['ram_ratio']*100:.1f}%")
    print(f"Recommended CPU cores: {recommendations['cores_to_use']}")
    print(f"Recommended method: {'Single-core' if recommendations['method'] == 1 else 'Multi-core'}")
    print(f"Optimal chunk size: {recommendations['chunk_size']}")
    print()

    # RAM ratio selection
    use_recommended = input("Use recommended settings? (y/n): ").strip().lower()
    if use_recommended == 'y':
        ratio = recommendations['ram_ratio']
        delay = 0.1
        block_size = 100
        method = recommendations['method']
        optimal_cores = recommendations['cores_to_use']
    else:
        default_ratio = recommendations['ram_ratio']
        print(f"Hardware-recommended RAM usage ratio: {default_ratio*100:.0f}%")
        choice = input("Change RAM usage ratio? (y/n): ").strip().lower()
        if choice == 'y':
            try:
                ratio = float(input("Enter RAM usage ratio (0.01 for 1%): ").strip())
                if ratio <= 0 or ratio > 1:
                    print("Invalid ratio, using recommended.")
                    ratio = default_ratio
            except:
                print("Invalid input, using recommended.")
                ratio = default_ratio
        else:
            ratio = default_ratio

        delay_input = input("Enter delay between updates in seconds (default 0.1): ").strip()
        try:
            delay = float(delay_input) if delay_input else 0.1
        except:
            delay = 0.1

        block_input = input("Enter number of digits per block (default 100): ").strip()
        try:
            block_size = int(block_input) if block_input else 100
            if block_size <= 0:
                print("Invalid block size, using default 100.")
                block_size = 100
        except:
            block_size = 100

        method = choose_method()
        optimal_cores = None

    live_preview_choice = input("Live preview? (y/n): ").strip().lower()
    live_preview = live_preview_choice == 'y'

    if method == 1:
        run_simple_method_optimized(ratio, digits, delay, block_size, live_preview)
    else:
        run_parallel_chunked_method_optimized(ratio, digits, delay, block_size, live_preview, optimal_cores)

if __name__ == "__main__":
    main()
