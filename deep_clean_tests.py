import os
import glob
import re

def clean_test_files():
    """深度清理测试文件"""
    test_files = glob.glob('tests/**/*.py', recursive=True)
    for file_path in test_files:
        try:
            with open(file_path, 'r+', encoding='utf-8') as f:
                content = f.read()
                # 移除所有XML标签残留
                cleaned_content = re.sub(r'<\/?[a-z_]+>', '', content)
                # 移除中文字符错误
                cleaned_content = cleaned_content.replace('：', ':')
                if cleaned_content != content:
                    f.seek(0)
                    f.write(cleaned_content)
                    f.truncate()
                    print(f"Cleaned: {file_path}")
        except Exception as e:
            print(f"Error cleaning {file_path}: {str(e)}")

if __name__ == '__main__':
    clean_test_files()