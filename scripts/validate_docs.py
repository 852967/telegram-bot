import os
import glob
from pathlib import Path

def validate_markdown_files():
    """验证文档文件基本完整性"""
    docs_dir = Path('docs')
    required_files = [
        'API_REFERENCE.md',
        'DEPLOYMENT_GUIDE.md', 
        'DEVELOPER_GUIDE.md'
    ]
    
    # 检查文件存在性
    missing_files = [
        f for f in required_files 
        if not (docs_dir / f).exists()
    ]
    if missing_files:
        raise FileNotFoundError(f"缺少文档文件: {missing_files}")
    
    # 检查基础内容
    for doc_file in docs_dir.glob('*.md'):
        print(f"验证文件: {doc_file.name}")
        content = doc_file.read_text(encoding='utf-8')
        
        # 检查代码块封闭
        if '```' in content:
            if content.count('```') % 2 != 0:
                raise ValueError(f"{doc_file}: 代码块未封闭")
                
        # 检查端口配置
        if 'port' in content.lower():
            if '8000' not in content:
                print(f"警告: {doc_file} 中未发现默认端口8000")

if __name__ == '__main__':
    validate_markdown_files()
    print("所有文档验证通过")