\# ChronosMatch: Zero-Copy High-Frequency Trading Engine



ChronosMatch is a Python-based trading-engine project demonstrating binary order representation, memory-mapped inter-process communication (IPC), and price-time-priority order matching.



\## Features



\- \*\*Binary order records:\*\* Fixed-size 21-byte order records implemented with Python's `struct` module.

\- \*\*Memory-mapped IPC:\*\* Transfers binary order records between separate Python processes using `mmap`.

\- \*\*Concurrent ring-buffer demonstration:\*\* Uses shared memory and synchronization to coordinate order producers and consumers.

\- \*\*Order matching:\*\* Matches compatible buy and sell orders, supporting partial fills and price-time priority.

\- \*\*Cython implementation:\*\* Provides a compiled matching-engine demonstration.

\- \*\*Asynchronous market feed:\*\* Connects generated orders to the matching engine.

\- \*\*Terminal dashboard:\*\* Displays the best bid, best ask, market spread, processed orders, and executed trades.



\## Requirements



\- Python 3.14 or a compatible Python version

\- Cython and setuptools for building the Cython extension

\- Microsoft C++ Build Tools on Windows for compiling the extension



\## Run the demonstrations



Run these commands from the repository root.



\### 1. Order-book demonstration



```powershell

python main.py

```



\### 2. Million-order IPC transfer



```powershell

python ipc\_ring\_demo.py

```



This demonstrates concurrent transfer of 1,000,000 binary order records and verifies the resulting checksum.



\### 3. IPC and order-book integration



```powershell

python ipc\_engine\_demo.py

```



This demonstrates IPC input followed by order matching and verification of the remaining order quantity.



\### 4. Cython matching engine



Build the extension from an x64 Native Tools Command Prompt for Visual Studio:



```powershell

python setup.py build\_ext --inplace

```



Then run:



```powershell

python test\_cython.py

```



\### 5. Market feed and matching engine



```powershell

python src/market\_engine\_demo.py

```



\### 6. Terminal dashboard



```powershell

python dashboard.py

```



The current dashboard uses sample orders to demonstrate best bid, best ask, spread, and trade information.



\### 7. Automated tests



```powershell

python -m pytest -v

```



\## Verification notes



The project demonstrations have separately verified million-order IPC transfer, order matching, Cython matching, asynchronous market-feed processing, and dashboard output.



The IPC transfer benchmark, market-feed benchmark, and matching-engine demonstrations measure different execution paths. Their results should not be treated as one combined end-to-end performance benchmark.



The terminal dashboard currently uses sample orders and is not connected to a live IPC stream.



\## Current development status



The project is under development. Further work can focus on integrating the dashboard with live engine data, improving IPC robustness, and evaluating performance across the complete processing pipeline.

