import os
import sys
import tempfile
from git.repo import Repo

from zegopy.builder import zip_folder as zegozip
from zegopy.builder.artifactory import Artifactory
from zegopy.common import io
from zegopy.common import log

class JitpackUploader():
    def __init__(self, uploader_username: str, gradle_library_name: str, release_tag: str) -> None:
        self.uploader_username = uploader_username
        self.gradle_library_name = gradle_library_name

        self.release_tag = release_tag

        self.github_ssh_address = 'git@github.com:{username}/{project}.git'.format(
            username=self.uploader_username, project=self.gradle_library_name)


    def setup_sdk_param(self, sdk_download_url: str, sdk_zip_root_folder: str):
        self.sdk_download_url_by_pass = sdk_download_url
        self.sdk_zip_root_folder_by_pass = sdk_zip_root_folder


    def upload(self):
        dest_tmp_folder = tempfile.mkdtemp()

        print('current tmp folder: {}'.format(dest_tmp_folder))
        #sdk_zip_name = self._download_sdk(dest_zip_folder=dest_tmp_folder)

        #sdk_local_path = os.path.join(dest_tmp_folder, 'sdk')
        #self._unzip_file(os.path.join(dest_tmp_folder, sdk_zip_name), sdk_local_path)

        git_local_path = os.path.join(dest_tmp_folder, 'github')
        repo = Repo.clone_from(self.github_ssh_address, to_path=git_local_path, branch='main')
        repo.config_writer().set_value("user", "name", self.uploader_username).release()
        repo.config_writer().set_value("user", "email", "developer@zego.im").release()

        #sdk_product_root_folder = ''
        #for folder in os.listdir(sdk_local_path):
        #    if os.path.isdir(os.path.join(sdk_local_path, folder)):
        #        sdk_product_root_folder = os.path.join(sdk_local_path, folder)
        #        break

        #if len(sdk_product_root_folder) == 0:
        #    raise Exception("Can not find sdk product")

        #jar_src_path = os.path.join(sdk_product_root_folder, '{}.jar'.format(self.product_name))
        #jar_dst_path = os.path.join(git_local_path, '{}'.format(self.gradle_library_name), 'libs')
        #io.copy(src=jar_src_path, dst=jar_dst_path)
        #log.i("Copy JAR : {} -> {}".format(jar_src_path, jar_dst_path))

        #for so_folder in os.listdir(sdk_product_root_folder):
        #    if so_folder in self.support_abi:
        #        so_src_path = os.path.join(sdk_product_root_folder, so_folder)
        #        so_dst_path = os.path.join(git_local_path, 'src', 'main', 'jniLibs', so_folder)
        #        io.copy_folder(src=so_src_path, dst_folder=so_dst_path, overwrite=True)
        #        log.i("Copy SO : {} -> {}".format(so_src_path, so_dst_path))


        self._update_gradle_info(os.path.join(git_local_path, '{}'.format(self.gradle_library_name), 'build.gradle'))

        log.i(repo.git.add('.'))
        log.i(repo.git.commit(m='Update {}'.format(self.release_tag)))
        tag = repo.create_tag('{}'.format(self.release_tag))
        log.i(repo.git.push())
        log.i(repo.remotes.origin.push(tag))


    def _update_gradle_info(self, module_build_gradle_path: str):

        with open(module_build_gradle_path, 'r', encoding='UTF-8') as gradle_reader:
            lines = gradle_reader.readlines()

        with open(module_build_gradle_path, 'w', encoding='UTF-8') as gradle_writer:
            for line in lines:
                if 'commandLine \"python\"' in line:
                    line = '        commandLine \"python\", \"download_native_sdk.py\", \"--sdk_download_url\", \"{}\", \"--sdk_zip_root_folder\", \"{}\"\n'.format(self.sdk_download_url_by_pass, self.sdk_zip_root_folder_by_pass)
                gradle_writer.write(line)


if __name__ == "__main__":
    import argparse

    parse = argparse.ArgumentParser()
    parse.add_argument("--uploader_username", action='store', type=str, help="Specify github username")
    parse.add_argument("--gradle_library_name", action='store', type=str, help="Specify gradle library name for Jitpack")
    parse.add_argument("--sdk_download_url", action='store', type=str, help="Specify SDK download URL from coding")
    parse.add_argument("--sdk_zip_root_folder", action='store', default='', type=str)
    parse.add_argument("--release_tag", action='store', type=str)

    arguments = parse.parse_args()

    uploader = JitpackUploader(arguments.uploader_username, arguments.gradle_library_name, arguments.release_tag)
    uploader.setup_sdk_param(arguments.sdk_download_url, arguments.sdk_zip_root_folder)
    uploader.upload()
