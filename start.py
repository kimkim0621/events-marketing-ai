#!/usr/bin/env python3
"""
イベント集客施策提案AI 起動スクリプト
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_streamlit():
    """Streamlit Webアプリケーションを起動"""
    print("🚀 Streamlit Webアプリケーションを起動しています...")
    print("ブラウザで http://localhost:8501 にアクセスしてください")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])

def run_api():
    """FastAPI サーバーを起動"""
    print("🚀 FastAPI サーバーを起動しています...")
    print("APIサーバー: http://localhost:8000")
    print("APIドキュメント: http://localhost:8000/docs")
    subprocess.run([sys.executable, "main.py"])

def install_dependencies():
    """依存関係をインストール"""
    print("📦 依存関係をインストールしています...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def main():
    parser = argparse.ArgumentParser(description="イベント集客施策提案AI")
    parser.add_argument(
        "mode", 
        choices=["web", "api", "install"],
        help="起動モード: web (Streamlit), api (FastAPI), install (依存関係インストール)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎯 イベント集客施策提案AI")
    print("=" * 60)
    
    if args.mode == "install":
        install_dependencies()
    elif args.mode == "web":
        run_streamlit()
    elif args.mode == "api":
        run_api()

if __name__ == "__main__":
    main() 