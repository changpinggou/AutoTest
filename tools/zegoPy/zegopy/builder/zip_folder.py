#! /usr/bin/env python

import os
import zipfile


def zip_folder_list(source_folder_list, dest_folder, zip_name):

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    zip_file = os.path.realpath(os.path.join(dest_folder, zip_name))
    f = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)

    for source_folder in source_folder_list:
        if not os.path.exists(source_folder):
            print (">> source folder do not exist!")
            continue

        filelist = []
        if os.path.isfile(source_folder):
            filelist.append(source_folder)
        else:
            for root, dirs, files in os.walk(source_folder):
                for name in files:
                    filelist.append(os.path.join(root, name))

        for tar in filelist:
            basename = os.path.split(source_folder)[-1]
            arcname = tar[len(source_folder):]
            filename = basename + arcname
            print (">> zip file {0}".format(filename))
            f.write(tar, filename)

    f.close()

    return True


def zip_folder(source_folder, dest_folder, zip_name, exclude_file_names = None):
    def _is_exclude_file(fname):
        if exclude_file_names is None or len(exclude_file_names) == 0:
            return False

        for exclude_name in exclude_file_names:
            if fname.endswith(exclude_name):
                return True
        return False

    if not os.path.exists(source_folder):
        print (">> source folder do not exist!")
        return False

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    filelist = []
    if os.path.isfile(source_folder):
        filelist.append(source_folder)
    else:
        for root, dirs, files in os.walk(source_folder):
            for name in files:
                if _is_exclude_file(name):
                    continue
                filelist.append(os.path.join(root, name))

    zip_file = os.path.realpath(os.path.join(dest_folder, zip_name))
    f = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)
    for tar in filelist:
        basename = os.path.split(source_folder)[-1]
        arcname = tar[len(source_folder):]
        filename = basename + arcname
        print (">> zip file {0}".format(filename))
        f.write(tar, filename)

    f.close()

    return True


def zip_folder_with_link(source_folder, dest_folder, zip_name):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    zip_file = os.path.realpath(os.path.join(dest_folder, zip_name))
    f = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)

    rootLen = len(os.path.dirname(source_folder))
    archive_directory(source_folder, f, rootLen)


def archive_directory(parentDirectory, zipOut, rootLen):
    contents = os.listdir(parentDirectory)

    if not contents:
        archiveRoot = parentDirectory[rootLen:].replace('\\', '/').lstrip('/')
        zipInfo = zipfile.ZipInfo(archiveRoot+'/')
        zipOut.writestr(zipInfo, '')
    for item in contents:
        fullpath = os.path.join(parentDirectory, item)
        if os.path.isdir(fullpath) and not os.path.islink(fullpath):
            archive_directory(fullpath, zipOut, rootLen)
        else:
            archiveRoot = fullpath[rootLen:].replace('\\', '/').lstrip('/')
            print (">> zip file {0}".format(archiveRoot))
            if os.path.islink(fullpath):
                zipInfo = zipfile.ZipInfo(archiveRoot)
                zipInfo.create_system = 3
                # long type of hex val of '0xA1ED0000L',
                # say, symlink attr magic...
                zipInfo.external_attr = 2716663808
                zipOut.writestr(zipInfo, os.readlink(fullpath))
            else:
                zipOut.write(fullpath, archiveRoot, zipfile.ZIP_DEFLATED)


def unzip_file(source_zip_file, dest_folder):
    zip_ref = zipfile.ZipFile(source_zip_file, 'r')
    zip_ref.extractall(dest_folder)
    zip_ref.close()


if __name__ == '__main__':
    # zip_folder(sys.argv[1], sys.argv[2], sys.argv[3])
    zip_folder_with_link('/Users/Strong/zegolibs/ZegoLiveRoom/OSX/release',
                         '/Users/Strong/zegolibs/ZegoLiveRoom/OSX', 'test.zip')
