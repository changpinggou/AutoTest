import subprocess

class DockerController():

    def get_docker(self, tag_name):
        # 先执行拉取docker接口
        cmd = ["/bin/bash", "/root/pull_docker.sh", tag_name]
        subprocess.run(cmd)
        # 获取最近的容器id
        cmd = ['docker', 'ps', '-l', '-q']
        container_id = subprocess.check_output(cmd).decode('utf-8').strip('\n')
        # 根据容器id启动docker
        cmd = ['docker', 'start', container_id]
        result = subprocess.check_output(cmd).decode('utf-8').strip('\n')
        print('launch docker result: ' + result)
        # 根据上文容器id，获取其创建者名
        cmd = f"docker inspect --format='{{{{.Name}}}}' {container_id} | awk -F/ '{{print $2}}'"
        docker_server_name = subprocess.check_output(cmd, shell=True).decode('utf-8').strip('\n')
        return container_id, docker_server_name

    def del_docker(self, container_id):
        cmd = ['docker', 'ps', f'--filter=name={container_id}']
        result = subprocess.run(cmd)
        if result != '':
            #欲要删其像，必先停其器
            cmd = ['docker', 'stop', container_id]
            result = subprocess.check_output(cmd).decode('utf-8').strip('\n')
            print('container id stop: ' + result)
            #通过容器id获取镜像名
            cmd = ['docker', 'inspect', '--format', '"{{.Image}}"', container_id]
            image_id = subprocess.check_output(cmd).decode('utf-8').strip('\n').strip('"')
            #删除容器id
            cmd = ['docker', 'rm', '-f', container_id]
            subprocess.run(cmd)
            #删除镜像
            cmd = ['docker', 'rmi', '-f', image_id]
            result = subprocess.run(cmd)
