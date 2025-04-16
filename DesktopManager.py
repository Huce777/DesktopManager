import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import shutil
import re
import json
import requests
import threading


ZHIPU_API_KEY = "428990744831408aa813e6d34a255403.hrMye8CFukhF5EGJ"


class SmartDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("桌面智能管理系统")
        self.root.geometry("1200x800")

        self.categories = {}
        self.file_mapping = {}
        self.drag_data = {"item": None}

        self.create_navbar()
        self.create_panels()
        self.show_panel(self.desktop_org_panel)

        self.status_label = None

    def create_navbar(self):
        navbar = ttk.Frame(self.root)
        navbar.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(navbar, text="桌面整理", command=lambda: self.show_panel(self.desktop_org_panel)).pack(side=tk.LEFT)
        ttk.Button(navbar, text="文件检索", command=self.open_search_window).pack(side=tk.LEFT)

    def create_panels(self):
        self.desktop_org_panel = ttk.Frame(self.root)
        self.create_desktop_org_ui()

    def show_panel(self, panel):
        self.desktop_org_panel.pack_forget()
        panel.pack(fill=tk.BOTH, expand=True)

    def create_desktop_org_ui(self):
        control_frame = ttk.Frame(self.desktop_org_panel)
        control_frame.pack(fill=tk.X, pady=5)

        ttk.Button(control_frame, text="扫描桌面", command=self.scan_desktop).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="新建分类", command=self.create_category).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="执行整理", command=self.organize_files).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="AI一键分类", command=self.ai_auto_classify).pack(side=tk.LEFT)

        paned_window = tk.PanedWindow(self.desktop_org_panel, orient=tk.HORIZONTAL, sashwidth=12, bg="lightgray")
        paned_window.pack(fill=tk.BOTH, expand=True)

        self.desktop_tree = ttk.Treeview(paned_window, columns=("name", "type", "size", "path"), show="headings")
        self.desktop_tree.heading("name", text="文件名")
        self.desktop_tree.heading("type", text="类型")
        self.desktop_tree.heading("size", text="大小")
        self.desktop_tree.heading("path", text="路径")
        self.desktop_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.desktop_tree.bind("<ButtonPress-1>", self.on_drag_start)
        self.desktop_tree.bind("<B1-Motion>", self.on_drag_motion)
        self.desktop_tree.bind("<ButtonRelease-1>", self.on_drag_end)

        category_frame_container = ttk.Frame(paned_window)
        category_frame_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tip_label = ttk.Label(category_frame_container, text="提示：选中分类内的文件后按 Delete 键可将其移除",
                              foreground="gray")
        tip_label.pack(side=tk.TOP, anchor="w", padx=10, pady=(5, 0))

        self.category_canvas = tk.Canvas(category_frame_container, bg="white")
        self.category_container = ttk.Frame(self.category_canvas)

        self.category_scroll_y = tk.Scrollbar(category_frame_container, orient=tk.VERTICAL,
                                              command=self.category_canvas.yview)
        self.category_canvas.configure(yscrollcommand=self.category_scroll_y.set)
        self.category_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.category_scroll_x = tk.Scrollbar(category_frame_container, orient=tk.HORIZONTAL,
                                              command=self.category_canvas.xview)
        self.category_canvas.configure(xscrollcommand=self.category_scroll_x.set)
        self.category_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.category_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.category_canvas.create_window((0, 0), window=self.category_container, anchor="nw")
        self.category_container.bind("<Configure>", lambda e: self.category_canvas.configure(
            scrollregion=self.category_canvas.bbox("all")))

        paned_window.add(self.desktop_tree)
        paned_window.add(category_frame_container)

    def add_category(self, name):
        frame = ttk.LabelFrame(self.category_container, text=name)
        frame.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=5)
        listbox = tk.Listbox(frame, width=30, height=10, selectbackground="lightblue")
        listbox.bind("<Delete>", lambda e, name=name: self.remove_item_from_category(e, name))
        listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.categories[name] = listbox
        self.file_mapping[name] = []

    def create_category(self):
        name = simpledialog.askstring("新建分类", "请输入分类名称:")
        if name and name not in self.categories:
            self.add_category(name)
        elif name:
            messagebox.showwarning("提示", "该分类已存在")

    def scan_desktop(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        self.desktop_tree.delete(*self.desktop_tree.get_children())
        for f in os.listdir(desktop):
            path = os.path.join(desktop, f)
            if os.path.isfile(path):
                size = os.path.getsize(path)
                self.desktop_tree.insert("", "end", values=(
                    f,
                    f.split(".")[-1] if "." in f else "文件",
                    self.format_size(size),
                    path
                ))

    def on_drag_start(self, event):
        item = self.desktop_tree.identify_row(event.y)
        if item:
            self.drag_data["item"] = item

    def on_drag_motion(self, event):
        pass

    def on_drag_end(self, event):
        if not self.drag_data["item"]:
            return
        x, y = event.x_root, event.y_root
        widget_under_cursor = self.root.winfo_containing(x, y)

        for name, listbox in self.categories.items():
            if widget_under_cursor == listbox:
                values = self.desktop_tree.item(self.drag_data["item"], "values")
                if values:
                    file_path = values[3]
                    if file_path not in self.file_mapping[name]:
                        self.file_mapping[name].append(file_path)
                        listbox.insert(tk.END, values[0])
                        break

        self.drag_data["item"] = None

    def remove_item_from_category(self, event, category_name):
        """移除分类中的文件"""
        listbox = self.categories[category_name]
        selected_index = listbox.curselection()
        if selected_index:
            file_name = listbox.get(selected_index)
            listbox.delete(selected_index)
            file_path_to_remove = None
            for path in self.file_mapping[category_name]:
                if os.path.basename(path) == file_name:
                    file_path_to_remove = path
                    break
            if file_path_to_remove:
                self.file_mapping[category_name].remove(file_path_to_remove)


    def organize_files(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        error_log = []
        for category, files in self.file_mapping.items():
            target_dir = os.path.join(desktop, category)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            for file_path in files:
                try:
                    shutil.move(file_path, target_dir)
                except Exception as e:
                    error_log.append(f"移动失败: {file_path} ({str(e)})")

        if error_log:
            messagebox.showerror("操作完成（部分错误）", "\n".join(error_log))
        else:
            messagebox.showinfo("操作完成", "文件整理完成")
        self.scan_desktop()

    def open_search_window(self):
        self.search_window = tk.Toplevel(self.root)
        self.search_window.title("文件检索")
        self.search_window.geometry("600x400")

        search_frame = ttk.Frame(self.search_window)
        search_frame.pack(pady=10, fill=tk.X)

        tk.Label(search_frame, text="搜索关键字:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_files).pack(side=tk.LEFT, padx=5)

        self.search_tree = ttk.Treeview(self.search_window, columns=("name", "path"), show="headings")
        self.search_tree.heading("name", text="文件名")
        self.search_tree.heading("path", text="文件路径")
        self.search_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.status_label = ttk.Label(self.search_window, text="", foreground="gray")
        self.status_label.pack(pady=(0, 10))

    def search_files(self):
        pattern = self.search_entry.get().strip().lower()
        if not pattern:
            messagebox.showwarning("提示", "请输入搜索关键字！")
            return

        self.search_tree.delete(*self.search_tree.get_children())

        if self.status_label:
            self.status_label.config(text="🔍 正在搜索，请耐心等待...")

        threading.Thread(target=self._search_files_thread, args=(pattern,), daemon=True).start()

    def _search_files_thread(self, pattern):
        results = []
        drives = [f"{chr(d)}:/" for d in range(65, 91) if os.path.exists(f"{chr(d)}:/")]

        for drive in drives:
            for root, _, files in os.walk(drive):
                for f in files:
                    if pattern in f.lower():  # 👈 模糊匹配
                        results.append((f, os.path.join(root, f)))

        # 回到主线程更新 UI
        self.root.after(0, lambda: self._update_search_results(results))

    def _update_search_results(self, results):
        for name, path in results:
            self.search_tree.insert("", "end", values=(name, path))

        if self.status_label:
            self.status_label.config(text="")  # 清除提示

    def ai_auto_classify(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        files = []

        for f in os.listdir(desktop):
            path = os.path.join(desktop, f)
            if os.path.isfile(path):
                files.append(f)

        if not files:
            messagebox.showinfo("提示", "桌面没有可识别的文件。")
            return

        prompt = (
            "我有一些桌面文件，请你根据它们的文件名和扩展名，结合可能的使用场景，"
            "将它们按功能用途进行分类，例如：设计相关、办公文档、娱乐多媒体、软件开发、系统工具等。"
            "请返回一个 JSON 格式：{\"分类名\": [\"文件1\", \"文件2\"]}。\n\n文件列表如下：\n"
            + "\n".join(files)
        )
        messagebox.showinfo("请稍候", "AI正在分析文件，请耐心等待...")

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ZHIPU_API_KEY}"
            }

            data = {
                "model": "glm-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }

            response = requests.post("https://open.bigmodel.cn/api/paas/v4/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]

            # 使用正则尝试提取 JSON 部分
            import re
            match = re.search(r'\{[\s\S]+\}', content)
            if not match:
                raise ValueError("未能从返回结果中提取有效的 JSON")

            json_str = match.group(0)
            classification = json.loads(json_str)

            self.categories.clear()
            self.file_mapping.clear()
            for widget in self.category_container.winfo_children():
                widget.destroy()

            for cat, file_list in classification.items():
                self.add_category(cat)
                for filename in file_list:
                    full_path = os.path.join(desktop, filename)
                    if os.path.exists(full_path):
                        self.file_mapping[cat].append(full_path)
                        self.categories[cat].insert(tk.END, filename)

            messagebox.showinfo("AI分类完成", "已根据AI智能分类完成文件分组。")
        except Exception as e:
            messagebox.showerror("错误", f"AI 分类失败：{str(e)}")

    @staticmethod
    def format_size(size):
        units = ['B', 'KB', 'MB', 'GB']
        index = 0
        while size >= 1024 and index < 3:
            size /= 1024
            index += 1
        return f"{size:.1f} {units[index]}"


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartDesktopApp(root)
    root.mainloop()
