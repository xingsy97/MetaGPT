#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Desc: Provide configuration, singleton.
@Modified By: mashenquan, replace `CONFIG` with `os.environ` to support personal config
        `os.environ` doesn't support personalization, while `Config` does.
        Hence, the parameter reading priority is `Config` first, and if not found, then `os.environ`.
@Modified By: mashenquan, 2023/8/23. Add `options` to `Config.__init__` to support externally specified options.
"""
import os

import openai
import yaml

from metagpt.const import PROJECT_ROOT
from metagpt.logs import logger
from metagpt.tools import SearchEngineType, WebBrowserEngineType
from metagpt.utils.singleton import Singleton


class NotConfiguredException(Exception):
    """Exception raised for errors in the configuration.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="The required configuration is not set"):
        self.message = message
        super().__init__(self.message)


class Config:
    """
    For example:

    ```python
    config = Config("config.yaml")
    secret_key = config.get_key("MY_SECRET_KEY")
    print("Secret key:", secret_key)
    ```
    """

    key_yaml_file = PROJECT_ROOT / "config/key.yaml"
    default_yaml_file = PROJECT_ROOT / "config/config.yaml"

    def __init__(self, yaml_file=default_yaml_file, options=None):
        self._configs = {}
        self._init_with_config_files_and_env(self._configs, yaml_file)
        if options:
            self._configs.update(options)
        self._parse()

    def _parse(self):
        logger.info("Config loading done.")
        self.global_proxy = self._get("GLOBAL_PROXY")
        self.openai_api_key = self._get("OPENAI_API_KEY")
        self.anthropic_api_key = self._get("Anthropic_API_KEY")
        if (not self.openai_api_key or "YOUR_API_KEY" == self.openai_api_key) and (
                not self.anthropic_api_key or "YOUR_API_KEY" == self.anthropic_api_key
        ):
            raise NotConfiguredException("Set OPENAI_API_KEY or Anthropic_API_KEY first")
        self.openai_api_base = self._get("OPENAI_API_BASE")
        openai_proxy = self._get("OPENAI_PROXY") or self.global_proxy
        if openai_proxy:
            openai.proxy = openai_proxy
            openai.api_base = self.openai_api_base
        self.openai_api_type = self._get("OPENAI_API_TYPE")
        self.openai_api_version = self._get("OPENAI_API_VERSION")
        self.openai_api_rpm = self._get("RPM", 3)
        self.openai_api_model = self._get("OPENAI_API_MODEL", "gpt-4")
        self.max_tokens_rsp = self._get("MAX_TOKENS", 2048)
        self.deployment_id = self._get("DEPLOYMENT_ID")

        self.claude_api_key = self._get("Anthropic_API_KEY")
        self.serpapi_api_key = self._get("SERPAPI_API_KEY")
        self.serper_api_key = self._get("SERPER_API_KEY")
        self.google_api_key = self._get("GOOGLE_API_KEY")
        self.google_cse_id = self._get("GOOGLE_CSE_ID")
        self.search_engine = SearchEngineType(self._get("SEARCH_ENGINE", SearchEngineType.SERPAPI_GOOGLE))
        self.web_browser_engine = WebBrowserEngineType(self._get("WEB_BROWSER_ENGINE", WebBrowserEngineType.PLAYWRIGHT))
        self.playwright_browser_type = self._get("PLAYWRIGHT_BROWSER_TYPE", "chromium")
        self.selenium_browser_type = self._get("SELENIUM_BROWSER_TYPE", "chrome")

        self.long_term_memory = self._get("LONG_TERM_MEMORY", False)
        if self.long_term_memory:
            logger.warning("LONG_TERM_MEMORY is True")
        self.max_budget = self._get("MAX_BUDGET", 10.0)
        self.total_cost = 0.0

        self.puppeteer_config = self._get("PUPPETEER_CONFIG", "")
        self.mmdc = self._get("MMDC", "mmdc")
        self.calc_usage = self._get("CALC_USAGE", True)
        self.model_for_researcher_summary = self._get("MODEL_FOR_RESEARCHER_SUMMARY")
        self.model_for_researcher_report = self._get("MODEL_FOR_RESEARCHER_REPORT")

    def _init_with_config_files_and_env(self, configs: dict, yaml_file):
        """Load in decreasing priority from `config/key.yaml`, `config/config.yaml`, and environment variables."""
        configs.update(os.environ)

        for _yaml_file in [yaml_file, self.key_yaml_file]:
            if not _yaml_file.exists():
                continue

            # Load local YAML file.
            with open(_yaml_file, "r", encoding="utf-8") as file:
                yaml_data = yaml.safe_load(file)
                if not yaml_data:
                    continue
                configs.update(yaml_data)

    def _get(self, *args, **kwargs):
        return self._configs.get(*args, **kwargs)

    def get(self, key, *args, **kwargs):
        """Retrieve value from `config/key.yaml`, `config/config.yaml`, and environment variables.
        Raise an error if not found."""
        value = self._get(key, *args, **kwargs)
        if value is None:
            raise ValueError(f"Key '{key}' not found in environment variables or in the YAML file")
        return value

    @property
    def runtime_options(self):
        """Runtime key-value configuration parameters."""
        opts = {}
        for k, v in self._configs.items():
            opts[k] = v
        for attribute, value in vars(self).items():
            if attribute == "_configs":
                continue
            opts[attribute] = value
        return opts

