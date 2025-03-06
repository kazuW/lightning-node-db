#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# プロジェクトのルートディレクトリをシステムパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# main モジュールをインポート
from src.main import main

if __name__ == "__main__":
    # CLIとして実行
    sys.exit(main())