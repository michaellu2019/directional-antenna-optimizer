#include <Servo.h>
#include <LiquidCrystal.h>
#include <string.h>
#include <stdlib.h>

const uint8_t rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

const uint8_t lcd_data_precision = 5;
const uint8_t data_len = 64;

const uint8_t min_sweep_angle = 0;
const uint8_t max_sweep_angle = 180;
uint8_t low = min_sweep_angle;
uint8_t high = max_sweep_angle;
int decay_rate = 3;
int sample_step = 5;
int sample_delay = 100;

int f, s11, s21;

char data[data_len];
boolean new_data = false;

Servo servo;
const uint8_t servo_pin = 9;

void setup() {
  Serial.begin(115200);

  servo.attach(servo_pin);
  servo.write(0);
  
  lcd.begin(16, 2);
  lcd.setCursor(0, 0);
  lcd.print("Init...");
  
  delay(3000);
}

void loop() {
  read_vna_data();
      
  if (new_data) {
    s21 = atoi(data);
    lcd.setCursor(0, 0);
    lcd.print("    S21: ");
    lcd.print(s21);
    lcd.setCursor(0, 1);
    lcd.print("Max S21: ");
    lcd.print(max_s21);
    
    new_data = false;
  }
}

void read_vna_data() {
    static byte ndx = 0;
    char end_marker = ';';
    char rc;
    
    while (Serial.available() > 0 && !new_data) {
        rc = Serial.read();

        if (rc != end_marker) {
            data[ndx] = rc;
            ndx++;
            if (ndx >= data_len) {
                ndx = data_len - 1;
            }
        } else {
            data[ndx] = '\0';
            ndx = 0;
            
            new_data = true;
        }
    }
}
