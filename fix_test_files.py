import os
import glob

def fix_test_files():
    """修复测试文件中的格式问题"""
    test_files = glob.glob('tests/**/*.py', recursive=True)
    for file_path in test_files:
        try:
            with open(file_path, 'r+', encoding='utf-8') as f:
                content = f.read()
                # 移除XML标签残留
                fixed_content = content.replace(']]</content>', '')
                if fixed_content != content:
                    f.seek(0)
                    f.write(fixed_content)
                    f.truncate()
                    print(f"Fixed: {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

if __name__ == '__main__':
    fix_test_files()