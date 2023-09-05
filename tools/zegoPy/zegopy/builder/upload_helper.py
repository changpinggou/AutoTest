#!/usr/bin/env python -u
# coding: utf-8

"""
Warning: Deprecated 此模块偶合太紧，推荐使用 archive_helper & ftp_uploader 组合用于上传编译结果

上传编译结果至 share 服务器
"""

import os
from zegopy.builder import zego_upload

from zegopy.common import io as zegoio
from zegopy.common import mount
from zegopy.common import ziputil


# 推荐使用 archive_helper & ftp_uploader 替代
def upload_android_to_share_server(dst_path, framework, date_version, share_folder, build_type='normal',
                                   upload_file_list=[]):
    print("<< zip dst_path: {0}\n build_type:{1}".format(dst_path, build_type))

    mount_folders = {"normal":"android", "cplus":"android_cplus", "c_interface":"android_c", "cpp_static":"android_cpp_static"}
    # compress symbol
    if "cpp_static" != build_type:
        zip_symbol_name = 'symbol_{}.zip'.format(date_version)
        product_symbol_folder = os.path.realpath(os.path.join(dst_path, 'symbols'))
        print("<< zip symbol {0} to {1}".format(product_symbol_folder, zip_symbol_name))
        success = ziputil.zip_folder(product_symbol_folder, dst_path, zip_symbol_name)
        if not success:
            raise Exception('<<zip symbol failed!')

        zip_symbol_file = os.path.realpath(os.path.join(dst_path, zip_symbol_name))
        upload_file_list.append(zip_symbol_file)    # add symbol file to upload list

    src_file_list = []
    libs_folder = os.path.relpath(os.path.join(dst_path, 'libs'))
    date_version_with_platform = '{0}_{1}'.format(date_version, mount_folders[build_type])
    mount_folder = os.path.join(date_version, mount_folders[build_type])

    if 'normal' == build_type:
        # compress libs
        for item in os.listdir(libs_folder):
            if item.startswith("."):
                continue
            src_file_list.append(os.path.relpath(os.path.join(libs_folder, item)))

        # compress doc
        zip_doc_name = 'doc_{}.zip'.format(date_version_with_platform)
        product_doc_folder = os.path.realpath(os.path.join(dst_path, 'doc'))
        print("<< zip doc {0} to {1}".format(product_doc_folder, zip_doc_name))
        success = ziputil.zip_folder(product_doc_folder, dst_path, zip_doc_name)
        if not success:
            raise Exception('<<zip doc failed!')
            # print ("[***] zip doc failed")

        zip_doc_file = os.path.realpath(os.path.join(dst_path, zip_doc_name))
        upload_file_list.append(zip_doc_file)   # add doc file to upload list

        
    elif build_type in ["cplus", "c_interface", "cpp_static"]:
        for item in os.listdir(libs_folder):
            if item.startswith("."):
                zegoio.delete(os.path.join(libs_folder, item))
        src_file_list.append(libs_folder)

        include_folder = os.path.relpath(os.path.join(dst_path, 'include'))
        src_file_list.append(include_folder)
    else:
        raise Exception('Unsupport build_type: ' + build_type)

    zip_libs_name = '{}.zip'.format(date_version_with_platform)
    print("<< zip release {0} to {1}".format(src_file_list, zip_libs_name))
    success = ziputil.zip_folder_list(src_file_list, dst_path, zip_libs_name)
    if not success:
        raise Exception('<<zip folder failed!')

    zip_libs_file = os.path.realpath(os.path.join(dst_path, zip_libs_name))
    upload_file_list.append(zip_libs_file)  # add libs zip file to upload list

    print("<<Upload to share")
    mount_path = os.path.realpath(os.path.join(os.path.expanduser("~"), "smb_temp"))
    zego_upload.upload(share_folder, mount_path, mount_folder, upload_file_list)
    print("<< download url: {}".format(os.path.join(zego_upload.get_default_share_path(), share_folder, mount_folder)))

    print("<< remove tmp zip file")
    for fname in upload_file_list:
        zegoio.delete(fname)

    return {"dynamic": '{}/{}/{}/{}'.format(zego_upload.get_default_share_path(),
                                            share_folder, mount_folder, zip_libs_name)}


def upload_android_lib_to_share_server(dst_path, framework, date_version, share_folder):
    print ("<< zip")
    
    zip_file_list = []
    zip_file_path = os.path.relpath(os.path.join(dst_path, '..', 'release'))
    zip_name = '{0}-android.zip'.format(date_version)
    print ("<< zip {0} to {1}".format(dst_path, zip_name))
    success = ziputil.zip_folder(dst_path, zip_file_path, zip_name)
    if not success:
        raise Exception('<<zip failed!')
        
    zip_file = os.path.realpath(os.path.join(zip_file_path, zip_name))
    zip_file_list.append(zip_file)

    print ("<<Upload to share")
    mount_path = os.path.realpath(os.path.join(os.path.expanduser('~'), "smb_temp"))
    zego_upload.upload(share_folder, mount_path, date_version, zip_file_list)

    print ("<< remove zip file")
    for zip_file in zip_file_list:
        zegoio.delete(zip_file)
        
    print ("<< upload done!")

    return zip_name


# 推荐使用 archive_helper & ftp_uploader 替代
def upload_ios_to_share_server(dst_path, framework, date_version, share_folder, build_type_set, zip_file_list = []):
    print ("<< zip")

    date_version_with_platform = '{}_ios'.format(date_version)

    _build_type_set = [bt.lower() for bt in build_type_set]
    zip_file_path = dst_path

    output_zip_file_list = {}
    total_share_path = '{}/{}/{}/iOS'.format(zego_upload.get_default_share_path(), share_folder, date_version)

    # release
    build_config = "Release"
    if 'dynamic' in _build_type_set:
        product_folder = os.path.relpath(os.path.join(dst_path, build_config))
        zip_name = '{0}.zip'.format(date_version_with_platform)
        print ("<< zip release {0} to {1}".format(product_folder, zip_name))
        success = ziputil.zip_folder(product_folder, zip_file_path, zip_name)
        if not success:
            raise Exception('<<zip folder failed!')

        zip_file = os.path.realpath(os.path.join(zip_file_path, zip_name))
        zip_file_list.append(zip_file)
        output_zip_file_list["dynamic"] = '{}/{}'.format(total_share_path, zip_name)

        # symbol
        zip_symbol_name = 'symbol_{}.zip'.format(framework)
        product_symbol_folder = os.path.realpath(os.path.join(dst_path, 'symbol', build_config, 'iPhoneos'))
        print ("<< zip symbol {0} to {1}".format(product_symbol_folder, zip_symbol_name))
        success = ziputil.zip_folder(product_symbol_folder, dst_path, zip_symbol_name)
        if not success:
            raise Exception('<<zip symbol failed!')

        zip_symbol_file = os.path.realpath(os.path.join(dst_path, zip_symbol_name))
        zip_file_list.append(zip_symbol_file)

        # compress doc
        zip_doc_name = 'doc_{}.zip'.format(date_version_with_platform)
        product_doc_folder = os.path.realpath(os.path.join(dst_path, 'doc'))
        print ("<< zip doc {0} to {1}".format(product_doc_folder, zip_doc_name))
        success = ziputil.zip_folder(product_doc_folder, dst_path, zip_doc_name)
        if not success:
            print ('<<zip doc failed!')
        else:
            zip_doc_file = os.path.realpath(os.path.join(dst_path, zip_doc_name))
            zip_file_list.append(zip_doc_file)   

    # static
    if 'static' in _build_type_set:
        zip_static_name = '{0}_static.zip'.format(date_version_with_platform)
        product_static_folder = os.path.realpath(os.path.join(dst_path, 'Static'))
        print ("<< zip static {0} to {1}".format(product_static_folder, zip_static_name))
        success = ziputil.zip_folder(product_static_folder, dst_path, zip_static_name)
        if not success:
            raise Exception('<<zip static failed!')

        zip_static_file = os.path.realpath(os.path.join(dst_path, zip_static_name))
        zip_file_list.append(zip_static_file)
        output_zip_file_list["static"] = '{}/{}'.format(total_share_path, zip_static_name)

    # static_no_ffmpeg
    if 'no_ffmpeg' in _build_type_set:
        zip_static_noffmpeg_name = '{0}_noffmpeg_static.zip'.format(date_version_with_platform)
        product_static_folder = os.path.realpath(os.path.join(dst_path, 'noffmpeg'))
        print ("<< zip static noffmpeg {0} to {1}".format(product_static_folder, zip_static_noffmpeg_name))
        success = ziputil.zip_folder(product_static_folder, dst_path, zip_static_noffmpeg_name)
        if not success:
            raise Exception('<<zip static noffmpeg failed!')

        zip_static_noffmpeg_file = os.path.realpath(os.path.join(dst_path, zip_static_noffmpeg_name))
        zip_file_list.append(zip_static_noffmpeg_file)
        output_zip_file_list["no_ffmpeng"] = '{}/{}'.format(total_share_path, zip_static_noffmpeg_name)

    if 'plus' in _build_type_set:
        zip_plus_name = '{}_plus.zip'.format(date_version_with_platform)
        product_plus_folder = os.path.realpath(os.path.join(dst_path, 'Plus'))
        print ("<< zip plus {0} to {1}".format(product_plus_folder, zip_plus_name))
        success = ziputil.zip_folder(product_plus_folder, dst_path, zip_plus_name)
        if not success:
            raise Exception("<<zip plus failed!")

        zip_plus_file = os.path.realpath(os.path.join(dst_path, zip_plus_name))
        zip_file_list.append(zip_plus_file)
        output_zip_file_list["plus"] = '{}/{}'.format(total_share_path, zip_plus_name)

        # symbol_plus
        zip_symbol_plus_name = 'symbol_plus-{}.zip'.format(framework)
        product_symbol_plus_folder = os.path.realpath(os.path.join(dst_path, 'symbol_plus', build_config, 'iPhoneos'))
        print ("<< zip symbol {0} to {1}".format(product_symbol_plus_folder, zip_symbol_plus_name))
        success = ziputil.zip_folder(product_symbol_plus_folder, dst_path, zip_symbol_plus_name)
        if not success:
            raise Exception('<<zip symbol plus failed!')

        zip_symbol_plus_file = os.path.realpath(os.path.join(dst_path, zip_symbol_plus_name))
        zip_file_list.append(zip_symbol_plus_file)
    
    if 'c_interface' in _build_type_set:
        zip_c_name = '{}_c.zip'.format(date_version_with_platform)
        product_c_folder = os.path.realpath(os.path.join(dst_path, 'CAPI'))
        print ("<< zip c {0} to {1}".format(product_c_folder, zip_c_name))
        success = ziputil.zip_folder(product_c_folder, dst_path, zip_c_name)
        if not success:
            raise Exception("<<zip c failed!")

        zip_c_file = os.path.realpath(os.path.join(dst_path, zip_c_name))
        zip_file_list.append(zip_c_file)
        output_zip_file_list["c"] = '{}/{}'.format(total_share_path, zip_c_name)

        # symbol_c
        zip_symbol_c_name = 'symbol_c-{}.zip'.format(framework)
        product_symbol_c_folder = os.path.realpath(os.path.join(dst_path, 'symbol_c', build_config, 'iPhoneos'))
        print ("<< zip symbol {0} to {1}".format(product_symbol_c_folder, zip_symbol_c_name))
        success = ziputil.zip_folder(product_symbol_c_folder, dst_path, zip_symbol_c_name)
        if not success:
            raise Exception('<<zip symbol c failed!')

        zip_symbol_c_file = os.path.realpath(os.path.join(dst_path, zip_symbol_c_name))
        zip_file_list.append(zip_symbol_c_file)

    if "plus_static" in _build_type_set:
        zip_name = "{}_cpp_static.zip".format(date_version_with_platform)
        product_folder = os.path.realpath(os.path.join(dst_path, "Plus_Static"))
        print("<< zip plus static {} to {}".format(product_folder, zip_name))
        success = ziputil.zip_folder(product_folder, dst_path, zip_name)
        if not success:
            raise Exception("zip plus static failed!")

        zip_file = os.path.realpath(os.path.join(dst_path, zip_name))
        zip_file_list.append(zip_file)
        output_zip_file_list["plus_static"] = '{}/{}'.format(total_share_path, zip_name)

    print ("<<Upload to share")
    mount_path = os.path.realpath(os.path.join(os.path.expanduser('~'), "smb_temp"))

    mount_folder = os.path.join(date_version, 'iOS')
    zego_upload.upload(share_folder, mount_path, mount_folder, zip_file_list)

    print ("<< remove zip file")
    for zip_file in zip_file_list:
        zegoio.delete(zip_file)

    print ("<< upload done!")
    return output_zip_file_list


def upload_ios_lib_to_share_server(dst_path, framework, date_version, share_folder):
    print ("<< zip")
    
    zip_file_list = []
    zip_file_path = os.path.relpath(os.path.join(dst_path, '..', 'release'))
    zip_name = '{0}-ios.zip'.format(date_version)
    print ("<< zip {0} to {1}".format(dst_path, zip_name))
    success = ziputil.zip_folder(dst_path, zip_file_path, zip_name)
    if not success:
        raise Exception('<<zip failed!')
        
    zip_file = os.path.realpath(os.path.join(zip_file_path, zip_name))
    zip_file_list.append(zip_file)

    print ("<<Upload to share")
    mount_path = os.path.realpath(os.path.join(os.path.expanduser('~'), "smb_temp"))
    zego_upload.upload(share_folder, mount_path, date_version, zip_file_list)

    print ("<< remove zip file")
    for zip_file in zip_file_list:
        zegoio.delete(zip_file)
        
    print ("<< upload done!")

    return zip_name


def upload_mac_to_share_server(dst_path, framework, date_version, share_folder, build_type_set, zip_file_list = []):
    def zip_folder(source_folder, dest_folder, zip_name, exclude_file_names=None):
        """DO NOT use zip_folder from zegopy, for symbolic link in mac framework"""

        def _is_exclude_file(fname):
            if exclude_file_names is None or len(exclude_file_names) == 0:
                return False

            for exclude_name in exclude_file_names:
                if fname.endswith(exclude_name):
                    return True
            return False

        if not os.path.exists(source_folder):
            print(">> source folder do not exist!")
            return False

        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)

        from zegopy.common import command as zegocmd
        zegocmd.execute('zip -r -y {} {}'.format(zip_name, source_folder))
        import shutil
        shutil.move(zip_name, dest_folder)

        return True
        
    _build_type_set = [bt.lower() for bt in build_type_set]
    zip_file_path = dst_path

    target_config_set = {
        'dynamic': {
            'product_folder': 'Release',
            'product_symbol_folder': 'symbol'
        },
        'plus': {
            'product_folder': 'Plus',
            'product_symbol_folder': 'symbol_plus'
        },
        'static': {
            'product_folder': 'Static'
        },
        'plus_static': {
            'product_folder': 'Plus_Static'
        },
        'c_interface': {
            'product_folder': 'C_API'
        }
    }

    output_zip_file_list = {}
    total_share_path = '{}/{}/{}/Mac'.format(zego_upload.get_default_share_path(), share_folder, date_version)
    
    for build_type in _build_type_set:
        if build_type in target_config_set:
            config = target_config_set[build_type]

            product_folder = os.path.relpath(os.path.join(dst_path, config['product_folder']))
            zip_name = '{}-mac-{}-{}.zip'.format(framework, date_version, config['product_folder'])
            print("<< zip release {0} to {1}".format(product_folder, zip_name))
            success = zip_folder(product_folder, zip_file_path, zip_name)
            if not success:
                raise Exception('<< zip {} failed!'.format(product_folder))

            zip_file = os.path.realpath(os.path.join(zip_file_path, zip_name))
            zip_file_list.append(zip_file)
            output_zip_file_list[build_type] = '{}/{}'.format(total_share_path, zip_name)

            # compress doc
            zip_doc_name = 'doc-mac-{}.zip'.format(date_version)
            product_doc_folder = os.path.realpath(os.path.join(dst_path, 'doc'))
            print ("<< zip doc {0} to {1}".format(product_doc_folder, zip_doc_name))
            success = ziputil.zip_folder(product_doc_folder, dst_path, zip_doc_name)
            if not success:
                print ('<<zip doc failed!')
            else:
                zip_doc_file = os.path.realpath(os.path.join(dst_path, zip_doc_name))
                zip_file_list.append(zip_doc_file) 

            # symbol
            if 'product_symbol_folder' not in config: 
                continue

            zip_symbol_name = '{}-mac-{}-{}.zip'.format(framework, date_version, config['product_symbol_folder'])
            product_symbol_folder = os.path.relpath(os.path.join(dst_path, config['product_symbol_folder']))
            print("<< zip symbol {0} to {1}".format(product_symbol_folder, zip_symbol_name))
            success = zip_folder(product_symbol_folder, dst_path, zip_symbol_name)
            if not success:
                raise Exception('<< zip symbol failed!')

            zip_symbol_file = os.path.realpath(os.path.join(dst_path, zip_symbol_name))
            zip_file_list.append(zip_symbol_file)

        else:
            print('[*] skip {}'.format(build_type))

    print ("<<Upload to share")
    mount_path = os.path.realpath(os.path.join(os.path.expanduser('~'), "smb_temp"))

    mount_folder = os.path.join(date_version, 'Mac')
    zego_upload.upload(share_folder, mount_path, mount_folder, zip_file_list)

    for zip_file in zip_file_list:
        print ("<< remove zip file {}".format(zip_file))
        zegoio.delete(zip_file)

    print ("<< upload done!")
    return output_zip_file_list


def upload_mac_lib_to_share_server(dst_path, framework, date_version, share_folder):
    print ("<< zip")
    
    zip_file_list = []
    zip_file_path = os.path.relpath(os.path.join(dst_path, '..', 'release'))
    zip_name = '{0}-mac.zip'.format(date_version)
    print ("<< zip {0} to {1}".format(dst_path, zip_name))
    success = ziputil.zip_folder(dst_path, zip_file_path, zip_name)
    if not success:
        raise Exception('<<zip failed!')
        
    zip_file = os.path.realpath(os.path.join(zip_file_path, zip_name))
    zip_file_list.append(zip_file)

    print ("<<Upload to share")
    mount_path = os.path.realpath(os.path.join(os.path.expanduser('~'), "smb_temp"))
    zego_upload.upload(share_folder, mount_path, date_version, zip_file_list)

    print ("<< remove zip file")
    for zip_file in zip_file_list:
        zegoio.delete(zip_file)
        
    print ("<< upload done!")
    return zip_name


def upload_windows_cs_to_share_server(src_path, framework, share_folder, date_version_str, upload_file_list=[]):
    """
    zip /include
        /libs
            /x86
                /Release
            /x64
                /Release
    """
    print ('<< Going to upload products to share')
    zip_file_path = src_path

    zip_name = '{0}_cs.zip'.format(date_version_str)

    print ('<< zip file to {0}'.format(zip_name))
    zip_include_folder = os.path.realpath(os.path.join(src_path, 'include'))
    zip_libs_folder = os.path.realpath(os.path.join(src_path, 'libs'))
    success = ziputil.zip_folder_list([zip_include_folder, zip_libs_folder], zip_file_path, zip_name)
    if not success:
        raise Exception("zip libs failed")

    zip_file = os.path.realpath(os.path.join(zip_file_path, zip_name))

    zip_pdb_name = "symbol_{}_cs.zip".format(framework)

    print ("<< zip pdb to {}".format(zip_pdb_name))
    pdb_folder = os.path.realpath(os.path.join(src_path, 'symbol'))
    success = ziputil.zip_folder(pdb_folder, zip_file_path, zip_pdb_name)
    if not success:
        raise Exception("zip symbol failed")

    zip_pdb_file = os.path.realpath(os.path.join(zip_file_path, zip_pdb_name))

    zip_doc_name = "doc_{}_cs.zip".format(framework)

    print ("<< zip doc to {}".format(zip_doc_name))
    doc_folder = os.path.realpath(os.path.join(src_path, 'doc'))
    success = ziputil.zip_folder(doc_folder, zip_file_path, zip_doc_name)
    if not success:
        print ("zip doc failed")
    else:
        zip_doc_file = os.path.realpath(os.path.join(zip_file_path, zip_doc_name))
        upload_file_list.append(zip_doc_file)

    print ("<< upload to share")
    mount_folder = os.path.join(date_version_str, "windows_cs")

    upload_file_list.append(zip_file)
    upload_file_list.append(zip_pdb_file)
    
    zego_upload.upload_win32(share_folder, mount_folder, upload_file_list)

    zegoio.delete(zip_file)
    zegoio.delete(zip_pdb_file)

    print ('<< upload done!')

    return {"dynamic": '{}/{}/{}/windows_cs/{}'.format(zego_upload.get_default_share_path(), share_folder.replace('\\', '/'), date_version_str, zip_name)}


def upload_windows_to_share_server(src_path, framework, build_type_set, share_folder, date_version_str, upload_file_list=[]):
    """
    zip /include
        /libs
            /x86
            /x64
    """
    print('<< Going to upload products to share')
    zip_file_path = src_path

    tmp_zipfile_list = []
    upload_result = {}
    for build_type in build_type_set:
        zip_name = '{0}_{1}.zip'.format(date_version_str, build_type)
        src_root_for_type = os.path.realpath(os.path.join(src_path, build_type))

        zip_include_folder = os.path.join(src_root_for_type, 'include')
        zip_libs_folder = os.path.join(src_root_for_type, 'libs')
        print('<< zip file to {0}'.format(zip_name))
        success = ziputil.zip_folder_list([zip_include_folder, zip_libs_folder], zip_file_path, zip_name)
        if success:
            tmp_zipfile_list.append(os.path.join(zip_file_path, zip_name))
            upload_result[build_type] = '{}/{}/{}/windows/{}'.format(zego_upload.get_default_share_path(),
                                                     share_folder.replace('\\', '/'), date_version_str, zip_name)
        else:
            raise Exception("zip libs failed")

        pdb_folder = os.path.realpath(os.path.join(src_root_for_type, 'symbol'))
        if os.path.exists(pdb_folder):
            zip_pdb_name = "symbol_{}_{}.zip".format(framework, build_type)
            print("<< zip pdb to {}".format(zip_pdb_name))
            success = ziputil.zip_folder(pdb_folder, zip_file_path, zip_pdb_name)
            if success:
                tmp_zipfile_list.append(os.path.join(zip_file_path, zip_pdb_name))
            else:
                raise Exception("zip symbol failed")

        doc_folder = os.path.realpath(os.path.join(src_root_for_type, 'doc'))
        if os.path.exists(doc_folder):
            zip_doc_name = "doc_{}.zip".format(framework)
            print("<< zip doc to {}".format(zip_doc_name))
            success = ziputil.zip_folder(doc_folder, zip_file_path, zip_doc_name)
            if success:
                tmp_zipfile_list.append(os.path.join(zip_file_path, zip_doc_name))
            else:
                print("zip doc failed")

    print("<< upload to share")
    mount_folder = os.path.join(date_version_str, "windows")
    upload_file_list.extend(tmp_zipfile_list)
    zego_upload.upload_win32(share_folder, mount_folder, upload_file_list)

    for _file in tmp_zipfile_list:
        zegoio.delete(_file)

    print('<< upload done!')

    return upload_result


def upload_windows_lib_to_share_server(dst_path, framework, date_version, share_folder):
    print ("<< zip")
    
    zip_file_list = []
    zip_file_path = os.path.relpath(os.path.join(dst_path, '..', 'release'))
    zip_name = '{0}-windows.zip'.format(date_version)
    print ("<< zip {0} to {1}".format(dst_path, zip_name))
    success = ziputil.zip_folder(dst_path, zip_file_path, zip_name)
    if not success:
        raise Exception('<<zip failed!')
        
    zip_file = os.path.realpath(os.path.join(zip_file_path, zip_name))
    zip_file_list.append(zip_file)

    print ("<< upload to share")
    mount_path = date_version + "_win"
    zego_upload.upload_win32(share_folder, mount_path, [zip_file])

    print ("<< remove zip file")
    for zip_file in zip_file_list:
        zegoio.delete(zip_file)
        
    print ("<< upload done!")

    return zip_name


def upload_linux_lib_to_share_server(dst_path, framework, date_version, share_folder):
    return upload_embedded_linux_lib_to_share_server(dst_path, "linux", date_version, share_folder)


def upload_linux_to_share_server(product_path, platform, product, date_version, share_folder, upload_file_list=[]):
    print ("<< zip")
    zip_file_name = "{}_for_{}_{}.zip".format(date_version, platform, product)
    print ("<< zip product to {}".format(zip_file_name))
    so_path = os.path.join(product_path, "libs")
    header_path = os.path.join(product_path, "include")

    _ready_file_list = (so_path, header_path)
    success = ziputil.zip_folder_list(_ready_file_list, product_path, zip_file_name)
    if not success:
        raise Exception("<< zip failed!")

    print ("<< upload to share")
    zip_file = os.path.realpath(os.path.join(product_path, zip_file_name))
    # new_date_version = "{}_{}".format(date_version, platform)
    dst_path = os.path.join(share_folder, platform, product, date_version)

    symbols_local_path = os.path.join(product_path, "symbols")
    symbols_file = None
    symbols_share_path = None
    for fname in os.listdir(symbols_local_path):
        if fname.endswith(".so"):
            symbols_file = os.path.join(symbols_local_path, fname)
            symbols_share_path = os.path.join(dst_path, "symbols")
            break

    for fname in os.listdir(product_path):
        if fname.endswith("_size_result.txt") or fname.endswith(".map"):    # 将原始 map 文件及分析结果文件都上传至服务器
            upload_file_list.append(os.path.join(product_path, fname))

    m = _mount_share_server()
    try:
        m.mount()
        m.push(zip_file, dst_path)
        m.push(symbols_file, symbols_share_path)
        for _file in upload_file_list:
            m.push(_file, dst_path)
    finally:
        m.umount()

    print ("<< remove zip file")
    zegoio.delete(zip_file)

    print ("<< upload done!")
    

def upload_embedded_linux_lib_to_share_server(dst_path, platform, date_version, share_folder):
    print ("<< zip")
    
    zip_file_path = os.path.relpath(os.path.join(dst_path, '..', 'release'))
    zip_name = '{0}-{1}.zip'.format(date_version, platform)
    print ("<< zip {0} to {1}".format(dst_path, zip_name))
    success = ziputil.zip_folder(dst_path, zip_file_path, zip_name)
    if not success:
        raise Exception('<<zip failed!')

    zip_file = os.path.realpath(os.path.join(zip_file_path, zip_name))

    print ("<<Upload to share")
    m = _mount_share_server()
    try:
        dst_share_path = '{0}/{1}'.format(share_folder, date_version)
        m.push(zip_file, dst_share_path)
    finally:
        m.umount()

    print ("<< remove zip file")
    zegoio.delete(zip_file)
       
    print ("<< upload done!")
    return zip_name


def upload_to_share_server(upload_file_list, remote_folder):
    def _upload_folder(folder, remote_folder_name, m):
        abs_path = os.path.realpath(folder)
        root_dir = os.path.dirname(abs_path)
        for root, folders, items in os.walk(abs_path):
            for _item in items:
                rel_path = root.replace(root_dir, "")
                if rel_path.startswith('/') or rel_path.startswith('\\'):
                    rel_path = rel_path[1:]
                target = os.path.join(remote_folder_name, rel_path)
                src = os.path.join(root, _item)
                print("upload: {} to {}".format(src, target))
                m.push(src, target)

    print("<<Upload to share")
    m = _mount_share_server()
    try:
        m.mount()
        for _file in upload_file_list:
            if os.path.isdir(_file):
                _upload_folder(_file, remote_folder, m)
            else:
                m.push(_file, remote_folder)
    finally:
        m.umount()

    print("<< upload done!")
    print("download url: smb://192.168.1.3/share/{}".format(remote_folder))


def _mount_share_server():
    m = mount.Mount("192.168.1.3", "share")
    m.set_user("share", "share@zego")
    return m
