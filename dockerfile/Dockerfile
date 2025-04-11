FROM nvidia/cudagl:11.1-devel-ubuntu20.04
ENV USER=user

RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub

# Install dependencies
# https://github.com/nytimes/rd-blender-docker/blob/master/dist/3.3.1-gpu-ubuntu18.04/Dockerfile
RUN apt-get update && apt-get install -y \
	wget \
	libopenexr-dev \
	bzip2 \
	build-essential \
	zlib1g-dev \
	libxmu-dev \
	libxi-dev \
	libxxf86vm-dev \
	libfontconfig1 \
	libxrender1 \
	libgl1-mesa-glx \
	xz-utils \
        libxkbcommon0 \
    python3-dev python3-pip git \
    libjpeg-dev libfreeimage-dev


RUN python3 -m pip install git+https://github.com/hiroaki-santo/BlenderProc.git@v1.2
RUN blenderproc quickstart ; exit 0 # fails due to missing CUDA env

RUN blenderproc pip install tqdm
