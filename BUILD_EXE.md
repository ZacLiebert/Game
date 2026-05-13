# Build game thành `.exe`

Dùng các file này để đóng gói game thành file chạy trên Windows bằng PyInstaller.

## Cách nhanh nhất trên Windows

1. Cài Python 3.10+ nếu máy chưa có.
2. Mở thư mục project `MutationRPG`.
3. Chạy file:

```bat
build_exe.bat
```

Sau khi build xong, file game sẽ nằm ở:

```text
dist\MutationRPG.exe
```

Bạn có thể gửi file `MutationRPG.exe` này cho giáo viên để chạy game.

## Cách chạy thủ công

```bat
py -3 -m pip install -r requirements.txt
py -3 -m pip install -r requirements-build.txt
py -3 build_exe.py
```

## Ghi chú

- Nên build trên Windows nếu muốn tạo file `.exe` cho Windows.
- PyInstaller tạo file chạy theo hệ điều hành hiện tại. Nếu build trên macOS/Linux thì kết quả sẽ không phải file `.exe` Windows.
- Save game sẽ được tạo trong thư mục `dist\save_data` khi chạy file `.exe`.
