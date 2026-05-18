with open("browser-test/src/index.js", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'currentStorage = null;' in line:
        pass
    elif 'logOutput("データベースを手動で閉じました。（テーブルの表示はそのまま残しています）");' in line:
        new_lines.append(line)
        new_lines.append('            currentStorage = null;\n')
    else:
        new_lines.append(line)

with open("browser-test/src/index.js", "w") as f:
    f.writelines(new_lines)
