#!/bin/bash
set -e

# Cross-platform build script for Claude CLI (Go version)
# Builds binaries for Windows, Linux (x64/ARM), and macOS (universal)

VERSION="0.1.0-alpha"
BUILD_DATE=$(date -u '+%Y-%m-%d_%H:%M:%S')
BINARY_NAME="claude-cli"
DIST_DIR="$(pwd)/dist"
GO_BUILD_LDFLAGS="-ldflags \"-X main.Version=${VERSION} -X main.BuildDate=${BUILD_DATE}\""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Claude CLI Cross-Platform Build${NC}"
echo "Version: $VERSION"
echo "Build Date: $BUILD_DATE"
echo ""

# Create dist directory
mkdir -p "$DIST_DIR"

# Function to build for a platform
build_for_platform() {
    local goos=$1
    local goarch=$2
    local output_suffix=$3

    echo -e "${BLUE}Building for $goos/$goarch...${NC}"

    local output_file="$DIST_DIR/${BINARY_NAME}-${output_suffix}"
    if [[ "$goos" == "windows" ]]; then
        output_file="${output_file}.exe"
    fi

    GOOS=$goos GOARCH=$goarch go build $GO_BUILD_LDFLAGS -o "$output_file" cmd/claude/main.go

    if [ -f "$output_file" ]; then
        local size=$(du -h "$output_file" | cut -f1)
        echo -e "${GREEN}✓${NC} Built: $output_file ($size)"
        chmod +x "$output_file" 2>/dev/null || true
    else
        echo -e "${RED}✗${NC} Failed to build $output_file"
        return 1
    fi
}

# Linux builds
echo ""
echo -e "${BLUE}=== Linux Builds ===${NC}"
build_for_platform "linux" "amd64" "linux-x64"
build_for_platform "linux" "arm64" "linux-arm64"
build_for_platform "linux" "arm" "linux-arm32"

# Windows builds
echo ""
echo -e "${BLUE}=== Windows Builds ===${NC}"
build_for_platform "windows" "amd64" "windows-x64"
build_for_platform "windows" "386" "windows-x86"

# macOS builds (Intel)
echo ""
echo -e "${BLUE}=== macOS Builds ===${NC}"
build_for_platform "darwin" "amd64" "macos-x64"
build_for_platform "darwin" "arm64" "macos-arm64"

# Create macOS universal binary
echo ""
echo -e "${BLUE}Creating macOS universal binary...${NC}"
if command -v lipo &> /dev/null; then
    lipo -create \
        "$DIST_DIR/${BINARY_NAME}-macos-x64" \
        "$DIST_DIR/${BINARY_NAME}-macos-arm64" \
        -output "$DIST_DIR/${BINARY_NAME}-macos-universal"

    if [ -f "$DIST_DIR/${BINARY_NAME}-macos-universal" ]; then
        local size=$(du -h "$DIST_DIR/${BINARY_NAME}-macos-universal" | cut -f1)
        echo -e "${GREEN}✓${NC} Created: $DIST_DIR/${BINARY_NAME}-macos-universal ($size)"
        chmod +x "$DIST_DIR/${BINARY_NAME}-macos-universal"

        # Remove individual binaries
        rm -f "$DIST_DIR/${BINARY_NAME}-macos-x64" "$DIST_DIR/${BINARY_NAME}-macos-arm64"
    fi
else
    echo -e "${BLUE}Note: 'lipo' not found, keeping separate macOS binaries${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}=== Build Summary ===${NC}"
echo -e "${GREEN}✓ All builds complete!${NC}"
echo ""
echo "Binaries:"
ls -lh "$DIST_DIR/" | awk 'NR>1 {printf "  %s (%s)\n", $9, $5}'
echo ""
echo "Total size:"
du -sh "$DIST_DIR"
echo ""
echo "Next steps:"
echo "  - Test binaries locally"
echo "  - Run './scripts/create-installers.sh' to create platform packages"
echo "  - Upload to releases: github.com/tewartech-node/claude-command-cli/releases"
