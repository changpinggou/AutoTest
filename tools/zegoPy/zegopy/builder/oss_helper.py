# coding=UTF-8
import os
import argparse

try: import oss2
except:
    os.system('pip3 install oss2')
    os.system('pip install oss2')
    import oss2

class OssHelper:
    def __init__(self):
        self._endpoint = 'https://storage.zego.im'
        self._bucket_name = 'zego-public'
        self._access_key_id = ''
        self._access_key_secret = ''

    def set_auth(self, access_key_id: str, access_key_secret: str):
        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret
        self._auth = oss2.Auth(access_key_id, access_key_secret)

    def set_bucket(self, bucket_name: str):
        # 我们使用了自定义域名，设置is_cname=True来开启CNAME。CNAME是指将自定义域名绑定到存储空间。
        self._bucket_name = bucket_name
        self._bucket = oss2.Bucket(self._auth, self._endpoint, bucket_name, is_cname=True)

    def upload_fie(self, local_path: str, target_path: str):
        """
        上传一个文件到oss
        :param local_path 待上传文件的本地路径
        :param target_path 相对于bucket的相对路径，比如 github/goclass/android/README.md
        """
        print("Uploading local file[{}] into oss [{}]...".format(local_path, target_path))
        self._bucket.put_object_from_file(target_path, local_path)
        return '/'.join([self._endpoint, target_path])

    def duplicate_file(self, src_path: str, target_path: str):
        """
        OSS 内部文件复制
        :param src_path OSS 源文件相对于 bucket 的相对路径，比如 zim/zim-ios-objc-1.3.0.zip
        :param target_path 相对于bucket的相对路径，比如 zim/zim-ios-objc.zip
        """
        print("Duplicaing OSS source file [{}] to [{}] ...".format(src_path, target_path))
        self._bucket.copy_object(self._bucket_name, src_path, target_path)
        return '/'.join([self._endpoint, target_path])

    def resumable_upload_file(self, local_path: str, target_path: str):
        """
        断点续传一个文件到oss，部分较大文件使用`upload_fie`可能会返回413，可使用这个方法进行断点续传
        :param local_path 待上传文件的本地路径
        :param target_path 相对于bucket的相对路径，比如 github/goclass/android/README.md
        """
        print("Resumable uploading local file[{}] into oss [{}]...".format(local_path, target_path))
        oss2.resumable_upload(self._bucket, target_path, local_path)
        return '/'.join([self._endpoint, target_path])

    def upload_dir(self, local_dir: str, target_dir: str):
        all_files = self._get_list_of_files(local_dir, local_dir)
        for file_name in all_files:
            self.upload_fie(os.path.join(local_dir, file_name),
                            os.path.join(target_dir, os.path.basename(local_dir), file_name))
        return '/'.join([self._endpoint, target_dir, local_dir])

    def _get_list_of_files(self, dir_name: str, rel_start: str = ''):
        # create a list of file and sub directories
        # names in the given directory
        list_of_file = os.listdir(dir_name)
        all_files = list()
        # Iterate over all the entries
        for entry in list_of_file:
            # Create full path
            full_path = os.path.join(dir_name, entry)
            # If entry is a directory then get the list of files in this directory
            if os.path.isdir(full_path):
                all_files = all_files + self._get_list_of_files(full_path, rel_start)
            else:
                # for Windows
                relpath = os.path.relpath(full_path, rel_start).replace('\\', '/')
                all_files.append(relpath)

        return all_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='OSS helper')
    parser.add_argument('-l', '--local', dest='local', help='本地文件')
    parser.add_argument('-t', '--target', dest='target', help='目标文件')
    args = parser.parse_args()

    helper = OssHelper()
    helper.set_auth('', '')
    helper.set_bucket('zego-public')
    helper.upload_dir(args.local, args.target)
