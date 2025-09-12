# Changelog

All notable changes to the dockvirt project will be documented in this file.

## [Unreleased]

### Added
- Support for multiple storage pool configurations
- Enhanced error handling for VM creation and management
- New documentation for system administrators

### Changed
- Updated default VM configuration to use 2 vCPUs and 2GB RAM
- Improved cleanup procedures for VM removal
- Better handling of system paths and permissions

### Fixed
- Fixed issues with VM cleanup and resource deallocation
- Resolved permission issues with system directories
- Fixed network configuration for better reliability

## [0.1.0] - 2025-09-12

### Added
- Initial release of dockvirt
- Basic VM creation and management commands
- Support for Ubuntu and Fedora cloud images
- Integrated Caddy reverse proxy
- Docker container support within VMs
