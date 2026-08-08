#!/bin/bash
set -e

# Create platform-specific installers
# Requires: fpm (for .deb/.rpm), Create MSI manually or use WiX

VERSION="0.1.0-alpha"
BINARY_NAME="claude-cli"
DIST_DIR="$(pwd)/dist"
INSTALLERS_DIR="$(pwd)/dist/installers"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}Creating Platform Installers${NC}"
mkdir -p "$INSTALLERS_DIR"

# Check for required tools
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 not found. Install it and try again.${NC}"
        return 1
    fi
}

# Create Debian package
create_deb() {
    echo -e "${BLUE}Creating .deb package...${NC}"

    if ! check_command "fpm"; then
        echo "Skipping .deb creation (fpm not installed)"
        echo "Install: sudo apt install ruby-dev && sudo gem install fpm"
        return
    fi

    fpm \
        -s dir \
        -t deb \
        -n $BINARY_NAME \
        -v $VERSION \
        --prefix /usr/local/bin \
        --description "Universal Claude CLI - Lightweight client for warnetech-server" \
        --url "https://github.com/tewartech-node/claude-command-cli" \
        --maintainer "TewartechNode <support@tewartech.com>" \
        --license "Apache-2.0" \
        -C $DIST_DIR \
        ${BINARY_NAME}-linux-x64=/claude-cli

    mv ${BINARY_NAME}_${VERSION}_amd64.deb "$INSTALLERS_DIR/"
    echo -e "${GREEN}✓${NC} Created: $INSTALLERS_DIR/${BINARY_NAME}_${VERSION}_amd64.deb"
}

# Create RPM package
create_rpm() {
    echo -e "${BLUE}Creating .rpm package...${NC}"

    if ! check_command "fpm"; then
        echo "Skipping .rpm creation (fpm not installed)"
        return
    fi

    fpm \
        -s dir \
        -t rpm \
        -n $BINARY_NAME \
        -v $VERSION \
        --prefix /usr/local/bin \
        --description "Universal Claude CLI - Lightweight client for warnetech-server" \
        --url "https://github.com/tewartech-node/claude-command-cli" \
        --maintainer "TewartechNode <support@tewartech.com>" \
        --license "Apache-2.0" \
        -C $DIST_DIR \
        ${BINARY_NAME}-linux-x64=/claude-cli

    mv ${BINARY_NAME}-${VERSION}-1.x86_64.rpm "$INSTALLERS_DIR/"
    echo -e "${GREEN}✓${NC} Created: $INSTALLERS_DIR/${BINARY_NAME}-${VERSION}-1.x86_64.rpm"
}

# Create macOS DMG (requires macOS)
create_dmg() {
    echo -e "${BLUE}Creating .dmg for macOS...${NC}"

    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo "Skipping DMG creation (not on macOS)"
        return
    fi

    # Create temporary DMG structure
    local dmg_temp="$INSTALLERS_DIR/${BINARY_NAME}-temp"
    mkdir -p "$dmg_temp/Applications"
    mkdir -p "$dmg_temp/.background"

    # Copy binary
    cp "$DIST_DIR/${BINARY_NAME}-macos-universal" "$dmg_temp/claude-cli"
    chmod +x "$dmg_temp/claude-cli"

    # Create DMG
    hdiutil create \
        -volname "Claude CLI" \
        -srcfolder "$dmg_temp" \
        -ov -format UDZO \
        "$INSTALLERS_DIR/${BINARY_NAME}-${VERSION}.dmg"

    rm -rf "$dmg_temp"
    echo -e "${GREEN}✓${NC} Created: $INSTALLERS_DIR/${BINARY_NAME}-${VERSION}.dmg"
}

# Create Windows MSI (requires WiX Toolset or similar)
create_msi() {
    echo -e "${BLUE}Windows MSI Installer${NC}"
    echo "To create MSI installer:"
    echo "  1. Install WiX Toolset (https://wixtoolset.org/)"
    echo "  2. Use scripts/create-msi.bat on Windows"
    echo "  Or use MSIXPack/Advanced Installer for easier setup"
}

# Create Chocolatey package
create_choco() {
    echo -e "${BLUE}Creating Chocolatey package...${NC}"

    local choco_dir="$INSTALLERS_DIR/chocolatey"
    mkdir -p "$choco_dir/tools"
    mkdir -p "$choco_dir/legal"

    # Create nuspec
    cat > "$choco_dir/claude-cli.nuspec" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>claude-cli</id>
    <version>0.1.0-alpha</version>
    <title>Claude CLI</title>
    <authors>TewartechNode</authors>
    <owners>TewartechNode</owners>
    <description>Universal CLI client for warnetech-server with cross-platform support</description>
    <projectUrl>https://github.com/tewartech-node/claude-command-cli</projectUrl>
    <licenseUrl>https://github.com/tewartech-node/claude-command-cli/blob/main/LICENSE</licenseUrl>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
    <tags>cli ai github authentication</tags>
  </metadata>
  <files>
    <file src="tools\**" target="tools" />
  </files>
</package>
EOF

    # Create PowerShell install script
    cat > "$choco_dir/tools/chocolateyInstall.ps1" << 'EOF'
$ErrorActionPreference = 'Stop'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url64 = "https://github.com/tewartech-node/claude-command-cli/releases/download/v0.1.0-alpha/claude-cli-windows-x64.exe"

$packageArgs = @{
  packageName   = $env:ChocolateyPackageName
  unzipLocation = $toolsDir
  url64bit      = $url64
  checksumType64 = 'sha256'
  checksum64    = 'GENERATE_ME'
}

Install-ChocolateyZipPackage @packageArgs
EOF

    echo -e "${GREEN}✓${NC} Created: $choco_dir/"
    echo "  Next: cd to this directory and run 'choco pack'"
}

# Main execution
echo ""
echo "Available installers:"
echo "  - .deb (Debian/Ubuntu) - via fpm"
echo "  - .rpm (Fedora/RHEL) - via fpm"
echo "  - .dmg (macOS) - via hdiutil"
echo "  - .msi (Windows) - manual (see below)"
echo "  - Chocolatey - via choco"
echo ""

# Create installers
create_deb
create_rpm
create_dmg
create_msi
create_choco

echo ""
echo -e "${GREEN}✓ Installer creation complete${NC}"
echo ""
echo "Installers directory: $INSTALLERS_DIR"
ls -lh "$INSTALLERS_DIR" 2>/dev/null || echo "(no installers created)"
