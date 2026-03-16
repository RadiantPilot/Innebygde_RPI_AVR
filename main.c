#define F_CPU 4000000UL
#include <avr/io.h>
#include <util/delay.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define BAUD_RATE 9600
#define USART_BAUD_VALUE ((uint16_t)((float)F_CPU * 64 / (16 * (float)BAUD_RATE) + 0.5))

/* Utvidet servo-område for fulle 180 grader
   31 ? 0.5ms puls ? 0°
   156 ? 2.5ms puls ? 180°
   Juster forsiktig hvis servoen staller */
#define SERVO_MIN  31
#define SERVO_MAX  156

/* ---- USART2 (ALT1: TX=PF4, RX=PF5) ---- */
void USART2_init(void) {
	PORTMUX.USARTROUTEA = PORTMUX_USART2_ALT1_gc;
	PORTF.OUT |= PIN4_bm;
	PORTF.DIR |= PIN4_bm;
	PORTF.DIR &= ~PIN5_bm;
	USART2.BAUD  = USART_BAUD_VALUE;
	USART2.CTRLB = USART_TXEN_bm | USART_RXEN_bm;
}

void USART2_sendChar(char c) {
	while (!(USART2.STATUS & USART_DREIF_bm));
	USART2.TXDATAL = c;
}

void USART2_sendString(const char *str) {
	while (*str) USART2_sendChar(*str++);
}

char USART2_receiveChar(void) {
	while (!(USART2.STATUS & USART_RXCIF_bm));
	return USART2.RXDATAL;
}

/* ---- ADC (PD0 = AIN0) ---- */
void ADC0_init(void) {
	VREF.ADC0REF = VREF_REFSEL_2V048_gc;
	PORTD.PIN0CTRL = PORT_ISC_INPUT_DISABLE_gc;
	ADC0.CTRLC = ADC_PRESC_DIV16_gc;  /* Tregere klokke: 250kHz (var 1MHz) */
	ADC0.CTRLA = ADC_ENABLE_bm | ADC_RESSEL_12BIT_gc;
	ADC0.MUXPOS = ADC_MUXPOS_AIN0_gc;
}

uint16_t ADC0_read(void) {
	/* Dummy-lesing: lader opp S/H-kondensatoren */
	ADC0.COMMAND = ADC_STCONV_bm;
	while (!(ADC0.INTFLAGS & ADC_RESRDY_bm));
	ADC0.INTFLAGS = ADC_RESRDY_bm;

	/* Ekte lesing */
	ADC0.COMMAND = ADC_STCONV_bm;
	while (!(ADC0.INTFLAGS & ADC_RESRDY_bm));
	ADC0.INTFLAGS = ADC_RESRDY_bm;
	return ADC0.RES;
}

/* ---- LED (PC0-PC3, aktiv lav) ---- */
void LED_init(void) {
	PORTC.DIR |= PIN0_bm | PIN1_bm | PIN2_bm | PIN3_bm;
	PORTC.OUT |= PIN0_bm | PIN1_bm | PIN2_bm | PIN3_bm;
}

void LED_set(int led, int on) {
	if (led < 0 || led > 3) return;
	uint8_t pin = (1 << led);
	if (on) PORTC.OUT &= ~pin;
	else    PORTC.OUT |=  pin;
}

/* ---- Servo (TCA0, WO0 ? PE0) ---- */
void TCA0_init_SERVO(void) {
	PORTMUX.TCAROUTEA = PORTMUX_TCA0_PORTE_gc;
	PORTE.DIRSET = PIN0_bm;
	PORTE.PIN0CTRL |= PORT_INVEN_bm;

	TCA0.SINGLE.CTRLB = TCA_SINGLE_WGMODE_SINGLESLOPE_gc
	                   | TCA_SINGLE_CMP0EN_bm;
	TCA0.SINGLE.PER   = 1249;
	TCA0.SINGLE.CMP0  = (SERVO_MIN + SERVO_MAX) / 2;
	TCA0.SINGLE.CNT   = 0;
	TCA0.SINGLE.CTRLA = TCA_SINGLE_CLKSEL_DIV64_gc | TCA_SINGLE_ENABLE_bm;
}

void Servo_set(int grader) {
	if (grader < 0)   grader = 0;
	if (grader > 180) grader = 180;
	uint16_t ticks = SERVO_MIN + ((SERVO_MAX - SERVO_MIN) * (uint32_t)grader) / 180;
	TCA0.SINGLE.CMP0BUF = ticks;
}

/* ---- Parser ---- */
int les_melding(char *cmd, int *verdi1, int *verdi2) {
	char buf[16];
	uint8_t i = 0;
	char c;

	do { c = USART2_receiveChar(); } while (c != '<');

	while (1) {
		c = USART2_receiveChar();
		if (c == '>') break;
		if (i < 15) buf[i++] = c;
	}
	buf[i] = '\0';

	if (i < 3 || buf[1] != ',') return 0;

	*cmd = buf[0];
	char *p = &buf[2];
	*verdi1 = atoi(p);

	char *komma2 = strchr(p, ',');
	if (komma2 != NULL) {
		*verdi2 = atoi(komma2 + 1);
		return 2;
	}
	return 1;
}

/* ---- Main ---- */
int main(void) {
	LED_init();
	USART2_init();
	ADC0_init();
	TCA0_init_SERVO();

	char cmd;
	int  verdi1, verdi2;
	char buf[16];
	int  antall;

	while (1) {
		antall = les_melding(&cmd, &verdi1, &verdi2);
		if (antall > 0) {
			switch (cmd) {
				case 'L':
					if (antall == 2) LED_set(verdi1, verdi2);
					USART2_sendString("OK\n");
					break;
				case 'S':
					Servo_set(verdi1);
					USART2_sendString("OK\n");
					break;
				case 'M':
					snprintf(buf, sizeof(buf), "%u\n", ADC0_read());
					USART2_sendString(buf);
					break;
				default:
					USART2_sendString("ERR\n");
					break;
			}
		}
	}
}