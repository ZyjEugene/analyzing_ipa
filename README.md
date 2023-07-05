# ipa包检测脚本的使用说明（Python3）

----
## 方法一
>将 **包检测脚本** 和 **ipa包文件** 放在同一文件夹下，使用以下命令，可自动解析。

使用脚本文件:
````
cd 脚本目录
python3 ipa.py
````

使用脚本可执行文件:
````
cd 脚本目录
./ipa
````

对ipa包中app可执行文件，进行指令操作

````
python3 ipa.py --b_cmd 'otool -ov' --grep 'logger'
或
./ipa --b_cmd 'otool -ov' --grep 'logger'
````

## 方法二
> **cd**到脚本所在的目录，直接使用以下命令，可自行解析。
> 
使用脚本文件:
````
cd 脚本目录
python3 ipa.py ipa文件路径 
````

使用脚本可执行文件:
````
cd 脚本目录
./ipa ipa文件路径
````

对ipa包中app可执行文件，进行指令操作
> eg: python3 ipa.py --b_cmd 'otool -ov' --ipapath /Users/yanjin/Desktop/YanJin-Workspace/PythonProjects/xxx.ipa --grep 'logger'
````
python3 ipa.py --b_cmd 'otool -ov' --ipapath ipa文件路径 --grep 'logger'
或
./ipa --b_cmd 'otool -ov' --ipapath ipa文件路径 --grep 'logger'
````

## 脚本指令帮助
````
cd 脚本目录
python3 ipa.py -h 或 ./ipa -h
````

---
## 打包可执行文件指令（将脚本打包成unix可执行文件）
````
pyinstaller -F ipa.py
````

---
## ⚠️可能遇到的问题
[权限问题：zsh: permission denied ..](https://blog.csdn.net/chnyifan/article/details/104705437)
>chmod u+x 需要执行权限的文件路径




