# This is a sample Python script.
import time
import zipfile # 解压缩文件
import re
import plistlib # iOS中plist文件的解析库
import subprocess # 子进程库
import os # 操作系统库
import shutil # 文件管理库
import json
import argparse

import sys
from io import BytesIO
from builtins import print

debug = False
ipa_info_result_dir = 'results/'

# 解析ipa的info.plist & embedded.mobileprovision文件，并输出文档
def ipa_info_and_provision_detail(ipa_file):
    print('--------------info文件 - 数据分割线------------------')
    # 'Payload/MYX.app/Info.plist'
    plist_path = find_path(ipa_file, 'Payload/[^/]*.app/Info.plist')
    # 读取plist内容
    plist_data = ipa_file.read(plist_path)
    # 解析plist内容
    plist_detail_info = plistlib.loads(plist_data)
    # 获取plist信息
    get_ipa_info(plist_detail_info)
    # 输出plist文件
    outputp_info_list(plist_detail_info, plist_path)

    print('app info 信息: %s' % str(plist_detail_info))
    # print('app info 信息 JSON: %s' % json.dumps(plist_detail_info, sort_keys=True, indent=4, separators=(',', ': ')))

    print()
    print('--------------描述文件 - 数据分割线------------------')
    # 获取mobileprovision文件路径 'Payload/MYX.app/embedded.mobileprovision'
    provision_path = find_path(ipa_file, 'Payload/[^/]*.app/embedded.mobileprovision')

    # 将mobileprovision保存为plist
    provision_plist_path = output_provision_plist(ipa_file, provision_path)

    # 加载plist并获取信息
    get_provision_info(provision_plist_path)

    # print()
    # 打印mobileprovision内容到控制台
    # print("/usr/libexec/PlistBuddy -c 'Print DeveloperCertificates:0' /dev/stdin <<< $(security cms -D -i %s) | openssl x509 -inform DER -noout -text" % provision_path)
    # os.system("/usr/libexec/PlistBuddy -c 'Print DeveloperCertificates:0' /dev/stdin <<< $(security cms -D -i %s) | openssl x509 -inform DER -noout -text" % provision_path)

# 解压ipa获取并信息
def unzip_ipa(path):
    ipa_file = zipfile.ZipFile(path)

    # 分割二进制解析 与 （ipa的info.plist & embedded.mobileprovision文件解析0
    if len(b_nm) == 0 and len(b_info) == 0 and len(b_strs) == 0 and len(b_cmd) == 0:
        # 解析ipa的info.plist & embedded.mobileprovision文件，并输出文档
        ipa_info_and_provision_detail(ipa_file)
        return

    print()
    print('--------------APP可执行文件 - 数据分割线------------------')
    # 获取ipa包的Unix二进制可执行文件 'Payload/MYX.app/MYX'
    app_unix = get_app_exec(ipa_file, 'Payload/[^/]*.app')
    print('app unix: ' + app_unix)

    # 临时解压 unix可执行文件 到'Payload/MYX.app/'目录下
    ipa_file.extract(app_unix, './')
    # 获取当前路径（脚本所在的文件）
    current_path = os.getcwd()
    print('current_path:' + current_path)

    # 指定 二进制文件指令操作结果 输出文本的路径
    cur_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    app_unix_txt_path = current_path + '/' + ipa_info_result_dir + '%s_app_unix_file.txt' % cur_time
    print('app_text:' + app_unix_txt_path)

    # 二进制可执行文件 操作指令
    unix_file_path = (current_path + '/' + app_unix)
    app_unix_cmd = ''
    if len(b_nm) > 0:
        app_unix_cmd = "%s %s" % (b_nm, unix_file_path)
    elif len(b_info) > 0:
        app_unix_cmd = "%s %s" % (b_info, unix_file_path)
    elif len(b_strs) > 0:
        app_unix_cmd = "%s %s" % (b_strs, unix_file_path)
    elif len(b_cmd) > 0:
        app_unix_cmd = "%s %s" % (b_cmd, unix_file_path)

    if len(b_grep) > 0 and (len(b_nm) > 0 or len(b_info) > 0 or len(b_strs) > 0 or len(b_cmd) > 0):
        app_unix_cmd = "%s | grep %s" % (app_unix_cmd, b_grep)

    print('app unix cmd: %s' % app_unix_cmd)
    print()
    print('ipa可执行文件(%s)的操作命令输出如下:' % app_unix)
    # 控制台输出 指令操作结果
    os.system(app_unix_cmd)

    # 将 指令操作结果 输出 txt文件
    cmd = '%s > %s' % (app_unix_cmd, app_unix_txt_path)
    string_mobileprovision = string_subprocessPopen(cmd, None, False)

    # 删除临时解压文件
    shutil.rmtree('./Payload')

# 获取文件路径
def find_path(zip_file, pattern_str):
    name_list = zip_file.namelist()
    pattern = re.compile(pattern_str)
    for path in name_list:
        m = pattern.match(path)
        if m is not None:
            return m.group()

# 获取Unix可执行文件
def get_app_exec(zip_file, pattern_str):
    name_list = zip_file.namelist()
    pattern = re.compile(pattern_str)
    for path in name_list:
        app_name = get_app_name(path)
        if len(app_name) > 0:
            return path + app_name

# 获取ipa中app的名字
def get_app_name(name_path):
    app_name = ''
    path = name_path
    if path.endswith('/'):
        # 去掉path最后字符 '/' ，并将path根据 '/' 分割成数组
        part_list = path[:-1].split('/')
        if len(part_list) > 0:
            # 逆序遍历
            for part in reversed(part_list):
                if not part.endswith('.app'):
                    continue
                app_name = part.split('.')[0]
                # print('app unix name:' + app_name)
                break
    return app_name

# 获取ipa信息
def get_ipa_info(plist_info):
    print('软件名称: %s' % str(plist_info['CFBundleDisplayName']))
    print('软件标识: %s' % str(plist_info['CFBundleIdentifier']))
    print('软件版本: %s' % str(plist_info['CFBundleShortVersionString']))
    print('支持版本: %s' % str(plist_info['MinimumOSVersion']))
    print('CPU 架构: %s' % str(plist_info['UIRequiredDeviceCapabilities']))

# 获取ipa签名信息 security cms -D -i embedded.mobileprovision
def get_provision_info(provision_plist):
    with open(provision_plist,'rb') as fb:
        plist_info = plistlib.load(fb)
        print('设备描述文件名:',plist_info['Name'])
        print('App ID Name:', plist_info['AppIDName'])
        print('App ID:', plist_info['Entitlements']['application-identifier'])
        print('Team Name:', plist_info['TeamName'])
        print('Team Identifier:', plist_info['TeamIdentifier'])
        print('Platform:', plist_info['Platform'])
        print('UUID:', plist_info['UUID'])
        print('Creation Date:', plist_info['CreationDate'])
        print('Expiration Date:',plist_info['ExpirationDate'])
        print()
        for (key, value) in plist_info['Entitlements'].items():
            print('%s : %s' % (key, value))
        print()
        if 'ProvisionedDevices' not in plist_info:
            print('该ipa的描述文件，不包含ProvisionedDevices字段，即不包含任何测试设备.')
            return
        devices = plist_info['ProvisionedDevices']
        print('已配置的设备:' + str(len(devices)) + '个')
        for device in devices:
            print(device)

'''将ipa中plist输出到文件中, 生成生成新的info.plist文件'''
def outputp_info_list(plist_detail_info, plist_path):
    new_info_plist_dirs = os.getcwd() + '/' + ipa_info_result_dir
    # 判断目录是否存在，不存在就创建
    if not os.path.exists(new_info_plist_dirs):
        os.makedirs(new_info_plist_dirs)

    # 写入内容到新建的plist文件中
    info_plist_name = os.path.basename(plist_path)
    new_info_plist = open(new_info_plist_dirs + info_plist_name, 'w')
    fp = BytesIO()
    plistlib.dump(plist_detail_info, fp)
    if debug:
        print('fp = ', (fp.getvalue()).decode('utf-8'))

    new_info_plist.write((fp.getvalue()).decode('utf-8'))
    new_info_plist.close

'''将ipa中的描述文件，生成plist文件'''
def output_provision_plist(ipa_file,provision_path):
    # 临时解压
    ipa_file.extract(provision_path, './')
    # 获取当前路径（脚本所在的文件）
    current_path = os.getcwd()#os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + os.path.sep + ".")
    print('current_path:' + current_path)

    # 获取mobileprovision保存为plist后的路径
    provision_plist_path = current_path + '/' + ipa_info_result_dir + 'provision_mobileprovision.plist'
    print('provision_plist_path:' + provision_plist_path)
    print()

    # 保存mobileprovision为plist
    cmd = 'security cms -D -i %s > %s' % (current_path + '/' + provision_path, provision_plist_path)
    string_mobileprovision = string_subprocessPopen(cmd, None, False)
    # os.system(cmd)

    return provision_plist_path

def string_subprocessPopen(command, cwd_patch, cancel_newline):
    command_file = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    cwd=cwd_patch)
    command_file.wait()
    command_string = command_file.stdout.read().decode()
    if cancel_newline == True:
        command_string = command_string.replace("\n", '')
    return command_string

# 全局参数
b_nm = ''
b_info = ''
b_strs = ''
b_cmd = ''
b_grep = ''
if __name__ == '__main__':
    # 定义一个命令行参数解析实例:
    parser = argparse.ArgumentParser(description='ipa包检测工具.',)

    # nm 显示符号表，获取Mach-O中的程序符号表:
    parser.add_argument('--b_nm', type=str, default='', nargs='?', help="nm 作用是显示符号表，获取Mach-O中的程序符号表. [B_NM] 参数为可选：nm、'nm -u'、'nm -nm'、或空，更详细的 nm指令，请自行查阅。eg: --b_nm 【nm、'nm -u'、'nm -nm'、或空】")
    # lipo -info 判断静态库所支持的平台 armv7 ｜ x86_64 ｜ arm64:
    parser.add_argument('--b_info', type=str, default='', nargs='?', help="lipo -info 判断静态库所支持的平台 armv7 ｜ x86_64 ｜ arm64. [B_INFO] 参数为可选：'lipo -info'、或空，更详细的 lipo指令，请自行查阅。eg：--b_info 【'lipo -info' 或 空】")
    # strings查看dylib库中包含的字符串（可以此排查二进制文件中是否包含相关字符串）
    parser.add_argument('--b_strs', type=str, default='', nargs='?', help="strings 查看dylib库中包含的字符串（可以此排查二进制文件中是否包含相关字符串）， [B_STRS] 参数为可选：strings、或空。eg: --b_strs 【strings 或 空】")
    # 看可执行程序都链接了哪些库、OC类结构和定义的方法
    parser.add_argument('--b_otool', type=str, default='', nargs='?',
                        help="otool 查看可执行程序都链接了哪些库、OC类结构和定义的方法. [B_OTOOL] 参数为可选：'otool -L'、'otool -ov'等等，更详细的 otool指令，请自行查阅。eg: --b_otool 【'otool -L' 或 'otool -ov'】")
    # 自定义对ipa包unix可执行文件的操作 otool -ov
    parser.add_argument('--b_cmd', type=str, default='', nargs='?',
                        help="自定义的对ipa包中unix可执行文件的操作指令. [B_CMD] 参数为可选：nm、'nm -u'、'nm -nm'、'lipo -info'、strings、'otool -L'、'otool -ov'等等。eg: --b_cmd 【nm、'lipo -info'、strings、'otool -ov'】")

    # 定义ipa位置参数,‘--’表示参数可选: /Users/yanjin/Desktop/YanJin-Workspace/PythonProjects/萌英雄.ipa
    parser.add_argument('--ipapath', default='', help="ipa包文件路径。eg：--ipapath 'ipa包文件路径'")

    # | grep 查询指定的字段 logger
    parser.add_argument('--grep', type=str, default='', help="查询b_nm、b_strs、b_otool输出的结果集中，是否包含 GREP 字段. eg: --grep '你要查找的字段'")

    # 解析参数:
    args = parser.parse_args()
    # 获取cmd指定的ipa路径
    ipa_path = args.ipapath
    b_nm = args.b_nm
    b_info = args.b_info
    b_strs = args.b_strs
    b_cmd = args.b_cmd
    b_grep = args.grep

    # 当参数值为None时， 设置默认值
    if b_nm is None:
        b_nm = 'nm'
    elif b_info is None:
        b_info = 'lipo -info'
    elif b_strs is None:
        b_strs = 'strings'

    print('编译中, 请稍后...')
    '''cmd命令传入的参数 '''
    if len(ipa_path) > 1 and os.path.exists(ipa_path):
        # 获取ipa文件
        filename = os.path.basename(ipa_path)
        # 处理xx.ipa文件
        if filename is not None:
            # 将指定路径的ipa文件，copy到脚本所在的文件夹
            new_ipa_path = os.getcwd() + '/' + filename
            shutil.copyfile(ipa_path, new_ipa_path)
            # 解压缩ipa文件
            unzip_ipa('./' + filename)
        else:
            print('ipa 文件路径错误：%s' % str(sys.argv))
            print('cd ipa可执行文件 或 ipa.py文件 所在的文件夹')
            print('输入：python3 ipa.py ipa路径 或 ./ipa ipa路径')

    else:
        flag = False
        for filename in os.listdir(os.getcwd()):
            hou = os.path.splitext(filename)[-1][1:]
            if hou == 'ipa':
                flag = True
                unzip_ipa('./' + filename)
                break

        if not flag:
            print('当前路径：' + os.getcwd())
            print('请将ipa放在 ipa可执行文件 或 ipa.py文件 所在的文件夹')
            print('输入：python3 ipa.py 或 ./ipa，执行脚本程序')

'''参考文档
Mach-O了解
https://blog.csdn.net/box_kun/article/details/110518606
https://blog.csdn.net/gyhjlauy/article/details/124231590
https://blog.csdn.net/chqj_163/article/details/102730380
https://www.jianshu.com/p/81928c705c88
https://www.jianshu.com/p/2e7466521803

命令解释器的用法
https://docs.python.org/zh-cn/3.6/library/argparse.html
https://zhuanlan.zhihu.com/p/56922793

子进程管理
https://docs.python.org/zh-cn/3/library/subprocess.html

'''