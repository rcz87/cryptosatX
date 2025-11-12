# Script to fix .replit port configuration for VM deployment
import re

# Read current .replit
with open('.replit', 'r') as f:
    content = f.read()

# Remove all [[ports]] sections
content = re.sub(r'\[\[ports\]\][\s\S]*?(?=\n\[|\n$)', '', content)

# Add single correct port mapping for VM deployment
port_config = '''
[[ports]]
localPort = 8000
externalPort = 80
'''

# Append to content
if '[[ports]]' not in content:
    content += port_config

# Write back
with open('.replit', 'w') as f:
    f.write(content)

print("✅ Fixed .replit port configuration:")
print("   localPort = 8000 → externalPort = 80")
