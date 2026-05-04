import streamlit as st
import streamlit.components.v1 as components
import os

_COMPONENT_DIR = os.path.dirname(os.path.abspath(__file__))
_component = components.declare_component("speech_input", path=_COMPONENT_DIR)

def speech_input(key: str, default=None):
    return _component(key=key, default=default, height=60)
