"""
Prompts Package - Centralized LLM Prompt Templates
Separation of concerns: All LLM prompts are managed here
"""

from .api_mapper_prompts import APIMapperPrompts

__all__ = ['APIMapperPrompts']
