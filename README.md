# ISAAC

This is the development repository for ISAAC, an input-aware auto-tuning framework and code-generator for HPC/DL. This version is only compatible with NVIDIA hardware (it generates PTX source code). For OpenCL/CUDA compatibility, visit the Intel fork (https://github.com/intel/isaac) or the v1.0 branch (deprecated) or the

### License

ISAAC is distributed under the MIT/X11 license.

### Usage

In order to compile and use ISAAC, only a proprietary NVIDIA driver is necessary. No CUDA SDK is required (except for testing and benchmarking against cuBLAS/cuDNN)
```
git clone https://github.com/ptillet/isaac.git
cd isaac; mkdir build; cd build;
cmake ../ ; make -j8;
```

Basic benchmarks for GEMM and CONV for DeepBench can be obtained using the isaac-tools binary interface:
```
./examples/isaac-tools --gemm --bench --suite deepbench --dtype float32
./examples/isaac-tools --conv --bench --suite deepbench --dtype float32
```

Custom shapes, layouts and datatypes can also be provided:
```
./examples/isaac-tools --gemm --bench --shape 2563,95,7541 --layout NN --dtype float16
```

If you want, you can also dump the PTX source code generated by ISAAC for some shapes:
```
./examples/isaac-tools --gemm --dump --format ptx --shape 2048,2048,2048 --layout NT --dtype float32
```

If you really know what you're doing, you can also capture the tiling parameters found by ISAAC:
```
./examples/isaac-tools --gemm --dump --format params --shape 2048,2048,2048 --layout NT --dtype float32
```

You will get the following output:
```
Tuning parameters: 4, 16, 8, 8, 8, 8, 16, 8, 16, 8, 1, 1, 1
```

The parameters respectively mean:
(1) that shared memory loads have a width of **4** ; 
(2) each block comprises **16**x**8** threads ; 
(3) each threads computes a tile of **8**x**8** elements; 
(4) Each loop iteration processes **8** elements along the K axis ; 
(5) threads are rearranged  as a **16** x **8** block for loading A, and a **16** x **8** block for loading B; 
(6) the  reduction is split accross **1**, **1** and **1** independent batches within each thread, thread-block and grid, and the results are accumulated after the inner-loop


### Coverage

The GEMM code is production-ready. Kernel selection is done using a MLP which has about 100us overhead, and the kernel to use is cached after the first prediction. I wouldn't advise this library for applications that use 1000s of different shapes exactly once (e.g., Blocked SVD).

The CONV code passes the tests, but is hardly usable in practice because (1) beta is not handled, (2) it requires CHWN tensor layouts. I'm in the process of refactoring it in the better-conv branch :)
