# DockerVirt Examples Test Report
==================================================

**Summary:**
- Total Examples: 3
- Successful Builds: 3

## 1-static-nginx-website

✅ **Build:** SUCCESS (image: my-static-website:latest)

**OS Compatibility:**
- ❌ ubuntu22.04: FAILED - Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/tom/github/dynapsys/dockvirt/dockvirt/cli.py", line 3, in <module>
    from .vm_manager import create_vm, destroy_vm, get_vm_ip
  File "/home/tom/github/dynapsys/dockvirt/dockvirt/vm_manager.py", line 3, in <module>
    from jinja2 import Template
ModuleNotFoundError: No module named 'jinja2'

- ❌ fedora38: FAILED - Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/tom/github/dynapsys/dockvirt/dockvirt/cli.py", line 3, in <module>
    from .vm_manager import create_vm, destroy_vm, get_vm_ip
  File "/home/tom/github/dynapsys/dockvirt/dockvirt/vm_manager.py", line 3, in <module>
    from jinja2 import Template
ModuleNotFoundError: No module named 'jinja2'


## 2-python-flask-app

✅ **Build:** SUCCESS (image: my-flask-app:latest)

**OS Compatibility:**
- ❌ ubuntu22.04: FAILED - Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/tom/github/dynapsys/dockvirt/dockvirt/cli.py", line 3, in <module>
    from .vm_manager import create_vm, destroy_vm, get_vm_ip
  File "/home/tom/github/dynapsys/dockvirt/dockvirt/vm_manager.py", line 3, in <module>
    from jinja2 import Template
ModuleNotFoundError: No module named 'jinja2'

- ❌ fedora38: FAILED - Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/tom/github/dynapsys/dockvirt/dockvirt/cli.py", line 3, in <module>
    from .vm_manager import create_vm, destroy_vm, get_vm_ip
  File "/home/tom/github/dynapsys/dockvirt/dockvirt/vm_manager.py", line 3, in <module>
    from jinja2 import Template
ModuleNotFoundError: No module named 'jinja2'


## 3-multi-os-comparison

✅ **Build:** SUCCESS (image: multi-os-demo:latest)

**OS Compatibility:**
- ❌ ubuntu22.04: FAILED - Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/tom/github/dynapsys/dockvirt/dockvirt/cli.py", line 3, in <module>
    from .vm_manager import create_vm, destroy_vm, get_vm_ip
  File "/home/tom/github/dynapsys/dockvirt/dockvirt/vm_manager.py", line 3, in <module>
    from jinja2 import Template
ModuleNotFoundError: No module named 'jinja2'

- ❌ fedora38: FAILED - Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/tom/github/dynapsys/dockvirt/dockvirt/cli.py", line 3, in <module>
    from .vm_manager import create_vm, destroy_vm, get_vm_ip
  File "/home/tom/github/dynapsys/dockvirt/dockvirt/vm_manager.py", line 3, in <module>
    from jinja2 import Template
ModuleNotFoundError: No module named 'jinja2'

