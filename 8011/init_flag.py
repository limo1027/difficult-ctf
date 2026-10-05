import shamir_utils
import subprocess
from encrypt import main
import os
import zipfile
import shutil
with open(".enc", mode='w') as f:
    f.write(main())


# 1. 准备要打包的文件
files_to_zip = [
    ".enc"
]

# 2. 创建压缩包
with zipfile.ZipFile("pack.zip", "w", zipfile.ZIP_DEFLATED) as zf:
    for file in files_to_zip:
        if os.path.exists(file):
            zf.write(file)
        else:
            print(f"警告: {file} 不存在")

os.remove(".enc")
with open("background.jpeg", "rb") as f1, open("pack.zip", "rb") as f2, open("output.jpeg", "wb") as out:
    shutil.copyfileobj(f1, out)
    shutil.copyfileobj(f2, out)

with zipfile.ZipFile("pack.zip", "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write("output.jpeg")

os.remove("output.jpeg")

# 1. 读取 encrypt.py 内容
with open("encrypt.py", "r", encoding="utf-8") as f:
    code = f.read()

# 2. 生成两个分片
key1, key2 = shamir_utils.get_key(code)

# 3. 将 key1 写入文件
with open("key1.txt", "w") as f:
    f.write(key1)

# 4. 初始化 Git 仓库（如果已存在则跳过）
subprocess.run(["git", "init"], check=False)

# 5. 添加 key1.txt 并提交
subprocess.run(["git", "add", "key1.txt"], check=True)
subprocess.run(["git", "commit", "-m", "add key"], check=True)

# 6. 为第一次提交添加 notes
subprocess.run(
    ["git", "notes", "add", "-m",
        "An Important encrypt, make many keys, but only need a few keys, it from Lagrange."],
    check=True
)

# 7. 删除 key1.txt 并提交
subprocess.run(["git", "rm", "key1.txt"], check=True)
subprocess.run(["git", "commit", "-m", "remove key"], check=True)

# 8. 为第二次提交添加 notes（key2 的值）
subprocess.run(["git", "notes", "add", "-m", key2], check=True)
