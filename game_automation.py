import cv2
import numpy as np
import pyautogui
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading

class GameAutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Automation Dashboard")
        self.root.geometry("900x600")
        
        # Variables
        self.running = False
        self.tasks = []
        self.logs = []
        self.current_screenshot = None
        
        # UI Setup
        self.setup_ui()
        
    def setup_ui(self):
        # Main Frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left Panel - Task Configuration
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Task List
        ttk.Label(left_panel, text="Task List").pack()
        self.task_tree = ttk.Treeview(left_panel, columns=('Trigger', 'Action'), show='headings')
        self.task_tree.heading('Trigger', text='Trigger Image')
        self.task_tree.heading('Action', text='Action')
        self.task_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Task Controls
        task_controls = ttk.Frame(left_panel)
        task_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(task_controls, text="Add Task", command=self.add_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(task_controls, text="Remove Task", command=self.remove_task).pack(side=tk.LEFT, padx=2)
        
        # Right Panel - Logs and Preview
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Screenshot Preview
        ttk.Label(right_panel, text="Screenshot Preview").pack()
        self.screenshot_label = ttk.Label(right_panel)
        self.screenshot_label.pack(fill=tk.BOTH, expand=True)
        
        # Logs
        ttk.Label(right_panel, text="Execution Logs").pack()
        self.log_text = tk.Text(right_panel, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Main Controls
        controls_frame = ttk.Frame(self.root)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Start", command=self.start_automation).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Stop", command=self.stop_automation).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Take Screenshot", command=self.take_screenshot).pack(side=tk.LEFT, padx=5)
        
    def add_task(self):
        # Open file dialog to select trigger image
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return
            
        # Ask for action type
        action = "click"  # Default to click, could be extended to ask user
        
        # Add to task list
        self.tasks.append({
            'trigger_image': cv2.imread(file_path, cv2.IMREAD_COLOR),
            'action': action,
            'name': file_path.split('/')[-1]
        })
        
        # Update UI
        self.task_tree.insert('', tk.END, values=(file_path.split('/')[-1], action))
        self.log(f"Added task: {file_path.split('/')[-1]} -> {action}")
        
    def remove_task(self):
        selected = self.task_tree.selection()
        if not selected:
            return
            
        # Remove from both UI and tasks list
        item = self.task_tree.item(selected[0])
        trigger_name = item['values'][0]
        
        self.task_tree.delete(selected[0])
        self.tasks = [t for t in self.tasks if t['name'] != trigger_name]
        self.log(f"Removed task: {trigger_name}")
        
    def take_screenshot(self):
        screenshot = pyautogui.screenshot()
        self.current_screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Display in UI
        img = Image.fromarray(cv2.cvtColor(self.current_screenshot, cv2.COLOR_BGR2RGB))
        img = img.resize((400, 300), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        
        self.screenshot_label.configure(image=img_tk)
        self.screenshot_label.image = img_tk
        self.log("Screenshot taken and displayed")
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        self.log_text.insert(tk.END, log_entry + "\n")
        self.log_text.see(tk.END)
        
    def start_automation(self):
        if not self.tasks:
            messagebox.showwarning("Warning", "No tasks configured")
            return
            
        if not self.current_screenshot:
            messagebox.showwarning("Warning", "Take a screenshot first")
            return
            
        self.running = True
        self.log("Automation started")
        
        # Start automation in separate thread
        threading.Thread(target=self.run_automation, daemon=True).start()
        
    def stop_automation(self):
        self.running = False
        self.log("Automation stopped")
        
    def run_automation(self):
        while self.running:
            # Take new screenshot
            screenshot = pyautogui.screenshot()
            screen_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            for task in self.tasks:
                if not self.running:
                    break
                    
                # Try to find trigger image
                result = cv2.matchTemplate(screen_img, task['trigger_image'], cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                # If found with good confidence
                if max_val > 0.8:
                    h, w = task['trigger_image'].shape[:2]
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    
                    self.log(f"Found {task['name']} at ({center_x}, {center_y})")
                    
                    # Perform action
                    if task['action'] == 'click':
                        pyautogui.click(center_x, center_y)
                        self.log(f"Clicked at ({center_x}, {center_y})")
                    elif task['action'] == 'drag':
                        # Example drag action - could be customized
                        pyautogui.dragTo(center_x + 100, center_y, duration=0.5)
                        self.log(f"Dragged from ({center_x}, {center_y})")
                    
                    # Update UI with detection
                    self.update_detection_ui(screen_img, max_loc, (w, h))
                    
            time.sleep(0.5)
            
    def update_detection_ui(self, screen_img, location, size):
        # Draw rectangle around detected area
        marked_img = screen_img.copy()
        cv2.rectangle(marked_img, location, 
                     (location[0] + size[0], location[1] + size[1]), 
                     (0, 255, 0), 2)
        
        # Convert to RGB for display
        marked_img = cv2.cvtColor(marked_img, cv2.COLOR_BGR2RGB)
        
        # Update UI
        img = Image.fromarray(marked_img)
        img = img.resize((400, 300), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        
        self.screenshot_label.configure(image=img_tk)
        self.screenshot_label.image = img_tk

if __name__ == "__main__":
    root = tk.Tk()
    app = GameAutomationApp(root)
    root.mainloop()