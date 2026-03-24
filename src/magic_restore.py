import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading 

# 🚨 AI 라이브러리 강제 호출
import torch
from diffusers import StableDiffusionInpaintPipeline

class MagicRestorer:
    def __init__(self, root):
        self.root = root
        self.root.title("Magic Restore Pro")
        self.root.geometry("1200x800")

        # ==========================================
        # 1. 초기 설정 변수
        # ==========================================
        self.brush_size = 10        
        self.zoom_scale = 1.0       
        self.history = []           
        self.is_panning = False     
        self.is_processing = False  
        
        self.ENABLE_SMART_PATCH = False 
        self.pipe = None 
        
        # 딥러닝 모델 백그라운드 로딩 시작
        if self.ENABLE_SMART_PATCH:
            threading.Thread(target=self.load_ai_model, daemon=True).start()

        self.mouse_x = 0
        self.mouse_y = 0
        self.last_x = None
        self.last_y = None

        self.clone_src_x = None
        self.clone_src_y = None
        self.clone_offset_x = 0
        self.clone_offset_y = 0
        self.clone_base_img = None

        self.inpaint_mode = cv2.INPAINT_NS
        self.mode_name = "NS 복원 (선/스크래치용)"
        self.mode_desc = "💡 추천: 길게 긁힌 상처, 구겨진 선. (스페이스바로 실행)"

        self.cv_img = None          
        self.cv_mask = None         

        # ==========================================
        # 2. UI 레이아웃 
        # ==========================================
        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.frame, bg="#2b2b2b")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.v_scroll = tk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        
        self.h_scroll = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scroll.grid(row=1, column=0, sticky="ew")

        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

        self.info_var = tk.StringVar()
        self.info_label = tk.Label(self.frame, textvariable=self.info_var, bg="#1a1a1a", fg="#00FF00", font=("Malgun Gothic", 11, "bold"), pady=8)
        self.info_label.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.update_info_panel()

        try:
            self.canvas.config(cursor="none")
        except:
            self.canvas.config(cursor="crosshair") 

        # ==========================================
        # 3. 이벤트 연결
        # ==========================================
        self.canvas.bind("<Motion>", self.on_mouse_move)     
        self.canvas.bind("<Button-1>", self.on_mouse_down)   
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)  
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Button-3>", self.set_clone_source)

        root.bind_all("<Control-z>", self.undo)            
        root.bind_all("<space>", self.run_restore)         
        root.bind_all("<Key>", self.handle_keypress)
        root.bind_all("<plus>", self.zoom_in)
        root.bind_all("<equal>", self.zoom_in) 
        root.bind_all("<minus>", self.zoom_out)
        root.bind_all("<Control-MouseWheel>", self.on_wheel)

        self.load_image()

    # ==========================================
    # 🌟 AI 모델 로딩 (백그라운드)
    # ==========================================
    def load_ai_model(self):
        try:
            print("🚀 [시스템] GPU 가속 AI 모델 예열 중... (창은 바로 뜹니다)")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model_id = "saik0s/realistic_vision_inpainting"
            
            self.pipe = StableDiffusionInpaintPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                use_safetensors=True,
                safety_checker=None
            ).to(device)
            
            if device == "cuda":
                self.pipe.enable_attention_slicing()
            print(f"✅ [준비 완료] NVIDIA GPU({device}) 엔진 장착 완료!")
        except Exception as e:
            print(f"❌ AI 모델 로딩 실패: {e}")
            self.pipe = "ERROR"

    def update_title(self):
        if self.cv_img is None: return
        zoom_pct = int(self.zoom_scale * 100)
        self.root.title(f"Magic Restore Pro - [붓 크기: {self.brush_size}]  [확대: {zoom_pct}%]")

    def update_info_panel(self):
        text = f" [{self.mode_name}] : {self.mode_desc}   ( M키로 기능 변경 )"
        self.info_var.set(text)

    def handle_keypress(self, event):
        if self.is_processing: return "break" 
        char = event.char
        if not char: return 
        if event.state & 0x0004: return 

        if char in ['m', 'M', 'ㅡ']:
            self.toggle_mode()
        elif char in ['z', 'Z', 'ㅋ']:
            self.decrease_brush()
        elif char in ['x', 'X', 'ㅌ']:
            self.increase_brush()
        elif char in ['r', 'R', 'ㄱ']:
            self.reset_image()
        elif char in ['s', 'S', 'ㄴ']:
            self.save_image()

    # ==========================================
    # 4. 파일 입출력 및 화면 갱신
    # ==========================================
    def load_image(self):
        if self.is_processing: return
        file_path = filedialog.askopenfilename(title="복원할 사진을 선택하세요")
        if not file_path:
            self.root.destroy()
            return
        
        stream = open(file_path.encode("utf-8"), "rb")
        bytes = bytearray(stream.read())
        numpyarray = np.asarray(bytes, dtype=np.uint8)
        self.cv_img = cv2.imdecode(numpyarray, cv2.IMREAD_UNCHANGED)

        h, w = self.cv_img.shape[:2]
        if w > 2000:
            scale = 2000 / w
            self.cv_img = cv2.resize(self.cv_img, (2000, int(h*scale)))

        self.cv_mask = np.zeros(self.cv_img.shape[:2], dtype=np.uint8)
        self.history = [] 
        self.last_x, self.last_y = None, None
        
        self.refresh_canvas()
        self.canvas.focus_set() 
        
        msg = "✅ 사진을 불러왔습니다!\n\n[조작법]\nM : 기능 변경 (NS/Telea/도장툴/Smart Patch)\nZ, X : 붓 크기 조절\n스페이스바 : 복원 실행\n우클릭 : 도장툴 원본 지정\nShift+클릭 : 직선 긋기"
        messagebox.showinfo("Magic Restore Pro", msg)

    def refresh_canvas(self):
        h, w = self.cv_img.shape[:2]
        new_w = int(w * self.zoom_scale)
        new_h = int(h * self.zoom_scale)
        
        resized_img = cv2.resize(self.cv_img, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
        
        if np.any(self.cv_mask):
            resized_mask = cv2.resize(self.cv_mask, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
            resized_img[resized_mask > 0] = [0, 0, 255] 

        img_rgb = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
        self.pil_img = Image.fromarray(img_rgb)
        self.tk_img = ImageTk.PhotoImage(self.pil_img)

        self.canvas.delete("overlay") 
        
        if not hasattr(self, 'img_id'):
            self.img_id = self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")
        else:
            self.canvas.itemconfig(self.img_id, image=self.tk_img)
        
        if self.inpaint_mode == "CLONE" and self.clone_src_x is not None:
            cx = self.clone_src_x * self.zoom_scale
            cy = self.clone_src_y * self.zoom_scale
            r = self.brush_size * self.zoom_scale
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="black", width=2, tags="overlay")
            self.canvas.create_line(cx - r - 5, cy, cx + r + 5, cy, fill="black", width=2, tags="overlay")
            self.canvas.create_line(cx, cy - r - 5, cx, cy + r + 5, fill="black", width=2, tags="overlay")

        self.canvas.config(scrollregion=(0, 0, new_w, new_h))
        self.update_title()
        
        if not self.is_processing:
            self.draw_brush_cursor() 

    # ==========================================
    # 5. 마우스 조작 및 도장툴(Clone) 로직
    # ==========================================
    def draw_brush_cursor(self):
        self.canvas.delete("cursor_brush")
        if self.is_panning or self.is_processing: return 
        
        r = self.brush_size * self.zoom_scale
        x, y = self.mouse_x, self.mouse_y
        
        self.canvas.create_oval(x - r, y - r, x + r, y + r, outline="white", width=1, tags="cursor_brush")
        self.canvas.create_oval(x - r - 1, y - r - 1, x + r + 1, y + r + 1, outline="black", width=1, tags="cursor_brush")
                                
        if self.inpaint_mode == cv2.INPAINT_NS:
            self.canvas.create_line(x - 3, y + 3, x + 3, y - 3, fill="white", width=2, tags="cursor_brush")
        elif self.inpaint_mode == cv2.INPAINT_TELEA:
            self.canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill="white", outline="white", tags="cursor_brush")
        elif self.inpaint_mode == "CLONE":
            self.canvas.create_line(x - 5, y, x + 5, y, fill="white", tags="cursor_brush")
            self.canvas.create_line(x, y - 5, x, y + 5, fill="white", tags="cursor_brush")
        elif self.inpaint_mode == "SMART":
            self.canvas.create_text(x, y, text="★", fill="yellow", font=("Arial", max(8, int(r))), tags="cursor_brush")

    def on_mouse_move(self, event):
        self.mouse_x = self.canvas.canvasx(event.x)
        self.mouse_y = self.canvas.canvasy(event.y)
        self.draw_brush_cursor()

    def set_clone_source(self, event):
        if self.is_processing: return
        self.canvas.focus_set() 
        if self.inpaint_mode != "CLONE": return
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        self.clone_src_x = int(canvas_x / self.zoom_scale)
        self.clone_src_y = int(canvas_y / self.zoom_scale)
        self.refresh_canvas()

    def push_history(self):
        if len(self.history) > 15:
            self.history.pop(0)
        self.history.append((self.cv_img.copy(), self.cv_mask.copy()))

    def paint_point(self, real_x, real_y):
        cv2.circle(self.cv_mask, (real_x, real_y), self.brush_size, 255, -1)
        cx, cy = real_x * self.zoom_scale, real_y * self.zoom_scale
        r = self.brush_size * self.zoom_scale
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="red", outline="red", tags="overlay")

    def paint_line(self, x1, y1, x2, y2):
        cv2.line(self.cv_mask, (x1, y1), (x2, y2), 255, thickness=self.brush_size * 2)
        cv2.circle(self.cv_mask, (x1, y1), self.brush_size, 255, -1)
        cv2.circle(self.cv_mask, (x2, y2), self.brush_size, 255, -1)
        
        cx1, cy1 = x1 * self.zoom_scale, y1 * self.zoom_scale
        cx2, cy2 = x2 * self.zoom_scale, y2 * self.zoom_scale
        r = self.brush_size * self.zoom_scale
        self.canvas.create_line(cx1, cy1, cx2, cy2, fill="red", width=r*2, capstyle=tk.ROUND, tags="overlay")

    def paint_clone(self, real_x, real_y, refresh=True):
        if self.clone_base_img is None or self.clone_src_x is None: return
        
        h, w = self.cv_img.shape[:2]
        radius = self.brush_size
        
        t_y1, t_y2 = max(0, real_y - radius), min(h, real_y + radius)
        t_x1, t_x2 = max(0, real_x - radius), min(w, real_x + radius)
        
        s_y1, s_y2 = t_y1 - self.clone_offset_y, t_y2 - self.clone_offset_y
        s_x1, s_x2 = t_x1 - self.clone_offset_x, t_x2 - self.clone_offset_x
        
        if s_x1 < 0: diff = -s_x1; s_x1 = 0; t_x1 += diff
        if s_y1 < 0: diff = -s_y1; s_y1 = 0; t_y1 += diff
        if s_x2 > w: diff = s_x2 - w; s_x2 = w; t_x2 -= diff
        if s_y2 > h: diff = s_y2 - h; s_y2 = h; t_y2 -= diff
            
        if t_x1 < t_x2 and t_y1 < t_y2:
            patch_mask = np.zeros((t_y2 - t_y1, t_x2 - t_x1), dtype=np.uint8)
            cv2.circle(patch_mask, (real_x - t_x1, real_y - t_y1), radius, 255, -1)
            
            src_patch = self.clone_base_img[s_y1:s_y2, s_x1:s_x2]
            tgt_patch = self.cv_img[t_y1:t_y2, t_x1:t_x2]
            
            np.copyto(tgt_patch, src_patch, where=(patch_mask[:,:,None] == 255))
            
            if refresh:
                self.refresh_canvas()

    def paint_clone_line(self, x1, y1, x2, y2):
        dist = int(np.hypot(x2 - x1, y2 - y1))
        step = max(1, int(self.brush_size / 3)) 
        
        if dist == 0:
            self.paint_clone(x2, y2, refresh=True)
            return
            
        for i in range(0, dist + 1, step):
            t = i / dist
            x = int(x1 + t * (x2 - x1))
            y = int(y1 + t * (y2 - y1))
            self.paint_clone(x, y, refresh=False) 
            
        self.paint_clone(x2, y2, refresh=False)
        self.refresh_canvas() 

    def on_mouse_down(self, event):
        if self.is_processing: return "break"
        self.canvas.focus_set() 
        if event.state & 0x0004: 
            self.canvas.scan_mark(event.x, event.y)
            self.is_panning = True
            self.canvas.config(cursor="fleur")
            self.draw_brush_cursor()
            return

        self.is_panning = False
        self.push_history() 
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        real_x = int(canvas_x / self.zoom_scale)
        real_y = int(canvas_y / self.zoom_scale)

        is_shift = bool(event.state & 0x0001) 

        if self.inpaint_mode == "CLONE":
            if self.clone_src_x is None:
                messagebox.showwarning("도장툴 안내", "우클릭으로 깨끗한 원본 위치를 먼저 찍어주세요!")
                return
            
            if is_shift and self.last_x is not None and self.last_y is not None:
                pass 
            else:
                self.clone_offset_x = real_x - self.clone_src_x
                self.clone_offset_y = real_y - self.clone_src_y
                
            self.clone_base_img = self.cv_img.copy()
            
            if is_shift and self.last_x is not None and self.last_y is not None:
                self.paint_clone_line(self.last_x, self.last_y, real_x, real_y)
            else:
                self.paint_clone(real_x, real_y)
        else:
            if is_shift and self.last_x is not None and self.last_y is not None:
                self.paint_line(self.last_x, self.last_y, real_x, real_y)
            else:
                self.paint_point(real_x, real_y)
        
        self.last_x, self.last_y = real_x, real_y

    def on_mouse_drag(self, event):
        if self.is_processing: return "break"
        self.mouse_x = self.canvas.canvasx(event.x)
        self.mouse_y = self.canvas.canvasy(event.y)
        
        if self.is_panning:
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            self.draw_brush_cursor()
            return
            
        real_x = int(self.mouse_x / self.zoom_scale)
        real_y = int(self.mouse_y / self.zoom_scale)

        if self.inpaint_mode == "CLONE":
            if self.last_x is not None and self.last_y is not None:
                self.paint_clone_line(self.last_x, self.last_y, real_x, real_y)
            else:
                self.paint_clone(real_x, real_y)
        else:
            if self.last_x is not None and self.last_y is not None:
                self.paint_line(self.last_x, self.last_y, real_x, real_y)
            else:
                self.paint_point(real_x, real_y)
                
        self.last_x, self.last_y = real_x, real_y
        self.draw_brush_cursor()

    def on_mouse_up(self, event):
        if self.is_panning:
            self.is_panning = False
            try:
                self.canvas.config(cursor="none")
            except:
                self.canvas.config(cursor="crosshair")
            self.draw_brush_cursor()

    # ==========================================
    # 6. 기능 (복원, 취소, 모드변경)
    # ==========================================
    def run_restore(self, event=None):
        if self.is_processing: return "break"
        if self.inpaint_mode == "CLONE": return "break" 
        if not np.any(self.cv_mask): return "break"

        self.is_processing = True
        
        # 🚨 모든 모드에서 공통적으로 작업 중에는 모래시계(로딩 커서)로 변경
        self.canvas.config(cursor="watch")
        
        # 🚨 Smart Patch 모드일 때만 큰 로딩 안내창 띄우기
        if self.inpaint_mode == "SMART":
            w = int(self.cv_img.shape[1] * self.zoom_scale)
            h = int(self.cv_img.shape[0] * self.zoom_scale)
            self.canvas.create_rectangle((w/2)-200, (h/2)-30, (w/2)+200, (h/2)+30, fill="black", stipple="gray50", tags="overlay")
            self.canvas.create_text(w/2, h/2, text="🚀 GPU 딥러닝 텍스처 생성 중... (잠시 대기)", fill="yellow", font=("Malgun Gothic", 16, "bold"), tags="overlay")
            
        self.root.update() 
        self.push_history() 

        def process_inpaint():
            radius = max(3, self.brush_size)
            try:
                if self.inpaint_mode in [cv2.INPAINT_NS, cv2.INPAINT_TELEA]:
                    restored = cv2.inpaint(self.cv_img, self.cv_mask, radius, self.inpaint_mode)
                    self.cv_img = restored
                    
                elif self.inpaint_mode == "SMART" and self.pipe is not None and self.pipe != "ERROR":
                    original_h, original_w = self.cv_img.shape[:2]
                    ratio = 512 / max(original_h, original_w)
                    new_h, new_w = int(original_h * ratio), int(original_w * ratio)
                    new_h, new_w = new_h - (new_h % 8), new_w - (new_w % 8)
                    
                    small_img = cv2.resize(self.cv_img, (new_w, new_h))
                    small_mask = cv2.resize(self.cv_mask, (new_w, new_h))

                    image_pil = Image.fromarray(cv2.cvtColor(small_img, cv2.COLOR_BGR2RGB))
                    mask_pil = Image.fromarray(small_mask)
                    
                    prompt = "restore missing part, realistic photo, high resolution, detailed texture, seamless blending"
                    negative_prompt = "cartoon, low quality, blur, distortion, ugly, artificial"

                    result_pil = self.pipe(
                        prompt=prompt, 
                        image=image_pil, 
                        mask_image=mask_pil,
                        negative_prompt=negative_prompt,
                        num_inference_steps=25 
                    ).images[0]

                    result_cv = cv2.cvtColor(np.array(result_pil), cv2.COLOR_RGB2BGR)
                    restored_patch = cv2.resize(result_cv, (original_w, original_h), interpolation=cv2.INTER_LANCZOS4)
                    
                    np.copyto(self.cv_img, restored_patch, where=(self.cv_mask[:,:,None] > 0))
                else:
                    self.cv_img = cv2.inpaint(self.cv_img, self.cv_mask, radius, cv2.INPAINT_NS)
                    
            except Exception as e:
                print(f"에러 발생: {e}")
            
            # 실행했던 모드를 기억해서 마무리 함수로 넘김
            self.root.after(0, lambda: self.finish_restore(self.inpaint_mode))

        threading.Thread(target=process_inpaint, daemon=True).start()
        return "break" 

    def finish_restore(self, executed_mode):
        self.cv_mask[:] = 0 
        self.is_processing = False 
        self.refresh_canvas() 
        
        # 🚨 Smart Patch 였을 때만 텍스트 피드백 표시! 그 외엔 조용히 모래시계 해제
        if executed_mode == "SMART":
            mouse_x = self.root.winfo_pointerx() - self.canvas.winfo_rootx()
            mouse_y = self.root.winfo_pointery() - self.canvas.winfo_rooty()
            msg_id = self.canvas.create_text(mouse_x, mouse_y - 40, text="✨ 텍스처 복원 완료!", fill="#00FF00", font=("Arial", 16, "bold"), tags="overlay")
            self.root.after(1000, lambda: self.canvas.delete(msg_id))
            
        try:
            self.canvas.config(cursor="none")
        except:
            self.canvas.config(cursor="crosshair")
            
        self.draw_brush_cursor()

    def undo(self, event=None):
        if self.is_processing: return "break"
        if not self.history:
            return "break"
        self.last_x, self.last_y = None, None
        prev_img, prev_mask = self.history.pop()
        self.cv_img = prev_img
        self.cv_mask = prev_mask
        self.refresh_canvas()
        return "break"

    def toggle_mode(self, event=None):
        if self.is_processing: return "break"
        self.last_x, self.last_y = None, None
        
        if np.any(self.cv_mask):
            self.cv_mask[:] = 0
            
        if self.inpaint_mode == cv2.INPAINT_NS:
            self.inpaint_mode = cv2.INPAINT_TELEA
            self.mode_name = "Telea 복원 (점/얼룩용)"
            self.mode_desc = "💡 추천: 동그란 곰팡이, 물방울, 얼룩. (스페이스바로 실행)"
            
        elif self.inpaint_mode == cv2.INPAINT_TELEA:
            self.inpaint_mode = "CLONE"
            self.mode_name = "도장툴 (직접 복사/붙여넣기)"
            self.mode_desc = "💡 추천: 패턴 복사. (우클릭으로 복사할 곳 지정 후 좌클릭 칠하기)"
            
        elif self.inpaint_mode == "CLONE":
            if self.ENABLE_SMART_PATCH:
                self.inpaint_mode = "SMART"
                self.mode_name = "Smart Patch (딥러닝 텍스처 재생성)"
                self.mode_desc = "🌟 VIP 전용: 찢어진 넓은 부위를 AI가 분석하여 완벽하게 새로 그려냅니다!"
            else:
                self.inpaint_mode = cv2.INPAINT_NS
                self.mode_name = "NS 복원 (선/스크래치용)"
                self.mode_desc = "💡 추천: 길게 긁힌 상처, 구겨진 선. (스페이스바로 실행)"
                
        elif self.inpaint_mode == "SMART":
            self.inpaint_mode = cv2.INPAINT_NS
            self.mode_name = "NS 복원 (선/스크래치용)"
            self.mode_desc = "💡 추천: 길게 긁힌 상처, 구겨진 선. (스페이스바로 실행)"
            
        self.update_info_panel() 
        self.update_title()
        self.refresh_canvas()
        
        return "break" 

    def reset_image(self, event=None):
        if self.is_processing: return "break"
        if messagebox.askyesno("초기화", "모든 작업을 취소하고 처음으로 돌아갈까요?"):
            self.load_image() 

    def zoom_in(self, event=None):
        if self.is_processing: return "break"
        self.zoom_scale += 0.2
        self.refresh_canvas()
        return "break"

    def zoom_out(self, event=None):
        if self.is_processing: return "break"
        if self.zoom_scale > 0.4:
            self.zoom_scale -= 0.2
            self.refresh_canvas()
        return "break"

    def on_wheel(self, event):
        if event.delta > 0: self.zoom_in()
        else: self.zoom_out()

    def increase_brush(self, event=None):
        if self.is_processing: return "break"
        self.brush_size += 1
        self.update_title()
        self.refresh_canvas() 
        return "break"

    def decrease_brush(self, event=None):
        if self.is_processing: return "break"
        if event and hasattr(event, 'state') and (event.state & 0x0004): 
            return "break"
            
        if self.brush_size > 1:
            self.brush_size -= 1
        self.update_title()
        self.refresh_canvas()
        return "break"

    def save_image(self, event=None):
        if self.is_processing: return "break"
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if path:
            cv2.imwrite(path, self.cv_img)
            messagebox.showinfo("저장", "성공적으로 저장되었습니다!")

if __name__ == "__main__":
    root = tk.Tk()
    app = MagicRestorer(root)
    root.mainloop()