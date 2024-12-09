docker_image_name="cuda_12.1:v1.0"
docker_container_name="triton"
WORKSPACE=$(pwd)
# Docker 실행
docker run -it \
  --name ${docker_container_name} \
  -v ${HOME}:${HOME} \
  -v ${WORKSPACE}:${WORKSPACE} \
  -w ${WORKSPACE} \
  --gpus all \
  --shm-size=128g \
  --ipc=host \
  --hostname ${docker_container_name} \
  ${docker_image_name}