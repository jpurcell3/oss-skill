"""
Configuration Management for OSS Compliance Scanning

Simplified configuration system for standalone usage without web application dependencies.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Optional, List
from cryptography.fernet import Fernet


class ComplianceConfig:
    """
    Configuration manager for OSS compliance scanning.
    
    Simplified version that works independently of the web application,
    using environment variables and simple YAML files.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration from file or environment variables.
        
        Args:
            config_file: Path to YAML configuration file (optional)
        """
        self.config_file = config_file or os.getenv('OSS_COMPLIANCE_CONFIG', 'oss_compliance_config.yaml')
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load configuration from file or environment variables."""
        config = {}
        
        # Try to load from file
        if Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                    config.update(file_config)
                    print(f"[INFO] Loaded configuration from {self.config_file}")
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        # Override with environment variables (only if set)
        env_overrides = {}
        
        if os.getenv('GITHUB_TOKEN'):
            env_overrides['github_token'] = os.getenv('GITHUB_TOKEN')
        if os.getenv('GITHUB_API_URL'):
            env_overrides['github_api_url'] = os.getenv('GITHUB_API_URL')
        if os.getenv('GITHUB_ORG'):
            env_overrides['github_org'] = os.getenv('GITHUB_ORG')
        if os.getenv('JENKINS_URL'):
            env_overrides['jenkins_url'] = os.getenv('JENKINS_URL')
        if os.getenv('JENKINS_USER'):
            env_overrides['jenkins_user'] = os.getenv('JENKINS_USER')
        if os.getenv('JENKINS_TOKEN'):
            env_overrides['jenkins_token'] = os.getenv('JENKINS_TOKEN')
        if os.getenv('ARTIFACTORY_BASE'):
            env_overrides['artifactory_base'] = os.getenv('ARTIFACTORY_BASE')
        if os.getenv('SSL_VERIFY'):
            env_overrides['ssl_verify'] = os.getenv('SSL_VERIFY', 'false').lower() == 'true'
        if os.getenv('CACHE_TTL_HOURS'):
            env_overrides['cache_ttl_hours'] = int(os.getenv('CACHE_TTL_HOURS', '24'))
        
        # Handle virtual repos environment overrides
        virtual_repos = config.get('virtual_repos', {})
        if os.getenv('VIRTUAL_REPO_NPM'):
            virtual_repos['npm'] = os.getenv('VIRTUAL_REPO_NPM')
        if os.getenv('VIRTUAL_REPO_PYPI'):
            virtual_repos['pypi'] = os.getenv('VIRTUAL_REPO_PYPI')
        if os.getenv('VIRTUAL_REPO_MAVEN'):
            virtual_repos['maven'] = os.getenv('VIRTUAL_REPO_MAVEN')
        if os.getenv('VIRTUAL_REPO_DOCKER'):
            virtual_repos['docker'] = os.getenv('VIRTUAL_REPO_DOCKER')
        if os.getenv('VIRTUAL_REPO_GO'):
            virtual_repos['go'] = os.getenv('VIRTUAL_REPO_GO')
        
        if virtual_repos:
            env_overrides['virtual_repos'] = virtual_repos
        
        # Merge environment overrides (environment takes precedence)
        config.update(env_overrides)
        
        # Set defaults for missing values
        config.setdefault('github_api_url', 'https://api.github.com')
        config.setdefault('artifactory_base', 'artifactory.example.com')
        config.setdefault('virtual_repos', {
            'npm': 'npm-virtual',
            'pypi': 'pypi-virtual',
            'maven': 'maven-virtual',
            'docker': 'docker-virtual',
            'go': 'go-virtual',
        })
        config.setdefault('ssl_verify', False)
        config.setdefault('cache_ttl_hours', 24)
        
        return config
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def get_github_token(self) -> Optional[str]:
        """Get GitHub authentication token."""
        # Try nested structure first (github: token)
        token = self.get('github.token')
        if token:
            return token
        # Try flat structure (github_token)
        return self.get('github_token')
    
    def get_github_api_url(self) -> str:
        """Get GitHub API URL."""
        # Try nested structure first (github: api_url)
        api_url = self.get('github.api_url')
        if api_url:
            return api_url
        # Try flat structure (github_api_url)
        return self.get('github_api_url', 'https://api.github.com')
    
    def get_github_org(self) -> Optional[str]:
        """Get GitHub organization name."""
        # Try nested structure first (github: org)
        org = self.get('github.org')
        if org:
            return org
        # Try flat structure (github_org)
        return self.get('github_org')
    
    def get_jenkins_url(self) -> Optional[str]:
        """Get Jenkins server URL."""
        # Try nested structure first (jenkins: url)
        url = self.get('jenkins.url')
        if url:
            return url
        # Try flat structure (jenkins_url)
        return self.get('jenkins_url')
    
    def get_jenkins_credentials(self) -> tuple:
        """Get Jenkins authentication credentials."""
        # Try nested structure first (jenkins: user/token)
        user = self.get('jenkins.user')
        token = self.get('jenkins.token')
        if user and token:
            return (user, token)
        # Try flat structure (jenkins_user/jenkins_token)
        return (self.get('jenkins_user'), self.get('jenkins_token'))
    
    def get_artifactory_base(self) -> str:
        """Get Artifactory base URL."""
        # Try nested structure first (artifactory: base_url)
        base_url = self.get('artifactory.base_url')
        if base_url:
            return base_url
        # Try flat structure (artifactory_base)
        return self.get('artifactory_base', 'artifactory.example.com')
    
    def get_virtual_repos(self) -> Dict:
        """Get virtual repository mappings."""
        # Try nested structure first (artifactory: virtual_repos)
        virtual_repos = self.get('artifactory.virtual_repos')
        if virtual_repos:
            return virtual_repos
        # Try flat structure (virtual_repos)
        return self.get('virtual_repos', {})
    
    def get_ssl_verify(self) -> bool:
        """Get SSL verification setting."""
        return self.get('ssl_verify', False)
    
    def get_cache_ttl_hours(self) -> int:
        """Get cache TTL in hours."""
        return self.get('cache_ttl_hours', 24)
    
    def validate(self) -> bool:
        """Validate required configuration."""
        if not self.get_github_token():
            print("Warning: GITHUB_TOKEN not configured")
            return False
        if not self.get_github_org():
            print("Warning: GITHUB_ORG not configured")
            return False
        print("[INFO] Configuration validation passed")
        return True