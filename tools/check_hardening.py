"""Ensure ELF artifacts do not request an executable process stack."""
import subprocess,sys
for filename in sys.argv[1:]:
    output=subprocess.check_output(['readelf','-W','-l',filename],text=True)
    stack=next(line for line in output.splitlines() if 'GNU_STACK' in line)
    flags=stack.split()[-2]
    if 'E' in flags:raise SystemExit('Executable stack requested: '+filename)
    print(filename+': non-executable stack ('+flags+')')
