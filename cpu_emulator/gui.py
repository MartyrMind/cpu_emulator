from __future__ import annotations

import threading
import time
from tkinter import BOTH, END, LEFT, RIGHT, TOP, BOTTOM, X, Y
import tkinter as tk
from tkinter import filedialog, messagebox

from loguru import logger

from cpu_emulator.core.cpu import CPU
from cpu_emulator.core.program_loader import ProgramLoader
from cpu_emulator.utils.demo_programs import (
    program_array_sum,
    program_convolution,
    program_array_sum_long,
    list_demo_names,
    get_demo_by_name,
)


class CPUEmulatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Эмулятор CPU")
        self.geometry("1000x680")

        self.cpu = CPU()
        self.loader = ProgramLoader()
        self.current_source_lines: list[str] = []

        self._create_widgets()
        self._running_thread: threading.Thread | None = None
        self._stop_run_flag = threading.Event()
        # UI state helpers
        self._prev_reg_values: list[int] = [0] * 9  # R0..R7 and R8(SP)
        self._prev_flags: dict[str, int] = {}
        # Removed default label background reliance; flashing restores per-widget original bg
        self._default_entry_bg: str | None = None
        self._was_halted: bool = False

        self._refresh_ui()

    # UI setup
    def _create_widgets(self) -> None:
        # Menu bar
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Открыть…", command=self._on_load, accelerator="Ctrl+O / ⌘O")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.destroy, accelerator="Ctrl+Q / ⌘Q")
        menubar.add_cascade(label="Файл", menu=file_menu)

        run_menu = tk.Menu(menubar, tearoff=0)
        run_menu.add_command(label="Шаг", command=self._on_step, accelerator="F10")
        run_menu.add_command(label="Пуск", command=self._on_run, accelerator="F5")
        run_menu.add_command(label="Пауза", command=self._on_pause, accelerator="F6")
        run_menu.add_command(label="Сброс", command=self._on_reset, accelerator="Ctrl+R / ⌘R")
        menubar.add_cascade(label="Выполнение", menu=run_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=lambda: messagebox.showinfo("О программе", "Эмулятор CPU (Tkinter UI)"))
        menubar.add_cascade(label="Справка", menu=help_menu)
        self.config(menu=menubar)

        # Global hotkeys
        self.bind_all("<F5>", lambda e: self._on_run())
        self.bind_all("<F6>", lambda e: self._on_pause())
        self.bind_all("<F10>", lambda e: self._on_step())
        self.bind_all("<Control-r>", lambda e: self._on_reset())
        self.bind_all("<Control-o>", lambda e: self._on_load())
        self.bind_all("<Control-q>", lambda e: self.destroy())
        # macOS Command bindings
        self.bind_all("<Command-r>", lambda e: self._on_reset())
        self.bind_all("<Command-o>", lambda e: self._on_load())
        self.bind_all("<Command-q>", lambda e: self.destroy())

        # Top controls frame
        controls = tk.Frame(self)
        controls.pack(side=TOP, fill=X, padx=8, pady=8)

        self.load_btn = tk.Button(controls, text="Загрузить ASM...", command=self._on_load)
        self.load_btn.pack(side=LEFT, padx=4)

        self.reset_btn = tk.Button(controls, text="Сброс", command=self._on_reset)
        self.reset_btn.pack(side=LEFT, padx=4)

        self.step_btn = tk.Button(controls, text="Шаг", command=self._on_step)
        self.step_btn.pack(side=LEFT, padx=4)

        self.run_btn = tk.Button(controls, text="Пуск", command=self._on_run)
        self.run_btn.pack(side=LEFT, padx=4)

        self.pause_btn = tk.Button(controls, text="Пауза", command=self._on_pause)
        self.pause_btn.pack(side=LEFT, padx=4)

        # Run speed
        tk.Label(controls, text="Гц:").pack(side=LEFT, padx=(16, 4))
        self.speed_var = tk.IntVar(value=20)
        self.speed_entry = tk.Entry(controls, width=6, textvariable=self.speed_var)
        self.speed_entry.pack(side=LEFT)
        try:
            self._default_entry_bg = self.speed_entry.cget("bg")
        except Exception:
            self._default_entry_bg = None

        # Scenarios dropdown
        tk.Label(controls, text="Сценарии:").pack(side=LEFT, padx=(16, 4))
        self.scenario_var = tk.StringVar(value=list_demo_names()[0])
        self.scenario_menu = tk.OptionMenu(controls, self.scenario_var, *list_demo_names())
        self.scenario_menu.pack(side=LEFT, padx=2)
        self.load_scenario_btn = tk.Button(
            controls, text="Загрузить", command=self._on_load_scenario
        )
        self.load_scenario_btn.pack(side=LEFT, padx=2)

        # State panels
        main_panes = tk.PanedWindow(self, sashrelief=tk.RAISED)
        main_panes.pack(fill=BOTH, expand=True, padx=8, pady=(0, 8))

        left_panel = tk.Frame(main_panes)
        right_panel = tk.Frame(main_panes)
        main_panes.add(left_panel, minsize=360)
        main_panes.add(right_panel)

        # Registers and flags in left panel
        regs_frame = tk.LabelFrame(left_panel, text="Регистры")
        regs_frame.pack(side=TOP, fill=X, padx=4, pady=4)

        self.reg_hex_vars: list[tk.StringVar] = []
        self.reg_dec_vars: list[tk.StringVar] = []
        self.reg_hex_labels: list[tk.Label] = []
        self.reg_dec_labels: list[tk.Label] = []
        for i in range(9):  # R0..R7 and R8(SP)
            var_hex = tk.StringVar(value="0x00000000")
            var_dec = tk.StringVar(value="(d: 0)")
            self.reg_hex_vars.append(var_hex)
            self.reg_dec_vars.append(var_dec)
            row = tk.Frame(regs_frame)
            row.pack(fill=X)
            name = f"R{i}" if i < 8 else "R8 (SP)"
            tk.Label(row, text=f"{name}:", width=9, anchor="w").pack(side=LEFT)
            hex_lbl = tk.Label(row, textvariable=var_hex, width=12, anchor="w")
            hex_lbl.pack(side=LEFT)
            dec_lbl = tk.Label(row, textvariable=var_dec, width=16, anchor="w")
            dec_lbl.pack(side=LEFT)
            self.reg_hex_labels.append(hex_lbl)
            self.reg_dec_labels.append(dec_lbl)
            # no global bg caching needed

        special_frame = tk.LabelFrame(left_panel, text="Специальные")
        special_frame.pack(side=TOP, fill=X, padx=4, pady=4)
        self.pc_var = tk.StringVar(value="0x00000")
        self.ir_var = tk.StringVar(value="0x00000000")
        self.cycle_var = tk.StringVar(value="0")
        for label, var, width in (
            ("PC", self.pc_var, 10),
            ("IR", self.ir_var, 12),
            ("Cycles", self.cycle_var, 10),
        ):
            row = tk.Frame(special_frame)
            row.pack(fill=X)
            tk.Label(row, text=f"{label}:", width=9, anchor="w").pack(side=LEFT)
            tk.Label(row, textvariable=var, width=width, anchor="w").pack(side=LEFT)

        flags_frame = tk.LabelFrame(left_panel, text="Флаги")
        flags_frame.pack(side=TOP, fill=X, padx=4, pady=4)
        self.flag_vars: dict[str, tk.StringVar] = {}
        self.flag_labels: dict[str, tk.Label] = {}
        for flag in ["Z", "S", "C", "O", "P"]:
            var = tk.StringVar(value="0")
            self.flag_vars[flag] = var
            row = tk.Frame(flags_frame)
            row.pack(fill=X)
            tk.Label(row, text=f"{flag}:", width=9, anchor="w").pack(side=LEFT)
            fl_lbl = tk.Label(row, textvariable=var, width=4, anchor="w")
            fl_lbl.pack(side=LEFT)
            self.flag_labels[flag] = fl_lbl

        # Result panel
        result_frame = tk.LabelFrame(left_panel, text="Результат")
        result_frame.pack(side=TOP, fill=X, padx=4, pady=4)
        # R0 result
        self.result_r0_hex_var = tk.StringVar(value="0x00000000")
        self.result_r0_dec_var = tk.StringVar(value="(d: 0)")
        row = tk.Frame(result_frame)
        row.pack(fill=X)
        tk.Label(row, text="R0:", width=9, anchor="w").pack(side=LEFT)
        self.result_r0_hex_lbl = tk.Label(row, textvariable=self.result_r0_hex_var, width=12, anchor="w")
        self.result_r0_hex_lbl.pack(side=LEFT)
        self.result_r0_dec_lbl = tk.Label(row, textvariable=self.result_r0_dec_var, width=16, anchor="w")
        self.result_r0_dec_lbl.pack(side=LEFT)
        # no global bg caching needed
        # 64-bit R1:R0 view
        self.result_64_hex_var = tk.StringVar(value="0x0000000000000000")
        row64 = tk.Frame(result_frame)
        row64.pack(fill=X)
        tk.Label(row64, text="R1:R0 (64-бит):", width=16, anchor="w").pack(side=LEFT)
        self.result_64_hex_lbl = tk.Label(row64, textvariable=self.result_64_hex_var, width=20, anchor="w")
        self.result_64_hex_lbl.pack(side=LEFT)

        # Right split: Memory (left) and Source (right)
        right_split = tk.PanedWindow(right_panel, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        right_split.pack(fill=BOTH, expand=True)

        mem_side = tk.Frame(right_split)
        src_side = tk.Frame(right_split)
        right_split.add(mem_side)
        right_split.add(src_side, minsize=260)

        # Memory controls
        mem_controls = tk.Frame(mem_side)
        mem_controls.pack(side=TOP, fill=X)
        tk.Label(mem_controls, text="Базовый адрес:").pack(side=LEFT)
        self.mem_base_var = tk.StringVar(value="0x0000")
        self.mem_base_entry = tk.Entry(mem_controls, width=12, textvariable=self.mem_base_var)
        self.mem_base_entry.pack(side=LEFT, padx=4)
        tk.Button(mem_controls, text="Перейти", command=self._refresh_memory).pack(side=LEFT)
        # Rows count
        tk.Label(mem_controls, text="Строки:").pack(side=LEFT, padx=(12, 4))
        self.rows_var = tk.IntVar(value=64)
        self.rows_entry = tk.Entry(mem_controls, width=6, textvariable=self.rows_var)
        self.rows_entry.pack(side=LEFT)
        # View mode
        tk.Label(mem_controls, text="Вид:").pack(side=LEFT, padx=(12, 4))
        self.mem_view_mode = tk.StringVar(value="Words")
        tk.OptionMenu(mem_controls, self.mem_view_mode, "Words", "Bytes", command=lambda _: self._refresh_memory()).pack(side=LEFT)
        # Goto / Follow PC
        tk.Button(mem_controls, text="К PC", command=self._goto_pc).pack(side=LEFT, padx=(12, 4))
        self.follow_pc_var = tk.BooleanVar(value=False)
        tk.Checkbutton(mem_controls, text="Следовать за PC", variable=self.follow_pc_var).pack(side=LEFT)
        # Memory view with scrollbar
        mem_view = tk.Frame(mem_side)
        mem_view.pack(side=TOP, fill=BOTH, expand=True, padx=4, pady=4)
        self.mem_text = tk.Text(mem_view, height=30, width=80, font=("Courier", 10))
        scroll = tk.Scrollbar(mem_view, orient=tk.VERTICAL, command=self.mem_text.yview)
        self.mem_text.configure(state=tk.DISABLED, yscrollcommand=scroll.set)
        self.mem_text.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.pack(side=RIGHT, fill=Y)
        # Tag for highlighting current PC line
        self.mem_text.tag_configure("pc_line", background="#FFF59D")

        # Source view
        src_frame = tk.LabelFrame(src_side, text="Программа (ASM)")
        src_frame.pack(side=TOP, fill=BOTH, expand=True, padx=4, pady=4)
        src_container = tk.Frame(src_frame)
        src_container.pack(fill=BOTH, expand=True)
        self.src_text = tk.Text(src_container, height=30, width=50, font=("Courier", 10))
        src_scroll = tk.Scrollbar(src_container, orient=tk.VERTICAL, command=self.src_text.yview)
        self.src_text.configure(state=tk.DISABLED, yscrollcommand=src_scroll.set)
        self.src_text.pack(side=LEFT, fill=BOTH, expand=True)
        src_scroll.pack(side=RIGHT, fill=Y)
        self.src_text.tag_configure("src_pc_line", background="#E1F5FE")

        # Status bar
        self.status_var = tk.StringVar(value="Готово")
        status = tk.Label(self, textvariable=self.status_var, anchor="w")
        status.pack(side=BOTTOM, fill=X)

    def _set_entry_valid(self, entry: tk.Entry, valid: bool) -> None:
        try:
            if valid:
                if self._default_entry_bg is not None:
                    entry.configure(bg=self._default_entry_bg)
            else:
                entry.configure(bg="#FFEBEE")
        except Exception:
            pass

    def _flash_widgets(self, widgets: list[tk.Widget], color: str = "#FFF59D", duration_ms: int = 300) -> None:
        # Capture original backgrounds per widget to restore accurately
        original_bg: dict[tk.Widget, str] = {}
        for w in widgets:
            try:
                original_bg[w] = w.cget("background")
            except Exception:
                pass
            try:
                w.configure(background=color)
            except Exception:
                pass
        def restore():
            for w in widgets:
                try:
                    if w in original_bg:
                        w.configure(background=original_bg[w])
                except Exception:
                    pass
        self.after(duration_ms, restore)

    # Actions
    def _on_load(self) -> None:
        path = filedialog.askopenfilename(
            title="Open Assembly File",
            filetypes=[("Assembly Files", "*.asm *.s *.txt"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.rstrip("\n") for line in f.readlines()]
            machine_code = self.loader.assemble_simple(lines)
            self.cpu.reset()
            self.cpu.load_program(machine_code)
            self.current_source_lines = [line for line in lines if line.strip()]
            self._populate_source_view()
            self.status_var.set(f"Loaded {len(machine_code)} bytes from {path}")
            self._refresh_ui()
        except Exception as e:
            logger.exception("Failed to load/assemble program")
            messagebox.showerror("Load Error", str(e))

    def _on_reset(self) -> None:
        self._stop_run_flag.set()
        self.cpu.reset()
        self._refresh_ui()
        self.status_var.set("CPU reset")

    def _on_step(self) -> None:
        try:
            self.cpu.step()
            self._refresh_ui()
        except Exception as e:
            logger.exception("Step failed")
            messagebox.showerror("Step Error", str(e))

    def _on_run(self) -> None:
        if self._running_thread and self._running_thread.is_alive():
            return
        self._stop_run_flag.clear()
        try:
            hz = int(self.speed_var.get())
            if hz < 1:
                raise ValueError
        except Exception:
            self._set_entry_valid(self.speed_entry, False)
            self.status_var.set("Некорректная частота (Гц). Используйте целое >= 1.")
            return
        self._set_entry_valid(self.speed_entry, True)

        def runner():
            logger.info("Run started")
            delay = 1.0 / hz
            while not self._stop_run_flag.is_set() and not self.cpu.halted:
                try:
                    self.cpu.step()
                except Exception as e:
                    logger.exception("Run step failed")
                    self.after(0, lambda: messagebox.showerror("Run Error", str(e)))
                    break
                # Update UI in main thread
                self.after(0, self._refresh_ui)
                time.sleep(delay)
            logger.info("Run stopped")

        self._running_thread = threading.Thread(target=runner, daemon=True)
        self._running_thread.start()
        self.status_var.set("Выполнение…")
        try:
            self._update_controls_state(self.cpu.get_state())
        except Exception:
            pass

    def _on_pause(self) -> None:
        self._stop_run_flag.set()
        self.status_var.set("Пауза")
        try:
            self._update_controls_state(self.cpu.get_state())
        except Exception:
            pass

    # UI refreshers
    def _refresh_ui(self) -> None:
        state = self.cpu.get_state()
        # Registers
        for i in range(8):
            value = state["registers"][f"R{i}"] & 0xFFFFFFFF
            self.reg_hex_vars[i].set(f"0x{value:08X}")
            self.reg_dec_vars[i].set(f"(d: {value})")
            if value != self._prev_reg_values[i]:
                self._flash_widgets([self.reg_hex_labels[i], self.reg_dec_labels[i]])
                self._prev_reg_values[i] = value
        sp_val = state["registers"]["R8"] & 0xFFFFFFFF
        self.reg_hex_vars[8].set(f"0x{sp_val:08X}")
        self.reg_dec_vars[8].set(f"(d: {sp_val})")
        if sp_val != self._prev_reg_values[8]:
            self._flash_widgets([self.reg_hex_labels[8], self.reg_dec_labels[8]])
            self._prev_reg_values[8] = sp_val

        # Special
        self.pc_var.set(f"0x{state['pc']:05X}")
        # IR may not be present initially
        ir_value = getattr(self.cpu.registers, "ir", 0) & 0xFFFFFFFF
        self.ir_var.set(f"0x{ir_value:08X}")
        self.cycle_var.set(str(state["cycle_count"]))

        # Flags
        for flag, var in self.flag_vars.items():
            val = int(state["flags"].get(flag, 0))
            var.set(str(val))
            if self._prev_flags.get(flag, -1) != val:
                self._flash_widgets([self.flag_labels[flag]])
                self._prev_flags[flag] = val

        # Result values (always update; flash on halt transition)
        r0 = state["registers"]["R0"] & 0xFFFFFFFF
        r1 = state["registers"]["R1"] & 0xFFFFFFFF
        r64 = ((r1 << 32) | r0) & 0xFFFFFFFFFFFFFFFF
        self.result_r0_hex_var.set(f"0x{r0:08X}")
        self.result_r0_dec_var.set(f"(d: {r0})")
        self.result_64_hex_var.set(f"0x{r64:016X}")

        # Adjust memory base if follow PC is enabled
        try:
            pc = int(self.cpu.registers.pc)
            rows = max(1, int(self.rows_var.get()))
            base = self._parse_base_address()
            mode = self.mem_view_mode.get()
            if mode == "Bytes":
                aligned_base = base - (base % 16) if base % 16 != 0 else base
                window_start = aligned_base
                window_end = aligned_base + rows * 16
                step = 16
            else:
                aligned_base = base - (base % 4) if base % 4 != 0 else base
                window_start = aligned_base
                window_end = aligned_base + rows * 4
                step = 4
            if self.follow_pc_var.get():
                if not (window_start <= pc < window_end):
                    # Center PC in the window when possible
                    centered_base = pc - (rows // 2) * step
                    if centered_base < 0:
                        centered_base = 0
                    # Align to view granularity
                    centered_base = centered_base - (centered_base % step)
                    self.mem_base_var.set(f"0x{centered_base:04X}")
        except Exception:
            pass

        # Memory
        self._refresh_memory()
        # Source highlight
        self._refresh_source_highlight()
        # Controls state
        try:
            self._update_controls_state(state)
        except Exception:
            pass
        # Flash results on transition to halted
        try:
            if bool(state.get("halted", False)) and not self._was_halted:
                self._flash_widgets([self.result_r0_hex_lbl, self.result_r0_dec_lbl, self.result_64_hex_lbl])
                self.status_var.set("Остановлено. Результат обновлён.")
                self._was_halted = True
            elif not bool(state.get("halted", False)):
                self._was_halted = False
        except Exception:
            pass

    def _update_controls_state(self, state: dict) -> None:
        is_running_thread = self._running_thread is not None and self._running_thread.is_alive()
        is_halted = bool(state.get("halted", False))

        # Load and scenarios are disabled while running
        set_disabled_while_running = [self.load_btn, self.scenario_menu, self.load_scenario_btn]
        for btn in set_disabled_while_running:
            try:
                btn.configure(state=tk.DISABLED if is_running_thread else tk.NORMAL)
            except Exception:
                pass

        # Run/Step disabled when running or halted
        try:
            self.run_btn.configure(state=tk.DISABLED if (is_running_thread or is_halted) else tk.NORMAL)
            self.step_btn.configure(state=tk.DISABLED if (is_running_thread or is_halted) else tk.NORMAL)
        except Exception:
            pass

        # Pause enabled only when running
        try:
            self.pause_btn.configure(state=tk.NORMAL if is_running_thread else tk.DISABLED)
        except Exception:
            pass

        # Reset always enabled
        try:
            self.reset_btn.configure(state=tk.NORMAL)
        except Exception:
            pass

    def _parse_base_address(self) -> int:
        text = self.mem_base_var.get().strip()
        try:
            if text.lower().startswith("0x"):
                return int(text, 16)
            return int(text)
        except Exception:
            return 0

    def _refresh_memory(self) -> None:
        text = self.mem_base_var.get().strip()
        base_ok = True
        try:
            if text.lower().startswith("0x"):
                base = int(text, 16)
            else:
                base = int(text)
        except Exception:
            base = 0
            base_ok = False
        self._set_entry_valid(self.mem_base_entry, base_ok)
        try:
            rows_val = int(self.rows_var.get())
            rows = max(1, rows_val)
            rows_ok = rows_val >= 1
        except Exception:
            rows = 64
            rows_ok = False
        self._set_entry_valid(self.rows_entry, rows_ok)

        mode = self.mem_view_mode.get()
        self.mem_text.configure(state=tk.NORMAL)
        self.mem_text.delete("1.0", END)
        self.mem_text.tag_remove("pc_line", "1.0", END)

        if mode == "Bytes":
            # Hex dump of bytes with ASCII, 16 bytes per row
            aligned_base = base - (base % 16) if base % 16 != 0 else base
            lines: list[str] = []
            for row in range(rows):
                row_addr = (aligned_base + row * 16) & 0xFFFFFFFF
                hex_bytes: list[str] = []
                ascii_chars: list[str] = []
                for i in range(16):
                    addr = row_addr + i
                    try:
                        b = self.cpu.memory.read_byte(addr)
                        hex_bytes.append(f"{b:02X}")
                        ascii_chars.append(chr(b) if 32 <= b < 127 else ".")
                    except Exception:
                        hex_bytes.append("??")
                        ascii_chars.append(".")
                hex_part = " ".join(hex_bytes)
                ascii_part = "".join(ascii_chars)
                lines.append(f"0x{row_addr:05X}: {hex_part:<47}  {ascii_part}")

            self.mem_text.insert("1.0", "\n".join(lines))

            # Highlight current PC row if within window
            try:
                pc = int(self.cpu.registers.pc)
                if aligned_base <= pc < aligned_base + rows * 16:
                    line_no = ((pc - aligned_base) // 16) + 1
                    self.mem_text.tag_add("pc_line", f"{line_no}.0", f"{line_no}.end")
            except Exception:
                pass

        else:
            # Words view: one 32-bit word per row (hex only)
            aligned_base = base - (base % 4) if base % 4 != 0 else base
            lines: list[str] = []
            for row in range(rows):
                addr = (aligned_base + row * 4) & 0xFFFFFFFF
                try:
                    word = self.cpu.memory.read_word(addr)
                    lines.append(f"0x{addr:05X}: 0x{word:08X}")
                except Exception as e:
                    lines.append(f"0x{addr:05X}: <err>")

            self.mem_text.insert("1.0", "\n".join(lines))

            # Highlight the PC's word line if within window
            try:
                pc = int(self.cpu.registers.pc)
                if aligned_base <= pc < aligned_base + rows * 4 and pc % 4 == 0:
                    line_no = ((pc - aligned_base) // 4) + 1
                    self.mem_text.tag_add("pc_line", f"{line_no}.0", f"{line_no}.end")
            except Exception:
                pass

        self.mem_text.configure(state=tk.DISABLED)

    def _populate_source_view(self) -> None:
        lines = self.current_source_lines
        self.src_text.configure(state=tk.NORMAL)
        self.src_text.delete("1.0", END)
        formatted: list[str] = []
        for i, line in enumerate(lines):
            addr = i * 4
            formatted.append(f"0x{addr:05X}: {line}")
        self.src_text.insert("1.0", "\n".join(formatted))
        self.src_text.configure(state=tk.DISABLED)

    def _refresh_source_highlight(self) -> None:
        self.src_text.configure(state=tk.NORMAL)
        self.src_text.tag_remove("src_pc_line", "1.0", END)
        try:
            pc = int(self.cpu.registers.pc)
            line_index = (pc // 4) + 1
            total_lines = int(self.src_text.index('end-1c').split('.')[0])
            if 1 <= line_index <= total_lines:
                start_idx = f"{line_index}.0"
                end_idx = f"{line_index}.end"
                self.src_text.tag_add("src_pc_line", start_idx, end_idx)
                # Optional: scroll into view
                self.src_text.see(start_idx)
        except Exception:
            pass
        self.src_text.configure(state=tk.DISABLED)

    def _goto_pc(self) -> None:
        try:
            pc = int(self.cpu.registers.pc)
            rows = max(1, int(self.rows_var.get()))
            mode = self.mem_view_mode.get()
            step = 16 if mode == "Bytes" else 4
            # Center PC in view where possible
            base = pc - (rows // 2) * step
            if base < 0:
                base = 0
            base = base - (base % step)
            self.mem_base_var.set(f"0x{base:04X}")
            self._refresh_memory()
        except Exception:
            pass

    # Built-in scenarios
    def _scenario_sum(self) -> None:
        """Load and run array sum scenario."""
        program_assembly = program_array_sum()
        try:
            machine_code = self.loader.assemble_simple(program_assembly)
            self.cpu.reset()
            self.cpu.load_program(machine_code)
            self.current_source_lines = program_assembly
            self._populate_source_view()
            self.status_var.set("Сценарий 'Сумма массива' загружен. Нажмите Run для запуска.")
            self._refresh_ui()
        except Exception as e:
            logger.exception("Scenario sum failed")
            messagebox.showerror("Scenario Error", str(e))

    def _scenario_convolution(self) -> None:
        """Load and run convolution scenario."""
        program_assembly = program_convolution()
        try:
            machine_code = self.loader.assemble_simple(program_assembly)
            self.cpu.reset()
            self.cpu.load_program(machine_code)
            self.current_source_lines = program_assembly
            self._populate_source_view()
            self.status_var.set("Сценарий 'Свертка массивов' загружен. Нажмите Run для запуска.")
            self._refresh_ui()
        except Exception as e:
            logger.exception("Scenario convolution failed")
            messagebox.showerror("Scenario Error", str(e))

    def _scenario_sum_long(self) -> None:
        """Load and run 64-bit array sum scenario (R1:R0)."""
        program_assembly = program_array_sum_long()
        try:
            machine_code = self.loader.assemble_simple(program_assembly)
            self.cpu.reset()
            self.cpu.load_program(machine_code)
            self.current_source_lines = program_assembly
            self._populate_source_view()
            self.status_var.set("Сценарий 'Сумма массива (64-бит)' загружен. Нажмите Пуск для запуска.")
            self._refresh_ui()
        except Exception as e:
            logger.exception("Scenario sum64 failed")
            messagebox.showerror("Scenario Error", str(e))

    def _on_load_scenario(self) -> None:
        try:
            name = self.scenario_var.get()
            program_assembly = get_demo_by_name(name)
            machine_code = self.loader.assemble_simple(program_assembly)
            self.cpu.reset()
            self.cpu.load_program(machine_code)
            self.current_source_lines = program_assembly
            self._populate_source_view()
            self.status_var.set(f"Сценарий '{name}' загружен. Нажмите Пуск для запуска.")
            self._refresh_ui()
        except Exception as e:
            logger.exception("Scenario load failed")
            messagebox.showerror("Scenario Error", str(e))


def run_gui() -> None:
    app = CPUEmulatorApp()
    app.mainloop()


