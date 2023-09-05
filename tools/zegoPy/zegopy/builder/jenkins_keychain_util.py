import os

def unlock_keychain_if_need():
    # The keychain only needs to be unlocked when running on jenkins
    if not os.environ.get('JENKINS_HOME') and not os.environ.get('CI'):
        return

    # Assuming that 'zego.keychain' is deployed on all macOS node
    cmd = 'security unlock-keychain -p "zego@2021" ~/Library/Keychains/zego.keychain'
    print('[*] Unlock keychain for CI, execute: "{}"'.format(cmd))
    os.system(cmd)
