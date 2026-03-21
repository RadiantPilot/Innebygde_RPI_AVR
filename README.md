<div align="center">

# ⚡ IO-kort kontroll

**AUT-2606 Innebygde Systemer — UiT Norges Arktiske Universitet**

![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-c51a4a?logo=raspberrypi&logoColor=white)
![MCU](https://img.shields.io/badge/MCU-AVR128DB-0066cc?logo=microchip&logoColor=white)
![Language](https://img.shields.io/badge/GUI-Python%203-3776ab?logo=python&logoColor=white)
![Language](https://img.shields.io/badge/firmware-C-00599c?logo=c&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

*Styring av AVR-basert IO-kort fra Raspberry Pi via USART med live GUI*

</div>

---

## 📐 Arkitektur

```
┌──────────────────┐                          ┌──────────────────────┐
│   RASPBERRY PI   │    USART · 9600 baud     │     AVR128DB MCU     │
│                  │    ◄───────────────────► │                      │
│  ┌────────────┐  │    TX (GPIO14) → RX(PF5) │  LED 0-3    (PC0-3)  │
│  │ Python GUI │  │    RX (GPIO15) ← TX(PF4) │  Servo PWM  (PE0)    │
│  │ ctk + mpl  │  │    GND ──────── GND      │  ADC 12-bit (PD0)    │
│  └────────────┘  │                          │                      │
└──────────────────┘                          └──────────────────────┘
```

## 📡 Protokoll

Meldinger pakkes i `<` `>` med kommaseparerte verdier:

```
<L,nr,on_off>      LED-styring         <L,2,1>  → slå på LED 2
<S,vinkel>         Servo-posisjon      <S,90>   → sett servo til 90°
<M,0>              ADC-lesing          <M,0>    → les analog verdi
```

> AVR svarer `OK\n` for LED/Servo og en tallverdi for ADC.

## 🗂️ Prosjektstruktur

```
.
├── main.c                 # AVR firmware – kommandoparser + HW-styring
├── RPI_Oppg_7_V2.py       # RPi GUI – customtkinter + matplotlib
├── RPI_Oppg_7_V2.puml     # UML-diagram
├── requirements.txt       # Python-avhengigheter
└── README.md
```

## 🚀 Kom i gang

### Forutsetninger

| Komponent    | Krav                                    |
|--------------|-----------------------------------------|
| Raspberry Pi | Raspbian OS, Python 3.x                 |
| AVR          | AVR128DB (32-pin TQFP), UPDI-programmer |
| Tilkobling   | USART krysskobling + felles GND         |

### 1. Installer avhengigheter (RPi)

```bash
pip3 install -r requirements.txt --break-system-packages
```

### 2. Flash AVR

Kompiler, koble til ledning og last opp via Microchip Studio

### 3. Koble opp

| RPi | | AVR |
|-----|:---:|-----|
| TX (GPIO 14) | → | RX (PF5) |
| RX (GPIO 15) | ← | TX (PF4) |
| GND | ── | GND |

### 4. Kjør

```bash
python3 RPI_Oppg_7_V2.py
```

> 💡 Starter automatisk i **demo-modus** hvis seriellporten ikke er tilgjengelig.

## 🎮 GUI-funksjoner

| Funksjon | Beskrivelse |
|----------|-------------|
| 💡 **LED-styring** | Individuelle toggle-knapper med fargeindikatorer |
| 💡 **Alle av/på** | Én knapp for å sette alle LED-er samtidig |
| 💡 **LED-sekvenser** | Knight Rider · Blink alle · Annenhver |
| 🔄 **Servo** | Slider 0–180° med live vinkelanimasjon |
| 📈 **ADC enkeltlesing** | Les og vis verdi med én knapp |
| 📈 **ADC logging** | Kontinuerlig sampling med live matplotlib-graf |

## 🔧 Endringer fra original kode

<details>
<summary><b>Servo — bare 90° bevegelse</b></summary>

Originale verdier `SERVO_MIN=62`, `SERVO_MAX=125` ga pulser 1.0–2.0ms.
Mange servoer trenger 0.5–2.5ms for fulle 180°.

```diff
- #define SERVO_MIN  62
- #define SERVO_MAX  125
+ #define SERVO_MIN  31     // ~0.5ms → 0°
+ #define SERVO_MAX  156    // ~2.5ms → 180°
```

> ⚠️ Hvis servoen staller ved ytterpunktene, juster til f.eks. `40`/`145`.
</details>

<details>
<summary><b>ADC — ustabil førsteverdi + for rask sampling</b></summary>

**Problem:** Første lesing etter pause ga maks-verdi, deretter gradvis nedgang.

**Årsak:** S/H-kondensatoren fikk ikke ladet opp med 1MHz ADC-klokke.

**Fiks 1** — Tregere klokke:
```diff
- ADC0.CTRLC = ADC_PRESC_DIV4_gc;
+ ADC0.CTRLC = ADC_PRESC_DIV16_gc;    // 250kHz
```

**Fiks 2** — Dummy-lesing foran ekte lesing:
```c
uint16_t ADC0_read(void) {
    // Dummy – lader S/H-kondensatoren
    ADC0.COMMAND = ADC_STCONV_bm;
    while (!(ADC0.INTFLAGS & ADC_RESRDY_bm));
    ADC0.INTFLAGS = ADC_RESRDY_bm;
    // Ekte lesing
    ADC0.COMMAND = ADC_STCONV_bm;
    while (!(ADC0.INTFLAGS & ADC_RESRDY_bm));
    ADC0.INTFLAGS = ADC_RESRDY_bm;
    return ADC0.RES;
}
```
</details>

## ⚙️ Hardware-spesifikasjoner

| Periferi | Detaljer |
|----------|----------|
| **LED** | PC0–PC3, aktiv lav, med strømbegrensende motstander |
| **Servo** | PE0, TCA0 single-slope PWM, 50Hz (PER=1249, DIV64) |
| **ADC** | PD0 (AIN0), 12-bit, VREF=2.048V, maks input 2.048V |
| **USART** | USART2 ALT1, 9600 baud, TX=PF4, RX=PF5 |

---

<div align="center">

Laget som del av lab 7/8 i **AUT-2606** · UiT Norges Arktiske Universitet

</div>
