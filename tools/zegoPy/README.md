# pyscripts

ZEGO python scripts for native developers

## 安装或更新

- 纯用户

    1. 假设你没有 clone 此仓库，仅需要使用 zegopy 脚本库
    2. 安装或升级都只需执行 `python3 -m pip install -i http://dev-pypi.pkg.coding.zego.cloud/common_utils/zegopy/simple zegopy --trusted-host dev-pypi.pkg.coding.zego.cloud --upgrade`

- 此仓库的维护者

    1. 假设你已经将此仓库 clone 到了本地的 `~/code/pyscripts`，然后 `cd ~/code/pyscripts`
    2. `python3 setup.py install` 安装到本地 python3 的 site-packages 目录
    3. 改动文件后建议修改 `./package.json` 文件中的 `version` 字段，以表示此脚本库有更新
    4. 当你修改了仓库内的脚本后需要再调用 `python3 setup.py install` 更新一下本地的 site-packages

    > 发布 pypi 的 Jenkins [任务链接](http://ci.zego.cloud/job/common_utils/job/zegopy)
    >
    > 注意：主干分支已禁止直接 Push，请拉分支提交推送后，在 Coding 发起 Merge Request 并找管理员进行 Code Review 以合入主干。
    > [Coding 远程仓库链接](http://dev.coding.zego.cloud/p/common_utils/d/pyscripts/git)

## 使用

在 python 脚本中引用此模块的方式：

```py
import zegopy

# OR import anything you need

from zegopy.builder import Polly
from zegopy.common import version_generator
from zegopy.builder.zego_artifactory import ZegoArtifactory
```
