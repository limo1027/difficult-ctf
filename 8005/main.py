import hashlib
import subprocess
import os
if not os.path.exists("app.py.bak"):
    open("app.py.bak", "w").write(open("app.py").read())
if hashlib.sha1(open("app.py.bak").read().encode()).hexdigest() != hashlib.sha1(open("app.py").read().encode()).hexdigest():
    open("app.py", mode='w').write(open("app.py.bak").read())
subprocess.run(["python", "app.py"])
