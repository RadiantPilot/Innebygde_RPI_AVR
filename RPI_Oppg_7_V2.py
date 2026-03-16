"""
GUI for styring av IO-kort (AVR) via USART fra Raspberry Pi.
Oppgave 7 â€“ AUT-2606 Innebygde Systemer (oppgradert)

Protokoll: <cmd,verdi>
  L,led_nr,on_off  â€“ LED-styring (0-3, 0/1)
  S,vinkel          â€“ Servo (0-180)
  M,0               â€“ Les ADC-verdi
"""

import customtkinter as ctk
import serial
import time
import math

# Matplotlib i tkinter
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---- Seriell oppsett ----
try:
    ser = serial.Serial(port='/dev/ttyS0', baudrate=9600, timeout=2)
    time.sleep(0.1)
    SERIAL_OK = True
except Exception as e:
    print(f"Kunne ikke Ã¥pne seriellport: {e}")
    print("KjÃ¸rer i demo-modus (ingen HW-tilkobling)")
    SERIAL_OK = False


def send_cmd(cmd, verdi):
    if not SERIAL_OK:
        if cmd == 'M':
            import random
            return str(random.randint(0, 4095))
        return "DEMO"
    melding = f"<{cmd},{verdi}>"
    ser.write(melding.encode())
    return ser.readline().decode().strip()


# ---- LED-klasse ----
class LED:
    def __init__(self, nr):
        self.nr = nr
        self.state = False

    def toggle(self):
        self.state = not self.state
        return send_cmd('L', f'{self.nr},{int(self.state)}')

    def set(self, on):
        self.state = bool(on)
        return send_cmd('L', f'{self.nr},{int(self.state)}')


# ---- GUI ----
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("IO-kort kontroll")
        self.geometry("520x850")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.leds = [LED(i) for i in range(4)]
        self.sekvens_aktiv = False  # for LED-sekvenser
        self.adc_logging = False    # for live ADC-graf
        self.adc_data = []
        self.adc_max_punkter = 50

        self._bygg_led_panel()
        self._bygg_servo_panel()
        self._bygg_adc_panel()
        self._bygg_status()

    # ============================================================
    # LED-panel
    # ============================================================
    def _bygg_led_panel(self):
        frame = ctk.CTkFrame(self)
        frame.pack(padx=15, pady=(15, 5), fill="x")

        ctk.CTkLabel(frame, text="LED-styring", font=("", 16, "bold")).pack(pady=(8, 4))

        # Individuelle knapper
        self.led_btns = []
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=4)

        for i in range(4):
            btn = ctk.CTkButton(
                btn_frame, text=f"LED {i}\nAV", width=90, height=50,
                fg_color="gray30",
                command=lambda idx=i: self._toggle_led(idx)
            )
            btn.grid(row=0, column=i, padx=5)
            self.led_btns.append(btn)

        # Alle av/pÃ¥ + sekvenser
        ctrl_frame = ctk.CTkFrame(frame, fg_color="transparent")
        ctrl_frame.pack(pady=(4, 8))

        ctk.CTkButton(
            ctrl_frame, text="Alle PÃ…", width=100,
            fg_color="green", hover_color="darkgreen",
            command=lambda: self._alle_led(True)
        ).grid(row=0, column=0, padx=4)

        ctk.CTkButton(
            ctrl_frame, text="Alle AV", width=100,
            fg_color="gray30",
            command=lambda: self._alle_led(False)
        ).grid(row=0, column=1, padx=4)

        self.sekv_menu = ctk.CTkOptionMenu(
            ctrl_frame, width=120,
            values=["Knight Rider", "Blink alle", "Annenhver"],
            command=self._start_sekvens
        )
        self.sekv_menu.set("Sekvens...")
        self.sekv_menu.grid(row=0, column=2, padx=4)

        self.sekv_stopp_btn = ctk.CTkButton(
            ctrl_frame, text="Stopp", width=70,
            fg_color="firebrick", hover_color="darkred",
            command=self._stopp_sekvens
        )
        self.sekv_stopp_btn.grid(row=0, column=3, padx=4)

    def _toggle_led(self, idx):
        self._stopp_sekvens()
        self.leds[idx].toggle()
        self._oppdater_led_btn(idx)
        on = self.leds[idx].state
        self._sett_status(f"LED {idx} â†’ {'PÃ…' if on else 'AV'}")

    def _alle_led(self, on):
        self._stopp_sekvens()
        for i in range(4):
            self.leds[i].set(on)
            self._oppdater_led_btn(i)
        self._sett_status(f"Alle LED â†’ {'PÃ…' if on else 'AV'}")

    def _oppdater_led_btn(self, idx):
        on = self.leds[idx].state
        self.led_btns[idx].configure(
            text=f"LED {idx}\n{'PÃ…' if on else 'AV'}",
            fg_color="green" if on else "gray30"
        )

    # ---- LED-sekvenser ----
    def _start_sekvens(self, valg):
        self._stopp_sekvens()
        self.sekvens_aktiv = True
        if valg == "Knight Rider":
            self._knight_rider(0, 1)
        elif valg == "Blink alle":
            self._blink_alle(True)
        elif valg == "Annenhver":
            self._annenhver(True)

    def _stopp_sekvens(self):
        self.sekvens_aktiv = False

    def _knight_rider(self, pos, retning):
        if not self.sekvens_aktiv:
            return
        for i in range(4):
            self.leds[i].set(i == pos)
            self._oppdater_led_btn(i)
        neste = pos + retning
        if neste > 3 or neste < 0:
            retning *= -1
            neste = pos + retning
        self.after(150, self._knight_rider, neste, retning)

    def _blink_alle(self, on):
        if not self.sekvens_aktiv:
            return
        for i in range(4):
            self.leds[i].set(on)
            self._oppdater_led_btn(i)
        self.after(300, self._blink_alle, not on)

    def _annenhver(self, fase):
        if not self.sekvens_aktiv:
            return
        for i in range(4):
            self.leds[i].set((i % 2 == 0) == fase)
            self._oppdater_led_btn(i)
        self.after(400, self._annenhver, not fase)

    # ============================================================
    # Servo-panel med visuell animasjon
    # ============================================================
    def _bygg_servo_panel(self):
        frame = ctk.CTkFrame(self)
        frame.pack(padx=15, pady=5, fill="x")

        ctk.CTkLabel(frame, text="Servo-styring", font=("", 16, "bold")).pack(pady=(8, 2))

        # Canvas for servo-visning
        self.servo_canvas = ctk.CTkCanvas(frame, width=220, height=130,
                                           bg="#2b2b2b", highlightthickness=0)
        self.servo_canvas.pack(pady=(4, 2))

        self.vinkel_label = ctk.CTkLabel(frame, text="Vinkel: 90Â°", font=("", 14))
        self.vinkel_label.pack()

        self.slider = ctk.CTkSlider(
            frame, from_=0, to=180,
            number_of_steps=180,
            command=self._slider_endret
        )
        self.slider.set(90)
        self.slider.pack(padx=20, pady=(0, 4), fill="x")

        ctk.CTkButton(
            frame, text="Send til servo",
            command=self._send_servo
        ).pack(pady=(0, 10))

        self._tegn_servo(90)

    def _tegn_servo(self, vinkel):
        c = self.servo_canvas
        c.delete("all")
        cx, cy = 110, 120  # sentrum av halvsirkel
        r = 90

        # Buebakgrunn (halvsirkel)
        c.create_arc(cx - r, cy - r, cx + r, cy + r,
                      start=0, extent=180, style="arc",
                      outline="#808080", width=2)

        # Gradmerker
        for deg in range(0, 181, 45):
            rad = math.radians(180 - deg)
            x1 = cx + (r - 8) * math.cos(rad)
            y1 = cy - (r - 8) * math.sin(rad)
            x2 = cx + (r + 2) * math.cos(rad)
            y2 = cy - (r + 2) * math.sin(rad)
            c.create_line(x1, y1, x2, y2, fill="#999999", width=1)
            xt = cx + (r + 14) * math.cos(rad)
            yt = cy - (r + 14) * math.sin(rad)
            c.create_text(xt, yt, text=str(deg), fill="#999999", font=("", 8))

        # NÃ¥l
        rad = math.radians(180 - vinkel)
        nx = cx + (r - 15) * math.cos(rad)
        ny = cy - (r - 15) * math.sin(rad)
        c.create_line(cx, cy, nx, ny, fill="#3b8ed0", width=3)
        c.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill="#3b8ed0", outline="")

    def _slider_endret(self, val):
        v = int(val)
        self.vinkel_label.configure(text=f"Vinkel: {v}Â°")
        self._tegn_servo(v)

    def _send_servo(self):
        vinkel = int(self.slider.get())
        svar = send_cmd('S', str(vinkel))
        self._sett_status(f"Servo â†’ {vinkel}Â°  (AVR: {svar})")

    # ============================================================
    # ADC-panel med live graf
    # ============================================================
    def _bygg_adc_panel(self):
        frame = ctk.CTkFrame(self)
        frame.pack(padx=15, pady=5, fill="x")

        ctk.CTkLabel(frame, text="ADC-lesing", font=("", 16, "bold")).pack(pady=(8, 2))

        self.adc_label = ctk.CTkLabel(frame, text="Verdi: â€“", font=("", 20))
        self.adc_label.pack()

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=4)

        ctk.CTkButton(
            btn_frame, text="Les Ã©n gang", width=110,
            command=self._les_adc
        ).grid(row=0, column=0, padx=5)

        self.log_btn = ctk.CTkButton(
            btn_frame, text="Start logging", width=110,
            fg_color="green", hover_color="darkgreen",
            command=self._toggle_logging
        )
        self.log_btn.grid(row=0, column=1, padx=5)

        ctk.CTkButton(
            btn_frame, text="TÃ¸m graf", width=90,
            fg_color="gray30",
            command=self._tom_graf
        ).grid(row=0, column=2, padx=5)

        # Matplotlib-figur
        self.fig = Figure(figsize=(4.8, 1.8), dpi=80, facecolor="#2b2b2b")
        self.ax = self.fig.add_subplot(111)
        self._stil_graf()

        self.canvas_fig = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas_fig.get_tk_widget().pack(padx=8, pady=(4, 10))

    def _stil_graf(self):
        ax = self.ax
        ax.set_facecolor("#2b2b2b")
        ax.tick_params(colors="#999999", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#808080")
        ax.set_ylim(0, 4200)
        ax.set_ylabel("ADC", color="#999999", fontsize=9)
        ax.set_xlabel("Samples", color="#999999", fontsize=9)

    def _oppdater_graf(self):
        self.ax.clear()
        self._stil_graf()
        if self.adc_data:
            self.ax.plot(self.adc_data, color="#3b8ed0", linewidth=1.5)
        self.canvas_fig.draw_idle()

    def _les_adc(self):
        svar = send_cmd('M', '0')
        self.adc_label.configure(text=f"Verdi: {svar}")
        try:
            self.adc_data.append(int(svar))
            if len(self.adc_data) > self.adc_max_punkter:
                self.adc_data.pop(0)
            self._oppdater_graf()
        except ValueError:
            pass
        self._sett_status(f"ADC â†’ {svar}")

    def _toggle_logging(self):
        self.adc_logging = not self.adc_logging
        if self.adc_logging:
            self.log_btn.configure(text="Stopp logging", fg_color="firebrick",
                                   hover_color="darkred")
            self._log_loop()
        else:
            self.log_btn.configure(text="Start logging", fg_color="green",
                                   hover_color="darkgreen")

    def _log_loop(self):
        if not self.adc_logging:
            return
        self._les_adc()
        self.after(500, self._log_loop)  # les hvert 500ms

    def _tom_graf(self):
        self.adc_data.clear()
        self._oppdater_graf()
        self._sett_status("ADC-graf tÃ¸mt")

    # ============================================================
    # Statuslinje
    # ============================================================
    def _bygg_status(self):
        self.status_label = ctk.CTkLabel(self, text="Klar", text_color="#999999")
        self.status_label.pack(pady=(5, 10))

    def _sett_status(self, tekst):
        self.status_label.configure(text=tekst)


if __name__ == "__main__":
    app = App()
    app.mainloop()
    if SERIAL_OK:
        ser.close()
