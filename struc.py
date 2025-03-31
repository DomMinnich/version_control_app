import os
import sys

def print_directory_structure(output_file, directory, indent=''):
    """Print the structure of directory with indentation to the specified output file"""
    if not os.path.exists(directory):
        output_file.write(f"Directory does not exist: {directory}\n")
        return
    
    output_file.write(f"{indent}Directory: {os.path.basename(directory)}/\n")
    indent += '    '
    
    # List all items in the directory
    items = os.listdir(directory)
    
    # Sort items - directories first, then files
    dirs = [item for item in items if os.path.isdir(os.path.join(directory, item))]
    files = [item for item in items if os.path.isfile(os.path.join(directory, item))]
    
    dirs.sort()
    files.sort()
    
    # Process directories first
    for dir_name in dirs:
        # Skip __pycache__ directories
        if dir_name == "__pycache__":
            output_file.write(f"{indent}{dir_name}/ (skipped)\n")
            continue
        print_directory_structure(output_file, os.path.join(directory, dir_name), indent)
    
    # Then process files
    for file_name in files:
        file_path = os.path.join(directory, file_name)
        output_file.write(f"{indent}File: {file_name}\n")
        
        # Write file content for text files
        try:
            # Skip large or binary files
            file_size = os.path.getsize(file_path)
            file_extension = os.path.splitext(file_name)[1].lower()
            
            binary_extensions = ['.exe', '.pyc', '.pyd', '.dll', '.so', '.png', '.jpg', '.jpeg']
            skip_file = any(file_name.endswith(ext) for ext in binary_extensions) or file_size > 1000000
            
            if skip_file:
                output_file.write(f"{indent}    (Binary or large file, content skipped)\n")
            else:
                output_file.write(f"{indent}    Content:\n")
                output_file.write(f"{indent}    {'-' * 40}\n")
                
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                # Write content with additional indentation
                for line in content.splitlines():
                    output_file.write(f"{indent}    {line}\n")
                
                output_file.write(f"{indent}    {'-' * 40}\n")
                output_file.write(f"{indent}    End of file\n")
        except Exception as e:
            output_file.write(f"{indent}    Error reading file: {str(e)}\n")


def main():
    # Current directory where the script is running
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, "app_structure_output.txt")
    
    # Directories to analyze
    directories = [
        os.path.join(base_dir, "app_control"),
        os.path.join(base_dir, "server")
    ]
    
    with open(output_path, 'w', encoding='utf-8') as output_file:
        output_file.write("APPLICATION STRUCTURE ANALYSIS\n")
        output_file.write("=" * 50 + "\n\n")
        
        for directory in directories:
            print_directory_structure(output_file, directory)
            output_file.write("\n" + "=" * 50 + "\n\n")
    
    print(f"Structure analysis complete. Output written to: {output_path}")

if __name__ == "__main__":
    main()