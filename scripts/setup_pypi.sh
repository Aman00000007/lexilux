#!/bin/bash
# Setup script for PyPI publishing
# This script helps set up PyPI credentials securely

set -e

echo "🔐 PyPI Publishing Setup"
echo "========================"
echo ""

# Check if .pypirc already exists
if [ -f ~/.pypirc ]; then
    echo "⚠️  Warning: ~/.pypirc already exists"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# Get PyPI token
echo "Enter your PyPI API token:"
echo "(Token will not be displayed)"
read -s PYPI_TOKEN

if [ -z "$PYPI_TOKEN" ]; then
    echo "❌ Error: Token cannot be empty"
    exit 1
fi

# Create .pypirc
cat > ~/.pypirc <<EOF
[pypi]
username = __token__
password = ${PYPI_TOKEN}

[testpypi]
username = __token__
password = ${PYPI_TOKEN}
EOF

# Set permissions
chmod 600 ~/.pypirc

echo ""
echo "✅ PyPI credentials configured in ~/.pypirc"
echo ""
echo "You can now publish using:"
echo "  make upload"
echo ""
echo "Or using twine directly:"
echo "  twine upload dist/*"
echo ""
echo "⚠️  Security reminder:"
echo "  - ~/.pypirc is in your home directory (not in the project)"
echo "  - Never commit this file to git"
echo "  - Keep your token secure"

