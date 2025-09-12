# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Docker Compose Integration**: Added support for running multi-container applications with Docker Compose inside VMs
  - New example in `examples/5-docker-compose/` demonstrating a Flask app with Nginx reverse proxy
  - Automated test script `test_compose.sh` to verify the setup
  - Documentation updates in README.md
- Support for multiple storage pool configurations
- Enhanced error handling for VM creation and management
- New documentation for system administrators

### Changed
- Updated documentation to include Docker Compose usage instructions
- Improved error handling for container startup and health checks
- Updated default VM configuration to use 2 vCPUs and 2GB RAM
- Improved cleanup procedures for VM removal
- Better handling of system paths and permissions

### Fixed
- Fixed SSH key handling in cloud-init configuration
- Resolved issues with port forwarding in multi-container setups
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
