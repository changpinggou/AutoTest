#! /usr/bin/env python3
# _*_ coding:utf-8 _*_
"""
@Auth : Dora
@Date : 2023/8/8 10:46
"""
import yaml, os, sys
from ruamel.yaml import YAML

PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ_PARENT_ROOT = os.path.abspath(os.path.dirname(PROJ_ROOT))

parentdir = os.path.dirname(PROJ_ROOT)
sys.path.insert(0, parentdir)
# sys.path.insert(0,r'/home/aitest/dora/')

yaml = YAML()


# 读取配置文件
class ReadElemet:
    def __init__(self, fileName):
        # self.filePath = '/home/aitest/dora/conf/{}.yaml'.format(fileName)
        # self.filePath = '/home/aitest/dora/conf/data.yaml'
        self.filePath = os.path.join(PROJ_PARENT_ROOT, "conf", '{}.yaml'.format(fileName))

    def All_element(self):
        # 读取数据配置文件fileName的所有数据
        # 用例单独所需的参数使用此方法切片获取，如嘴唇是切片[1:6]

        if not os.path.exists(self.filePath):
            raise FileNotFoundError("%s 文件不存在！" % self.filePath)
        with open(self.filePath, encoding='utf-8') as f:
            # self.data = yaml.safe_load(f)
            # return yaml.load(f, Loader=yaml.FullLoader)
            return yaml.load(f)

    def get_item(self, item):
        # 读取参数
        return self.All_element()[item]

    def old_com_element(self, item):
        # 读取公共参数,item为元素的名字
        return self.All_element()[0][item]

    def update_yaml(self, k, v):
        data = self.All_element()
        # k若存在就修改对应值，若k不存在就新增一组键值对
        data[k] = v
        with open(self.filePath, 'w', encoding='utf-8') as f:
            # yaml.safe_dump(data,f)
            yaml.dump(data, f)


if __name__ == '__main__':

    p1 = ReadElemet('data')
    k = 'no_model'
    v = 'change_value2'
    k1 = 'new_key'
    v1 = 'new_value'
    # p1.update_yaml(k1,v1)
    t = p1.All_element()['custom_video_list_to_model']
    print(type(t))
    for x in t:
        print(type(x), x)