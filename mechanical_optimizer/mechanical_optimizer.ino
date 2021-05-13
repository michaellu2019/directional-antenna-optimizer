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
  while (low < high) {
    int span = high - low;
    int angle = low;
    int max_angle = low;
    int max_s21 = 0;

    while (angle >= low && angle <= high) {
      servo.write(angle);
      read_vna_data();
      
      if (new_data) {
        if (s21 > max_s21) {
          max_s21 = s21;
          max_angle = angle;
        }
        
        s21 = atoi(data);
        lcd.setCursor(0, 0);
        lcd.print("    S21: ");
        lcd.print(s21);
        lcd.setCursor(0, 1);
        lcd.print("Max S21: ");
        lcd.print(max_s21);
        
        new_data = false;
      
  
        angle += sample_step;
  
        delay(sample_delay);
      }
    }

    sample_step = max(sample_step - 1, 0);
    span /= decay_rate;
    low = max(max_angle - span, min_sweep_angle);
    high = min(max_angle + span, max_sweep_angle);
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


//void read_vna_data() {
//  while (Serial.available() > 0) {
//    char data[data_len]; //= "2564356435,0.22084869346338235,0.03422193329537066;";
//    Serial.readStringUntil(";").toCharArray(data, data_len);
//    char* f_str = strtok(data, ",");
//    char* s11_str = strtok(NULL, ",");
//    char* s21_str = strtok(NULL, ";");
//
//    f = atoi(f_str);
//    s11 = atoi(s11_str);
//    s21 = atoi(s21_str);

//    String data = Serial.readStringUntil(";");
//    String data = "2564356435,0.22084869346338235,0.03422193329537066;";
//    int first_split = data.indexOf(",");
//    int last_split = data.lastIndexOf(",");
//    String f_str = data.substring(0, first_split);
//    String s11_str = data.substring(first_split + 1, last_split);
//    int i = data.lastIndexOf(";");
//    String s21_str = data.substring(0, i);
//
//    f = f_str.toInt();
//    s11 = s11_str.toInt();
//    s21 = s21_str.toInt();
//
//    Serial.print(s11);
//    Serial.print(", ");
//    Serial.print(s21);
//    Serial.println();
//
//    servo.write(f);
    
//    lcd.setCursor(0, 0);
//    lcd.print("S11: ");
//    lcd.print(s11_str);
//    lcd.setCursor(0, 1);
//    lcd.print("S21: ");
//    lcd.print(s21_str);
//    s21 = s21_str.toInt();
//    Serial.println(s21);
    
//    lcd.setCursor(0, 0);
//    lcd.print("S21: ");
//    lcd.print(data);
//  }
//}
