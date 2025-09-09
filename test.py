import dlib
print("DLIB_USE_CUDA:", dlib.DLIB_USE_CUDA)
print("CUDA devices:", dlib.cuda.get_num_devices() if dlib.DLIB_USE_CUDA else "No CUDA")