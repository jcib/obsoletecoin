"""Record local native build inputs without exporting private workspace contents."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--build', type=Path, default=Path('.local/windows-upgrade'))
p.add_argument('--node', type=Path, help='Staged runtime for the build being recorded')
p.add_argument('--ctest', type=Path, help='CTest report produced by the current build')
a = p.parse_args()
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
files = subprocess.check_output(
    ['git', 'ls-files', '--recurse-submodules', '-z', 'src', 'cmake', 'CMakeLists.txt']
).decode().split('\0')
sources = {name: digest(Path(name)) for name in sorted(files) if name and Path(name).is_file()}
source_json = json.dumps(sources, indent=2) + '\n'
node = a.node or a.build/'node'
(node/'source-hashes.json').write_text(source_json, encoding='utf-8')
manifest = {
    'kind': 'local-windows-build',
    'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'working_tree_changes_included': True,
    'source_hashes_sha256': digest(node/'source-hashes.json'),
    'build_script_sha256': digest(Path('release/build-native-msys.sh')),
    'cmake_cache_sha256': digest(a.build/'core/CMakeCache.txt'),
    'toolchain_sha256': digest(node/'toolchain.txt'),
    'ctest_xml_sha256': digest(a.ctest or a.build/'ctest.xml'),
    'network': 'obsolete',
    'mainnet_enabled': True,
    'files': {path.name: digest(path) for path in sorted(node.iterdir())
              if path.suffix.lower() in ('.exe', '.dll')},
}
(node/'node-provenance.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'source_files': len(sources), 'node': str(node)}))
