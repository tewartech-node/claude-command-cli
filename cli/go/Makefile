.PHONY: help build test lint fmt clean install

BINARY_NAME=claude-cli
VERSION=0.1.0-alpha
BUILD_DATE=$(shell date -u '+%Y-%m-%d_%H:%M:%S')
GO_BUILD_LDFLAGS=-ldflags "-X main.Version=$(VERSION) -X main.BuildDate=$(BUILD_DATE)"

help:
	@echo "Claude CLI Build System"
	@echo ""
	@echo "Targets:"
	@echo "  make build          - Build for current platform"
	@echo "  make build-all      - Build for all platforms (Windows, Linux, macOS, ARM)"
	@echo "  make build-linux    - Build for Linux (x64, ARM64, ARM32)"
	@echo "  make build-windows  - Build for Windows (x64, x86)"
	@echo "  make build-macos    - Build for macOS (universal: arm64+x86_64)"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linter"
	@echo "  make fmt            - Format code"
	@echo "  make install        - Install to ~/bin"
	@echo "  make clean          - Remove build artifacts"

build:
	go build $(GO_BUILD_LDFLAGS) -o bin/$(BINARY_NAME) cmd/claude/main.go

test:
	go test -v -race -cover ./...

lint:
	golangci-lint run ./...

fmt:
	go fmt ./...
	goimports -w .

clean:
	rm -rf bin/ dist/

# Cross-platform builds
build-linux:
	@echo "Building for Linux..."
	@mkdir -p dist
	GOOS=linux GOARCH=amd64 go build $(GO_BUILD_LDFLAGS) -o dist/$(BINARY_NAME)-linux-x64 cmd/claude/main.go
	GOOS=linux GOARCH=arm64 go build $(GO_BUILD_LDFLAGS) -o dist/$(BINARY_NAME)-linux-arm64 cmd/claude/main.go
	GOOS=linux GOARCH=arm go build $(GO_BUILD_LDFLAGS) -o dist/$(BINARY_NAME)-linux-arm32 cmd/claude/main.go
	@ls -lh dist/$(BINARY_NAME)-linux-*

build-windows:
	@echo "Building for Windows..."
	@mkdir -p dist
	GOOS=windows GOARCH=amd64 go build $(GO_BUILD_LDFLAGS) -o dist/$(BINARY_NAME)-windows-x64.exe cmd/claude/main.go
	GOOS=windows GOARCH=386 go build $(GO_BUILD_LDFLAGS) -o dist/$(BINARY_NAME)-windows-x86.exe cmd/claude/main.go
	@ls -lh dist/$(BINARY_NAME)-windows-*.exe

build-macos:
	@echo "Building for macOS..."
	@mkdir -p dist
	GOOS=darwin GOARCH=amd64 go build $(GO_BUILD_LDFLAGS) -o dist/$(BINARY_NAME)-macos-x64 cmd/claude/main.go
	GOOS=darwin GOARCH=arm64 go build $(GO_BUILD_LDFLAGS) -o dist/$(BINARY_NAME)-macos-arm64 cmd/claude/main.go
	lipo -create dist/$(BINARY_NAME)-macos-x64 dist/$(BINARY_NAME)-macos-arm64 -output dist/$(BINARY_NAME)-macos-universal
	rm -f dist/$(BINARY_NAME)-macos-x64 dist/$(BINARY_NAME)-macos-arm64
	@ls -lh dist/$(BINARY_NAME)-macos-*

build-all: build-linux build-windows build-macos
	@echo "✓ All platforms built"
	@echo ""
	@du -sh dist/*
	@echo ""
	@echo "Binaries ready in dist/"

install: build
	cp bin/$(BINARY_NAME) ~/bin/$(BINARY_NAME)
	chmod +x ~/bin/$(BINARY_NAME)
	@echo "✓ Installed to ~/bin/$(BINARY_NAME)"

dev-setup:
	go mod download
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Package managers (Linux)
package-deb: build-linux
	@echo "Building .deb package..."
	@mkdir -p dist/deb/usr/local/bin
	cp dist/$(BINARY_NAME)-linux-x64 dist/deb/usr/local/bin/$(BINARY_NAME)
	chmod +x dist/deb/usr/local/bin/$(BINARY_NAME)
	@echo "Package structure ready at dist/deb/"

package-rpm: build-linux
	@echo "Building .rpm package..."
	@mkdir -p dist/rpm/usr/local/bin
	cp dist/$(BINARY_NAME)-linux-x64 dist/rpm/usr/local/bin/$(BINARY_NAME)
	chmod +x dist/rpm/usr/local/bin/$(BINARY_NAME)
	@echo "Package structure ready at dist/rpm/"

# Development
run: build
	./bin/$(BINARY_NAME) status

run-ai: build
	./bin/$(BINARY_NAME) ai "What is Go?"

run-setup: build
	./bin/$(BINARY_NAME) setup
